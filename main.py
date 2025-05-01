__version__ = "0.3.0"

import ctypes
import os
import queue
import sys
import threading
import time
import traceback

import pywintypes
import win32api
import win32con
import win32gui

from settings import Settings

# OS environ call to hide the PyGame support prompt
os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "hide"
import pygame as pg
from PySide6.QtCore import (
    QObject,
    QRunnable,
    QThreadPool,
    Signal,
    Slot,
)
from PySide6.QtGui import (
    QAction,
)
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)

# [ ] Need to refresh app when the settings have been modified. (exe name changed)


class Joystick_Event_Emitter(QObject):
    joystick_axis_update = Signal(
        int,  # Joystick ID
        int,  # Axis
        int,  # New value
    )
    joystick_button = Signal(
        int,  # Joystick ID
        int,  # Button ID
    )
    joystick_button_up = Signal(
        int,  # Joystick ID
        int,  # Button ID
    )


def Joystick_Thread(emitter: Joystick_Event_Emitter):
    pg.init()
    pg.joystick.init()

    count = pg.joystick.get_count()
    if count == 0:
        print("No joystick found.")
        return

    joysticks = []

    for j in range(0, count):
        joysticks.append(pg.joystick.Joystick(j))
        joysticks[j].init()
        print("JOY {}: {} initialized:".format(j, joysticks[j].get_name()))
        print(" - Axis: {}".format(joysticks[j].get_numaxes()))
        print(" - Buttons: {}".format(joysticks[j].get_numbuttons()))
        print(" - Hats: {}".format(joysticks[j].get_numhats()))

        for ax in range(0, joysticks[j].get_numaxes()):
            emitter.joystick_axis_update.emit(j, ax, joysticks[j].get_axis(ax))

    while True:
        pg.event.pump()
        for event in pg.event.get():
            if event.type == pg.JOYAXISMOTION:
                emitter.joystick_axis_update.emit(
                    event.joy,
                    event.axis,
                    int(event.value * 100),
                )
            if event.type == pg.JOYBUTTONDOWN:
                print("Joy: {} Btn: {} Pressed".format(event.joy, event.button))

            if event.type == pg.JOYBUTTONUP:
                print("Joy: {} Btn: {} Released".format(event.joy, event.button))

            if event.type == pg.JOYHATMOTION:
                print(
                    "Joy: {} Hat: {} Val:{}".format(event.joy, event.hat, event.value)
                )

        pg.time.wait(50)


class Process_Monitor_Emitter(QObject):
    process_running = Signal(
        str,  # Process name
        bool,  # Process running state
    )


