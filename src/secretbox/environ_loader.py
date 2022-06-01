"""
Load system environ values

Author  : Preocts <Preocts#8196>
Git Repo: https://github.com/Preocts/secretbox
"""
from __future__ import annotations

import logging
import os

from secretbox.loader import Loader


class EnvironLoader(Loader):
    """Load environ values"""

    logger = logging.getLogger(__name__)

    def __init__(self) -> None:
        """Load system environ values"""
        self._loaded_values: dict[str, str] = {}

    @property
    def values(self) -> dict[str, str]:
        """Copy of loaded values"""
        return self._loaded_values.copy()

    def _load_values(self, **kwargs: str) -> bool:
        """Load all environmental variables."""
        self.logger.debug("Reading %s environ variables", len(os.environ))
        self._loaded_values.update(os.environ)
        return True

    def run(self) -> bool:
        """Load all environ variables."""
        has_loaded = self._load_values()

        for key, value in self._loaded_values.items():
            self.logger.debug("Found, %s : ***%s", key, value[-(len(value) // 4) :])

        return has_loaded
