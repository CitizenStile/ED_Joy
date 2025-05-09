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
            if not hasattr(self, "_settings"):
                self._settings = {}

    @property
    def _config_path(self):
        return resource_path(self.__config_file)

    def load_settings(self):
        """Load settings from TOML file."""
        try:
            with Path(self._config_path).open() as file:
                self._settings = toml.load(file)
        except FileNotFoundError:
            print(f"Warning: {self._config_file} not found. Using default settings.")
            self._settings = {}  # Empty or default settings can be used here

    def save_settings(self):
        """Write settings to the TOML file."""
        with Path(self._config_file).open("w") as file:
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
