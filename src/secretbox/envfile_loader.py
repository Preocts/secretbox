"""
Load local .env from CWD or path, if provided

Current format for the `.env` file supports strings only and is parsed in
the following order:
- Each seperate line is considered a new possible key/value set
- Each set is delimted by the first `=` found
- Leading and trailing whitespace are removed
- Matched leading/trailing single quotes or double quotes will be
  stripped from values (not keys).

I'm open to suggestions on standards to follow here.

Author  : Preocts <Preocts#8196>
Git Repo: https://github.com/Preocts/secretbox
"""
from __future__ import annotations

import logging
import os
import re

from secretbox.loader import Loader


class EnvFileLoader(Loader):
    """Load local .env file"""

    RE_LTQUOTES = re.compile(r"([\"'])(.*)\1$|^(.*)$")
    EXPORT_PREFIX = r"^\s*?export\s"

    logger = logging.getLogger(__name__)

    def __init__(self, filename: str | None = None) -> None:
        """
        Load local .env file.

        Args:
            filename: Optional filename (with path) to load, default is `.env`
        """
        self._loaded_values: dict[str, str] = {}
        self._filename = filename

    @property
    def values(self) -> dict[str, str]:
        """Copy of loaded values"""
        return self._loaded_values.copy()

    def run(self) -> bool:
        """Load .env, or instantiated filename, to class state and environ."""
        was_loaded = self._load_values()

        for key, value in self._loaded_values.items():
            self.logger.debug("Found, %s : ***%s", key, value[-(len(value) // 4) :])
            os.environ[key] = value

        return was_loaded

    def _load_values(self, filename: str | None = None, **kwargs: str) -> bool:
        """
        Load values from .env, or provided filename, to class state.

        Args:
            filename : [str] Alternate filename to load over `.env`
        """
        filename = self._filename or filename or ".env"
        self.logger.debug("Reading vars from '%s'", filename)
        try:
            with open(filename, "r", encoding="utf-8") as input_file:
                self.parse_env_file(input_file.read())
        except FileNotFoundError:
            return False
        return True

    def parse_env_file(self, input_file: str) -> None:
        """Parses env file into key-pair values"""
        for line in input_file.split("\n"):
            if not line or line.strip().startswith("#") or len(line.split("=", 1)) != 2:
                continue
            key, value = line.split("=", 1)

            key = self.strip_export(key).strip()
            value = value.strip()

            value = self.remove_lt_quotes(value)

            self._loaded_values[key] = value

    def remove_lt_quotes(self, in_: str) -> str:
        """Removes matched leading and trailing single / double quotes"""
        m = self.RE_LTQUOTES.match(in_)
        return m.group(2) if m and m.group(2) else in_

    def strip_export(self, in_: str) -> str:
        """Removes leading 'export ' prefix, case agnostic"""
        return re.sub(self.EXPORT_PREFIX, "", in_, flags=re.IGNORECASE)