class Process_Monitor_Worker(QRunnable):
    def __init__(
        self, emitter: Process_Monitor_Emitter, monitor_window_name, *args, **kwargs
    ):
        """Initialize our Process Monitor
        Args:
            monitor_window_name (str): The name of the process to monitor for
        """
        super().__init__()
        self.emitter = emitter
        self.monitor_name = monitor_window_name.lower()

        self.queue = queue.Queue()
        self._win_list = []
        """Internal list of windows"""
        self.is_process_running = False
        self.signals = Process_Monitor_Emitter()

        self.running = False

    def __enum_windows_callback(self, hwnd, result):
        """capture all running processes with window names"""
        # [ ] potentially refactor the code here so that we are only saving relevant names
        name = win32gui.GetWindowText(hwnd)
        # we can exclude blank names
        if name:
            result.append((hwnd, name))

    def _get_window_list(self):
        """update our window list"""
        self._win_list = []  # Reset our window list
        win32gui.EnumWindows(self.__enum_windows_callback, self._win_list)

    def focus_on_monitor_window(self):
        self.queue.put("focus")

    def _focus_window_name(self, window_name, force=False):
        hwnd = win32gui.FindWindow(None, window_name)
        if hwnd:
            self._focus_window(hwnd, force)

    def _focus_window(self, hwnd, force=False):
        """Private: Set focused window to hwnd. This will gracefully continue if it fails

        Args:
            hwnd (hwnd): Window Handle
            force (bool, optional): Force focus by hooking into current active window. Defaults to False.
        """
        try:
            win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
            win32gui.SetForegroundWindow(hwnd)
        except pywintypes.error:
            if force:
                self._force_focus(hwnd)

    def _force_focus(self, hwnd_target):
        """Private: Force focus on specified window.
        NOTE: As windows restricts when we can focus another program, we need to
        hook into the active foreground window. This is potentially an issue
        for games with cheat detection, need to be careful

        Args:
            hwnd_target (int): Window handle
        """
        user32 = ctypes.windll.user32
        foreground_hwnd = user32.GetForegroundWindow()
        if foreground_hwnd == hwnd_target:
            return  # We already have focus

        foreground_tid = user32.GetWindowThreadProcessId(foreground_hwnd, 0)
        target_tid = user32.GetWindowThreadProcessId(hwnd_target, 0)

        current_thread_id = win32api.GetCurrentThreadId()

        # Attach to the foreground thread
        user32.AttachThreadInput(current_thread_id, foreground_tid, True)
        user32.AttachThreadInput(current_thread_id, target_tid, True)

        try:
            win32gui.ShowWindow(hwnd_target, win32con.SW_RESTORE)
            win32gui.SetForegroundWindow(hwnd_target)
        except Exception as e:
            # print(f"Exception occurred while focusing. {e}")
            pass
        # Detach from foreground thread
        user32.AttachThreadInput(current_thread_id, foreground_tid, False)
        user32.AttachThreadInput(current_thread_id, target_tid, False)

    def _update_proc_running_state(self, is_running):
        # is_proc_running - Flag indicating last signal
        # if flag and is_running are different, update the flag and call the signal
        if self.is_process_running != is_running:
            self.is_process_running = is_running
            print(f"Is running: {is_running}")
            self.emitter.process_running.emit(self.monitor_name, is_running)
            # [ ] Need to call signal to indicate run state has changed

        pass

    def run(self):
        """Start running the process monitor worker"""
        if self.running:
            return  # As we are already running, do nothing

        self.running = True
        while self.running:
            self._get_window_list()
            # clear our current vars
            hwnd = None
            # name = None

            for l_hwnd, l_name in self._win_list:
                if self.monitor_name in l_name.lower():
                    hwnd = l_hwnd
                    # name = l_name
                    break
            self._update_proc_running_state(hwnd is not None)

            try:
                task = self.queue.get(timeout=0.5)  # Short timeout of 500ms
                if task == "focus":
                    if hwnd:
                        self._focus_window(hwnd, True)

                    self.queue.task_done()
            except queue.Empty:
                continue
            time.sleep(0.05)  # Sleep for 50ms

    def stop(self):
        """Stop the process monitor worker"""
        self.running = False


class Worker_Signals(QObject):
    """Signals from a running worker thread.

    finished
        No data

    error
        tuple (exctype, value, traceback.format_exc())

    result
        object data returned from processing, anything

    progress
        float indicating % progress
    """

    finished = Signal()
    error = Signal(tuple)
    result = Signal(object)
    progress = Signal(float)


class Worker(QRunnable):
    """Worker thread.

    Inherits from QRunnable to handler worker thread setup, signals and wrap-up.

    :param callback: The function callback to run on this worker thread.
                     Supplied args and kwargs will be passed through
                     to the runner.
    :type callback: function
    :param args: Arguments to pass to the callback function
    :param kwargs: Keywords to pass to the callback function
    """

    def __init__(self, fn, *args, **kwargs):
        super().__init__()
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = Worker_Signals()
        # Add the callback to our kwargs
        self.kwargs["progress_callback"] = self.signals.progress

    @Slot()
    def run(self):
        """Initialize the runner function with the passed self.args, self.kwargs"""
        try:
            result = self.fn(*self.args, **self.kwargs)
        except Exception:
            traceback.print_exc()
            exctype, value = sys.exc_info()[:2]
            self.signals.error.emit((exctype, value, traceback.format_exc()))
        else:
            self.signals.result.emit(result)  # Return the result of the processign
        finally:
            self.signals.finished.emit()  # Done


