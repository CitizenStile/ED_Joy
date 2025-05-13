import logging

from ed_joy import resource_path
from ed_joy.settings import Settings


def str_to_level(level: str):
    """Convert string level to log level.
    Valid levels: DEBUG, INFO, WARNING, ERROR, CRITICAL

    Args:
        level (str): Log level string

    Returns:
        int: Log level, 10 (DEBUG) if invalid level set
    """
    return getattr(logging, level.upper(), 10)


def get_logger(name: str):
    """Create a logger

    Args:
        name (str): Name for new logger
    """
    #  Get the log file using resource_path
    log_file = resource_path(f'logs/ed_joy_{name}.log', mkdir=True)

    logger = logging.getLogger(name)
    # Grab settings so we can check the log level
    settings = Settings()
    log_level = str_to_level(settings["logging.level"])
    logger.setLevel(log_level)

    # Create a formatter to attach to the handlers
    format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    formatter = logging.Formatter(format)

    # Check the number of handlers we currently have.
    if len(logger.handlers) == 0:
        add_handlers(logger, log_file, formatter)
    elif len(logger.handlers) != 2:
        # we have an odd number of handlers, we should probably remove them
        # and create new ones
        # [ ] Add logic to remove and re-add handlers if we don't have 2
        pass
    return logger

def add_handlers(logger:logging.Logger, file ,formatter: logging.Formatter):
    # Create the file handler
    file_handler = logging.FileHandler(file)
    file_handler.setFormatter(formatter)

    # Create the console handler for debug messages
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(formatter)
    # Add the handlers to the logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
