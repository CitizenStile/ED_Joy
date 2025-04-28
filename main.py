import os
import sys
import threading
import traceback
from enum import Enum

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


class ButtonState(Enum):
    UNKNOWN = -1
    UP = 0
    DOWN = 1


class JoystickEventEmitter(QObject):
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


def joystick_thread(emitter: JoystickEventEmitter):
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
                    int(event.value * 1000),
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


class worker_signals(QObject):
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


class worker(QRunnable):
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
        self.signals = worker_signals()
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


class main_window(QMainWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setWindowTitle("ED Joy v.{}".format("0.2.0"))
        self.generate_main_layout()
        self.settings = Settings()
        if self.settings["monitor.joysticks"] is None:
            self.settings["monitor.joysticks"] = []
        pg.joystick.init()

        self.threadpool = QThreadPool()
        # thread_count = self.threadpool.maxThreadCount()
        # print("Multithreading with maximum {} threads".format(thread_count))

        layout = QVBoxLayout()

        hbox = self.generate_group_boxes()
        layout.addLayout(hbox)
        w = QWidget()
        w.setLayout(layout)
        self.setCentralWidget(w)

        self.show()
        self.status_label.setText("Ready")

    def generate_group_boxes(self):
        hbox = QHBoxLayout()
        self.joystick_axis_widgets = {}
        self.joystick_monitor_widgets = {}
        # For each Joystick
        for joy_index in range(0, pg.joystick.get_count()):
            joy = pg.joystick.Joystick(joy_index)
            joy_gb = QGroupBox()
            joy_gb.setTitle(joy.get_name())
            # TODO We could add indicators for each button/hat
            axes_group_box = QGroupBox()
            axes_group_box.setTitle("Axis")

            axis_box_layout = QVBoxLayout()

            # Toggle monitored joystick
            joy_monitor_layout = QHBoxLayout()
            chk_monitor_joy = QCheckBox()
            chk_monitor_joy.setText(f"Monitor joystick {joy_index}")
            if int(joy_index) in self.settings["monitor.joysticks"]:
                chk_monitor_joy.setChecked(True)
            chk_monitor_joy.clicked.connect(self.monitor_checkbox_clicked)
            joy_monitor_layout.addWidget(chk_monitor_joy)

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

    def generate_main_layout(self):
        """Generate the main layout elements such as the menu and status bar"""
        self.setMinimumWidth(250)

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

    def monitor_checkbox_clicked(self):
        """Callback to add/remove monitored joystick based on the ID from the
        checkbox name
        """
        checkbox = self.sender()  # Get the checkbox that sent the signal
        if checkbox:
            # Extract the joystick id from the checkbox name
            joy_id = checkbox.text().replace("Monitor joystick ", "")
            self.update_monitored_joystick(joy_id, checkbox.isChecked())

    def update_axes_labels(self, joy_id, axis, val):
        self.joystick_axis_widgets[joy_id][axis].setText(str(val))

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

    # def execute_this_fn(self):
    #     for n in range(0, 5):
    #         time.sleep(1)
    #     return "Done."

    # def print_output(self, s):
    #     print(s)

    # def thread_complete(self):
    #     print("THREAD COMPLETE!")

    # def oh_no(self):
    #     # Pass the function to execute
    #     worker = Worker(
    #         self.execute_this_fn
    #     )  # Any additional args, kwargs are passed to the run function
    #     worker.signals.result.connect(self.print_output)
    #     worker.signals.finished.connect(self.thread_complete)

    #     # Execute
    #     self.threadpool.start(worker)

    # def recurring_timer(self):
    #     self.counter += 1
    #     self.label.setText("Counter: {}".format(self.counter))


def main():
    emitter = JoystickEventEmitter()

    app = QApplication(sys.argv)
    window = main_window()
    window.show()

    # Connect the signal to the GUI slot
    emitter.joystick_axis_update.connect(window.update_axes_labels)

    # Start pygame in a separate thread
    thread = threading.Thread(target=joystick_thread, args=(emitter,), daemon=True)
    thread.start()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