class Main_Window(QMainWindow):
    def __init__(self, process_monitor_emitter, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setWindowTitle("ED Joy {}".format(__version__))
        self.generate_base_layout()
        self.init_settings()
        self.pm = None
        self.process_monitor_emitter = process_monitor_emitter

        pg.joystick.init()

        self.threadpool = QThreadPool()

        # thread_count = self.threadpool.maxThreadCount()
        # print("Multithreading with maximum {} threads".format(thread_count))

        layout_main_window = QVBoxLayout()
        """Layout - Top level layout for the main window"""

        # Begin - Process Monitor
        gb_proc_monitor = QGroupBox()
        """Process Monitor group box"""
        gb_proc_monitor.setTitle("Process Monitor")
        layout_main_window.addWidget(gb_proc_monitor)

        gb_lay_monitor = QVBoxLayout()
        """Layout - Process Monitor groupbox"""
        gb_proc_monitor.setLayout(gb_lay_monitor)
        # horizontal widget to contain chkbox and le for msgs

        layout_proc_mon_row_0 = QHBoxLayout()
        """Layout - Process Monitor Row 0"""
        self.check_monitor_enable = QCheckBox()
        """Checkbox to enable Process Monitor"""
        self.check_monitor_enable.setText("Enable Monitor")
        self.check_monitor_enable.stateChanged.connect(
            self.on_checkbox_state_change_proc_mon
        )

        layout_proc_mon_row_0.addWidget(self.check_monitor_enable)
        self.le_monitor_status = QLineEdit()
        self.le_monitor_status.setReadOnly(True)
        self.le_monitor_status.setText("Process Monitor Status")
        layout_proc_mon_row_0.addWidget(self.le_monitor_status)
        gb_lay_monitor.addLayout(layout_proc_mon_row_0)

        # hbox for label and combobox
        layout_proc_mon_row_1 = QHBoxLayout()
        gb_lay_hbox_label = QLabel()
        gb_lay_hbox_label.setText("Window Title")
        layout_proc_mon_row_1.addWidget(gb_lay_hbox_label)
        gb_lay_hbox_ledit_title = QLineEdit()
        gb_lay_hbox_ledit_title.setText(self.settings["monitor.process.title"])
        gb_lay_hbox_ledit_title.setReadOnly(True)  # Temp
        layout_proc_mon_row_1.addWidget(gb_lay_hbox_ledit_title)
        gb_lay_monitor.addLayout(layout_proc_mon_row_1)
        # End - Monitor Section

        layout_main_window
        hbox = self.generate_group_boxes()
        layout_main_window.addLayout(hbox)
        w = QWidget()
        w.setLayout(layout_main_window)
        self.setCentralWidget(w)

        self.show()
        self.status_label.setText("Ready")
        self.check_monitor_enable.setChecked(self.settings["monitor.process.enabled"])

    def on_lineedit_text_change_proc_mon(self, state):
        # [ ] Restart monitor only if there is a change in text
        self.restart_proc_monitor()
        pass

    def on_checkbox_state_change_proc_mon(self, state):
        if state == 0:
            self.settings["monitor.process.enabled"] = False
            self.stop_proc_monitor()
        elif state == 2:
            self.settings["monitor.process.enabled"] = True
            self.start_proc_monitor()

    def restart_proc_monitor(self):
        """Restart process monitor only if it is running"""
        if self.pm is not None:
            self.stop_proc_monitor()
            self.start_proc_monitor()

    def start_proc_monitor(self):
        """Start process monitor if it is not running"""
        if self.pm is None:
            self.le_monitor_status.setText("Monitor started")
            # [ ] Add some logic to dynamicly update the monitor status from a function. Change colors/update text in one function
            self.pm = Process_Monitor_Worker(
                self.process_monitor_emitter, self.settings["monitor.process.title"]
            )
            self.threadpool.start(self.pm)

    def stop_proc_monitor(self):
        """Stop process Monitor if it is running"""
        if self.pm is not None:
            self.le_monitor_status.setText("Monitoring stopped")
            self.pm.stop()
            self.pm = None

    def generate_group_boxes(self):
        """Generate the groupboxes for all Joysticks."""
        hbox = QHBoxLayout()

        self.joystick_axis_widgets = {}
        self.joystick_monitor_widgets = {}
        # [ ] Implement deadzone on joysticks
        # self.joystick_deadzone_widgets = {}
        # [ ] Add display for button's being pressed on Joystick

        # For each Joystick
        for joy_index in range(0, pg.joystick.get_count()):
            joy = pg.joystick.Joystick(joy_index)
            joy_gb = QGroupBox()
            joy_gb.setTitle(joy.get_name())
            # [ ] We could add indicators for each button/hat
            axes_group_box = QGroupBox()
            axes_group_box.setTitle("Axis")

            axis_box_layout = QVBoxLayout()

            # Toggle monitored joystick
            joy_monitor_layout = QHBoxLayout()
            chk_monitor_joy = QCheckBox()
            # """Checkbox to toggle joystick monitoring"""
            chk_monitor_joy.setText(f"Monitor J{joy_index}")
            if int(joy_index) in self.settings["monitor.joysticks"]:
                chk_monitor_joy.setChecked(True)
            chk_monitor_joy.clicked.connect(self.joystick_monitor_checkbox_clicked)
            joy_monitor_layout.addWidget(chk_monitor_joy)

            # layout_joy_mon_row_1 = QHBoxLayout()
            # lbl_deadzone = QLabel()
            # lbl_deadzone.setText("Set Deadzone")
            # layout_joy_mon_row_1.addWidget(lbl_deadzone)
            # spin_deadzone = QSpinBox()
            # self.joystick_deadzone_widgets[joy_index] = spin_deadzone
            # layout_joy_mon_row_1.addWidget(spin_deadzone)
            # joy_monitor_layout.addLayout(layout_joy_mon_row_1)
            axis_box_layout.addLayout(joy_monitor_layout)

            # create an array to store each axis's lineedit in
            self.joystick_axis_widgets[joy_index] = {}
            # Generate a pair of labels/text fields for each axis
            for axis in range(0, joy.get_numaxes()):
                joy_axis_layout = QHBoxLayout()
                lbl_axis = QLabel("Axis {}".format(axis))
                le_axis = QLineEdit()
                le_axis.setReadOnly(True)
                # le_axis.setFixedWidth(51)
                self.joystick_axis_widgets[joy_index][axis] = le_axis
                joy_axis_layout.addWidget(lbl_axis)
                joy_axis_layout.addWidget(le_axis)

                axis_box_layout.addLayout(joy_axis_layout)
            axis_box_layout.addStretch()
            for button in range(0, joy.get_numbuttons()):
                pass

            joy_gb.setLayout(axis_box_layout)
            hbox.addWidget(joy_gb)
        return hbox

    def generate_base_layout(self):
        """Generate the main layout elements such as the menu and status bar"""
        self.setMinimumWidth(300)

        menu_bar = self.menuBar()
        # File menu
        file_menu = menu_bar.addMenu("File")

        # File -> Exit action
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Create status bar
        status_bar = QStatusBar()
        self.setStatusBar(status_bar)

        # Add a label to the status bar
        self.status_label = QLabel("Launching")
        status_bar.addPermanentWidget(self.status_label)

    def init_settings(self):
        """Ensure that settings exist, if not give them a default value"""
        self.settings = Settings()  # This will trigger a load
        if self.settings["monitor.joysticks"] is None:
            self.settings["monitor.joysticks"] = []

        # Ensure that we have a process to monitor defined.
        if self.settings["monitor.process.enabled"] is None:
            self.settings["monitor.process.enabled"] = False

        # Populate the default Elite Dangerous Client title
        if self.settings["monitor.process.title"] is None:
            self.settings["monitor.process.title"] = "Elite - Dangerous (CLIENT)"

        # Populate the default display name (only used when reporting status)
        if self.settings["monitor.process.display_name"] is None:
            self.settings["monitor.process.display_name"] = "Elite Dangerous"

    def joystick_monitor_checkbox_clicked(self):
        """Callback to add/remove monitored joystick based on the ID from the
        checkbox name
        """
        checkbox = self.sender()  # Get the checkbox that sent the signal
        if checkbox:
            # Extract the joystick id from the checkbox name
            joy_id = checkbox.text().replace("Monitor J", "")
            self.update_monitored_joystick(joy_id, checkbox.isChecked())

    def update_process_monitor(self, name, is_running):
        msg = f"{self.settings['monitor.process.display_name']}"
        if is_running:
            msg += " is running"
        else:
            msg += " not detected"
        self.le_monitor_status.setText(msg)

    def update_axes_labels(self, joy_id, axis, val):
        self.joystick_axis_widgets[joy_id][axis].setText(str(val))
        if self.settings["monitor.process.enabled"]:
            if joy_id in self.settings["monitor.joysticks"]:
                print(
                    "Joystick {joy_id} movement detect, joystick is monitored. Changing Focus"
                )
                self.pm.focus_on_monitor_window()

        # [ ] add logic to update focus if we are on a monitored joystick determined against the settings monitored axis

    def update_monitored_joystick(self, joy_id, is_checked):
        """Update the settings to add/remove the joystick from the monitored
        list based on is_checked

        Args:
            joy_id (int): Joystick ID
            is_checked (bool): Is the current joystick checked
        """

        if is_checked:
            if int(joy_id) not in self.settings["monitor.joysticks"]:
                joysticks = self.settings["monitor.joysticks"]
                # We need to modify the joysticks then reassign to trigger a save
                joysticks.append(int(id))
                self.settings["monitor.joysticks"] = joysticks
        else:
            arr = [x for x in self.settings["monitor.joysticks"] if x != int(id)]
            self.settings["monitor.joysticks"] = arr


def Main():
    joystick_emitter = Joystick_Event_Emitter()
    process_monitor_emitter = Process_Monitor_Emitter()

    app = QApplication(sys.argv)
    window = Main_Window(process_monitor_emitter)
    window.show()

    # Connect the signals to the GUI slots
    joystick_emitter.joystick_axis_update.connect(window.update_axes_labels)
    process_monitor_emitter.process_running.connect(window.update_process_monitor)

    # Start pygame in a separate thread
    thread = threading.Thread(
        target=Joystick_Thread, args=(joystick_emitter,), daemon=True
    )
    thread.start()

    sys.exit(app.exec())


if __name__ == "__main__":
    Main()
