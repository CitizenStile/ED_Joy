import sys
import tomllib
from pathlib import Path


def resource_path(relative_path, mkdir=False):
    """Get the absolute path to assets, works for both dev and PyInstaller

    Args:
        relative_path (str): relative path to convert to an actual path
        mkdir (bool, optional): should the folder path be created
        if not existing. Defaults to False.

    Returns:
        Path: absolute path
    """

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

def get_version():
    """Read the project version from pyproject.toml.
    Returns:
        str: semver version
    """
    pyproject = Path(__file__).parent.parent / "pyproject.toml"
    with pyproject.open("rb") as f:
        data = tomllib.load(f)
    ret = "0.0.0"
    if "project" in data and "version" in data["project"]:
        ret = data["project"]["version"]
    return ret
