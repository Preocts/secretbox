"""
Loads various environment variables/secrets for use

Author  : Preocts <Preocts#8196>
Git Repo: https://github.com/Preocts/secretbox
"""
from __future__ import annotations

import logging
import os
from typing import Any

from secretbox.awsparameterstore_loader import (
    AWSParameterStoreLoader as _AWSParameterStoreLoader,
)
from secretbox.awssecret_loader import AWSSecretLoader as _AWSSecretLoader
from secretbox.envfile_loader import EnvFileLoader as _EnvFileLoader
from secretbox.environ_loader import EnvironLoader as _EnvironLoader
from secretbox.loader import Loader

# To be removed with 2.8.0
LOADERS: dict[str, type[Loader]] = {
    "envfile": _EnvFileLoader,
    "environ": _EnvironLoader,
    "awssecret": _AWSSecretLoader,
    "awsparameterstore": _AWSParameterStoreLoader,
}


class SecretBox:
    """Loads various environment variables/secrets for use"""

    _logger = logging.getLogger(__name__)
    AWSParameterStoreLoader = _AWSParameterStoreLoader
    AWSSecretLoader = _AWSSecretLoader
    EnvFileLoader = _EnvFileLoader
    EnvironLoader = _EnvironLoader

    def __init__(
        self,
        *,
        auto_load: bool = False,
        debug_flag: bool = False,
    ) -> None:
        """
        Initialize SecretBox

        Keyword Args:
            auto_load : If true, environment vars and `.env` file will be loaded
            load_debug : When true, internal logger level is set to DEBUG
        """
        self._logger.setLevel(level="DEBUG" if debug_flag else "ERROR")
        self._logger.debug("Debug flag passed.")

        self._loaded_values: dict[str, str] = {}

        if auto_load:
            self.use_loaders(self.EnvironLoader(), self.EnvFileLoader())

    @property
    def values(self) -> dict[str, str]:
        """Property: loaded values."""
        return self._loaded_values.copy()

    def use_loaders(self, *loaders: Loader) -> None:
        """
        Loaded results are injected into environ and stored in state.

        Args:
            loaders: Variable length argument list of Loaders to execute.
        """
        for loader in loaders:
            loader.run()
            self._loaded_values.update(loader.values)

        self._push_to_environment()

    def load_from(
        self,
        loaders: list[str],
        **kwargs: Any,
    ) -> None:
        """
        Runs load_values from each of the listed loader in the order they appear

        Deprecated: This method will be replaced with `.use_loaders()` in v2.7.0

        Loader options:
            environ:
                Loads the current environmental variables into secretbox.
            envfile:
                Loads .env file. Optional `filename` kwarg can override the default
                load of the current working directory `.env` file.
            awssecret:
                Loads secrets from an AWS secret manager. Requires `aws_sstore_name`
                and `aws_region_name` keywords to be provided or for those values
                to be in the environment variables under `AWS_SSTORE_NAME` and
                `AWS_REGION_NAME`. `aws_sstore_name` is not the arn.
        """
        self._logger.warning("Deprecated: `.load_from()` will be removed in v2.8.0")
        for loader_name in loaders:
            self._logger.debug("Loading from interface: `%s`", loader_name)
            interface = LOADERS.get(loader_name)
            if interface is None:
                self._logger.error("Loader `%s` unknown, skipping", loader_name)
                continue
            loader = interface()
            loader._load_values(**kwargs)
            self._logger.debug("Loaded %d values.", len(loader.values))
            self._update_loaded_values(loader.values)
        self._push_to_environment()

    def _update_loaded_values(self, new_values: dict[str, str]) -> None:
        """Update/Create instance state of loaded values with new values"""
        self._loaded_values.update(new_values)

    def _push_to_environment(self) -> None:
        """Pushes loaded values to local environment vars, will overwrite existing"""
        for key, value in self._loaded_values.items():
            self._logger.debug("Push, %s : ***%s", key, value[-(len(value) // 4) :])
            os.environ[key] = value

    def get(self, key: str, default: str | None = None) -> str:
        """Get a value by key, return default if not found or raise if no default"""
        if default is None:
            return self._loaded_values[key]

        return self._loaded_values.get(key, default)

    def set(self, key: str, value: str) -> None:  # noqa: A003
        """Set a value by key. Will be converted to string and pushed to environment."""
        value = str(value)
        self._loaded_values[key] = value
        self._push_to_environment()
