import sys  # noqa: N999
from os import path


def resource_path(relative_path):
    """Get the absolute path to assets, works for both dev and PyInstaller"""
    base_path = getattr(sys, '_MEIPASS', path.abspath("."))
    return path.join(base_path, relative_path)
