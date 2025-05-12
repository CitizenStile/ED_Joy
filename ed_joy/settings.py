from pathlib import Path

import toml

from ed_joy import resource_path


class Settings:
    _instance = None
    __config_file = "config\\settings.toml"

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)

        return cls._instance

    def __init__(self):
        if not hasattr(self, "initialized"):  # Ensure that we only init once
            self.initialized = True
            self.load_settings()
            self.get_defaults()
            if not hasattr(self, "_settings"):
                self._settings = {}

    @property
    def _config_path(self):
        """Return the path to the settings file.
        Returns:
            Path
        """
        return resource_path(self.__config_file, True)

    def _open_config(self, mode = 'r'):
        """Open the config file in the specified mode. Recursively create directories,
           continue without error if folder exists
        Args:
            mode (str, optional): File access mode. Defaults to 'r'.
        Returns:
            file : Contextmanger stream to the file
        """
        pth = Path(self._config_path)
        pth.parent.mkdir(parents=True, exist_ok=True)
        return pth.open(mode)

    def load_settings(self):
        """Load settings from TOML file."""
        try:
            with Path(self._config_path).open() as file:
                self._settings = toml.load(file)
        except FileNotFoundError:
            print(f"Warning: {self.__config_file} not found. Using default settings.")
            self._settings = {}  # Empty or default settings can be used here

    def get_defaults(self, overwrite=False):
        """Ensure the settings dict is populated with at least the default values
        Args:
            overwrite (bool, optional): Overwrite the setting with the default value.
                                        Defaults to False.
        """

        if self["logging.level"] is None or overwrite:
            self["logging.level"] = "DEBUG"

        if self["monitor.joysticks"] is None or overwrite:
            self["monitor.joysticks"] = []

        if self["monitor.process.enabled"] is None or overwrite:
            self["monitor.process.enabled"] = False

        # # Populate the default Elite Dangerous Client title
        if self["monitor.process.title"] is None or overwrite:
            self["monitor.process.title"] = "Elite - Dangerous (CLIENT)"

        # # Populate the default display name (only used when reporting status)
        if self["monitor.process.display_name"] is None or overwrite:
            self["monitor.process.display_name"] = "Elite Dangerous"


    def save_settings(self):
        """Write settings to the TOML file."""
        with Path(self._config_path).open("w") as file:
            toml.dump(self._settings, file)

    def get(self, dotted_key, default=None):
        """Retrieve setting by key."""
        keys = dotted_key.split(".")
        value = self._settings
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        return value

    def set(self, dotted_key, value):
        keys = dotted_key.split(".")
        d = self._settings
        for key in keys[:-1]:
            if key not in d or not isinstance(d[key], dict):
                d[key] = {}
            d = d[key]
        d[keys[-1]] = value
        self.save_settings()

    def __getitem__(self, key):
        return self.get(key)

    def __setitem__(self, key, value):
        self.set(key, value)
