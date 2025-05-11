import sys
from pathlib import Path


def resource_path(relative_path, mkdir=False):
    """Get the absolute path to assets, works for both dev and PyInstaller"""
    base_path = getattr(sys, '_MEIPASS', Path(".").resolve())
    # base_path could be a str or Path, pass it to Path() for safety
    ret_pth = Path(base_path).joinpath(relative_path)
    if mkdir:
        try:
            ret_pth.parent.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            print("Exception occured while creating parents path")
            print(e)
    return ret_pth
