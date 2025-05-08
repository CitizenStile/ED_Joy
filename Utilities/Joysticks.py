import os
import threading
import time

# OS environ call to hide the PyGame support prompt
os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "hide"
import pygame as pg
from PySide6.QtCore import (
    Slot,  # noqa: F401
)

try:
    from Utilities.Emitters import JoystickEventEmitter
except Exception:
    from Emitters import JoystickEventEmitter


class Joysticks:
    _instance = None
    _lock = threading.Lock()  # Ensure that we have thread-safe access

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            with cls._lock:  # Lock only if we are not initialized
                if (
                    cls._instance is None
                ):  # Verify that we did not get initialized before we locked
                    cls._instance = super(Joysticks, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialization logic that will only run the first time"""
        if hasattr(self, "_initialized"):
            return  # short circuit if we are initialized

        self._sleep = None
        """How long we should sleep on each pass."""
        self.fps = 30
        """Our targeted FPS, used to determine how often to run"""
        self._halt_thread = False
        self._running = False
        self._initialized = True

        self._emitter = JoystickEventEmitter()
        """Joystick Event Emitter"""

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
            self._sleep = round(1 / self.fps * 1000)

    def start(self):
        """Start the joystick_thread to monitor input.
        If already started, do nothing"""
        if hasattr(self,'_thread') and self._thread is not None:
            # Only run if we do not have an existing thread
            return

        pg.init()
        pg.joystick.init()
        self._count = pg.joystick.get_count()

        if self._count == 0:
            print("No joystick found.")


        self._thread = threading.Thread(
            target=self.__joystick_thread, args=(), daemon=True
        )
        self._thread.start()

    def stop(self):
        if not hasattr(self,'_thread') or self._thread is None:
            # Only run if we do have an existing thread
            return
        with self._lock:
            self._halt_thread = True

    def get_joysticks_and_axis(self):
        self._joysticks = []
        for j in range(0, self._count):
            joy = pg.joystick.Joystick(j)
            joy.init()
            # Grab the current axis position. Seems to default to 0
            for axis in range(0, joy.get_numaxes()):
                self.emitter.axis_movement.emit(j, axis, joy.get_axis(axis),0)

            with self._lock:
                # Yay thread safety
                self._joysticks.append(joy)

    def __joystick_thread(self):
        self.get_joysticks_and_axis()
        while True:
            pg.event.pump()
            now = time.time()
            try:
                for event in pg.event.get():
                    if event.type == pg.JOYAXISMOTION:
                        self.emitter.axis_movement.emit(
                            event.joy,
                            event.axis,
                            int(event.value * 100),
                            now
                        )
                    if event.type == pg.JOYBUTTONDOWN:
                        self.emitter.button_down.emit(
                            event.joy,
                            event.button,
                            now,
                        )
                        # print(f"Joy: {event.joy} Btn: {event.button} Pressed")

                    if event.type == pg.JOYBUTTONUP:
                        self.emitter.button_up.emit(
                            event.joy,
                            event.button,
                            now,
                        )
                        # print(f"Joy: {event.joy} Btn: {event.button} Released")

                    if event.type == pg.JOYHATMOTION:
                        self.emitter.hat_motion.emit(
                            event.joy,
                            event.hat,
                            event.value,
                            now
                        )
                        # print(
                        #     f"Joy: {event.joy} Hat: {event.hat} Val:{event.value}",
                        # )

                with self._lock:
                    if self._halt_thread:
                        # Gracefully clean up our thread
                        self._thread = None
                        self.halt_thread = False
                        return
            except Exception as e:
                print(e)

            pg.time.wait(self._sleep)

    def print_details(self,joy_id):
        """Print the details about the joystick specified

        Args:
            joy_id (int): index of joystick
        """
        if joy_id >= 0 and joy_id < pg.joystick.get_count():
            print(f"Joystick {joy_id} not found.")
            return

        stick = pg.joystick.Joystick(joy_id)
        stick.init()
        print(f"JOY {joy_id}: {stick.get_name()} initialized:")
        print(f" - Axis: {stick.get_numaxes()}")
        print(f" - Buttons: {stick.get_numbuttons()}")
        print(f" - Hats: {stick.get_numhats()}")
