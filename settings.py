from pathlib import Path

import toml


class Settings:
    _instance = None
    _config_file = "settings.toml"

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.load_settings()
        return cls._instance

    def __init__(self):
        if not hasattr(self, "initialized"):  # Ensure that we only init once
            self.initialized = True
            if not hasattr(self, "_settings"):
                self._settings = {}

    def load_settings(self):
        """Load settings from TOML file."""
        try:
            with Path(self._config_file).open() as file:
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
