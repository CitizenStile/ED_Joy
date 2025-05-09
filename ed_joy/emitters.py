from PySide6.QtCore import (
    QObject,
    Signal,
)


class JoystickEventEmitter(QObject):
    axis_movement = Signal(
        int,   # Joystick ID
        int,   # Axis
        int,   # New value
        float, # Timestamp
    )
    button_down = Signal(
        int,   # Joystick ID
        int,   # Button ID
        float, # Timestamp
    )
    button_up = Signal(
        int,   # Joystick ID
        int,   # Button ID
        float, # Timestamp
    )
    hat_motion = Signal(
        int,   # Joystick ID
        int,   # Hat ID
        tuple, # Position Tuple
        float, # Timestamp
    )


class ProcessMonitorEmitter(QObject):
    process_running = Signal(
        str,  # Process name
        bool,  # Process running state
    )
