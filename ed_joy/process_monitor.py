import threading
import time

from ed_joy.emitters import ProcessMonitorEmitter


class ProcessMonitor:
    _instance = None
    _lock = threading.Lock()  # Ensure that we have thread-safe access

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:  # Lock only if we are not initialized
                if (cls._instance is None):
                    # Verify that we did not get initialized before we locked
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialization logic that will only run the first time"""
        if hasattr(self, "_initialized"):
            return  # short circuit if we are initialized

        self._sleep = None
        """How many times per second should we run."""
        self.fps = 30
        """Our targeted FPS, used to determine how often to run"""
        self._halt_thread = False
        self._running = False
        self._initialized = True

        self._emitter = ProcessMonitorEmitter()
        """Process Monitor Event Emitter"""

    def set_monitor_window_name(self, name:str):
        # [ ] Add logic to use _lock to update tracked window
        # Likely need to also implement logic to restart thread
        pass

    # def __init__(
    #     self, emitter: ProcessMonitorEmitter, monitor_window_name, *args, **kwargs
    # ):
    #     """Initialize our Process Monitor
    #     Args:
    #         monitor_window_name (str): The name of the process to monitor for
    #     """
    #     super().__init__()
    #     self.emitter = emitter
    #     self.monitor_name = monitor_window_name.lower()

    #     self.queue = queue.Queue()
    #     self._win_list = []

    #     """Internal list of windows"""
    #     self.is_process_running = False
    #     self.signals = ProcessMonitorEmitter()

    #     self.running = False

    @property
    def emitter(self):
        """Get the JoystickEventEmitter

        Returns:
            JoystickEventEmitter: emitter
        """
        return self._emitter

    @property
    def fps(self):
        """Return the current FPS.

        Returns:
            int: Current FPS
        """
        return self._fps

    @fps.setter
    def fps(self, fps):
        if not isinstance(fps, (int, float)):
            raise TypeError("fps parameter must be an int or float")
        if fps <= 0 or fps >= 60:
            raise ValueError("fps must be >0 and <=60")

        with self._lock:
            self._fps = fps
            self._sleep = 1 / self.fps * 1000

    def start(self):
        """Start the thread to monitor input.
        If already started, do nothing"""
        if hasattr(self,'_thread') and self._thread is not None:
            # Only run if we do not have an existing thread
            return

        self._thread = threading.Thread(
            target=self.__monitor_thread, args=(), daemon=True
        )
        self._thread.start()

    def stop(self):
        if not hasattr(self,'_thread') or self._thread is None:
            # Only run if we do have an existing thread
            return
        with self._lock:
            self._halt_thread = True

    def __monitor_thread(self):
        while True:
            try:
                # [ ] add logic for our monitor loop

                with self._lock:
                    if self._halt_thread:
                        # Gracefully clean up our thread
                        self._thread = None
                        self.halt_thread = False
                        return
            except Exception as e:
                print(e)

            time.sleep(self.fps)
