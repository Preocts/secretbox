"""
Loads local environment vars and .env file to an accessible object

Author  : Preocts <preocts@preocts.com>
Discord : Preocts#8196
Git Repo: https://github.com/Preocts/secretbox
"""
import os
from typing import Dict
from typing import Optional


class LoadEnv:
    """Loads local environment vars and .env file to an accessible object"""

    __slots__ = ["filename", "loaded_values"]

    def __init__(self, filename: str = ".env", auto_load: bool = False) -> None:
        """Provide full path and name to .env if not located in working directory"""
        self.filename: str = filename
        self.loaded_values: Dict[str, str] = {}
        if auto_load:
            self.load()

    def get(self, key: str) -> Optional[str]:
        """Get a value by key, can return None if not found"""
        return self.loaded_values.get(key)

    def load(self) -> None:
        """Loads environment vars, then .env (or provided) file"""
        self.load_env_vars()
        self.load_env_file()
        self.push_to_environment()

    def load_env_vars(self) -> None:
        """Loads all visible environmental variables"""
        for key, value in os.environ.items():
            self.loaded_values[key] = value

    def load_env_file(self) -> bool:
        """Loads local .env or from path if provided"""
        try:
            with open(self.filename, "r", encoding="utf-8") as input_file:
                self.__parse_env_file(input_file.read())
        except FileNotFoundError:
            return False
        return True

    def push_to_environment(self) -> None:
        """Pushes loaded values to local environment vars, will overwrite existing"""
        for key, value in self.loaded_values.items():
            os.environ[key] = value

    def __parse_env_file(self, input_file: str) -> None:
        """Parses env file into key-pair values"""
        for line in input_file.split("\n"):
            if not line or line.strip().startswith("#") or len(line.split("=", 1)) != 2:
                continue
            key, value = line.split("=", 1)
            self.loaded_values[key.strip()] = value.strip()
