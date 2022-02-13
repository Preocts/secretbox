"""
Loads various environment variables/secrets for use

Author  : Preocts <Preocts#8196>
Git Repo: https://github.com/Preocts/secretbox
"""
from __future__ import annotations

import logging
import os
from typing import Any

from secretbox.awsparameterstore_loader import AWSParameterStore
from secretbox.awssecret_loader import AWSSecretLoader
from secretbox.envfile_loader import EnvFileLoader
from secretbox.environ_loader import EnvironLoader
from secretbox.loader import Loader

LOADERS: dict[str, type[Loader]] = {
    "envfile": EnvFileLoader,
    "environ": EnvironLoader,
    "awssecret": AWSSecretLoader,
    "awsparameterstore": AWSParameterStore,
}


class SecretBox:
    """Loads various environment variables/secrets for use"""

    logger = logging.getLogger(__name__)

    def __init__(
        self,
        *,
        auto_load: bool = False,
        debug_flag: bool = False,
        **kwargs: Any,
    ) -> None:
        """
        Initialize SecretBox

        Keyword Args:
            auto_load : If true, environment vars and `.env` will be loaded
            load_debug : When true, internal logger level is set to DEBUG

        Additional Keywords:
            These will be passed to all loaders when called
        """
        self.logger.setLevel(level="DEBUG" if debug_flag else "ERROR")
        self.logger.debug("Debug flag passed.")

        self.loaded_values: dict[str, str] = {}
        self.kwarg_defaults = kwargs

        if auto_load:
            self.load_from(["environ", "envfile"])

    def get(self, key: str, default: str | None = None) -> str:
        """Get a value by key, return default if not found or raise if no default"""
        if default is None:
            return self.loaded_values[key]

        return self.loaded_values.get(key, default)

    def get_int(self, key: str, default: int | None = None) -> int:
        """Convert value by key to int."""
        if default is None:
            return int(self.get(key))

        value = self.get(key, "")
        return int(value) if value else default

    def get_list(
        self,
        key: str,
        delimiter: str = ",",
        default: list[str] | None = None,
    ) -> list[str]:
        """Convert value by key to list seperated by delimiter."""
        if default is None:
            default = []

        if not default:
            return self.get(key).split(delimiter)

        value = self.get(key, "")
        return value.split(delimiter) if value else default

    def load_from(
        self,
        loaders: list[str],
        **kwargs: Any,
    ) -> None:
        """
        Runs load_values from each of the listed loader in the order they appear

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
        for loader_name in loaders:
            self.logger.debug("Loading from interface: `%s`", loader_name)
            interface = LOADERS.get(loader_name)
            if interface is None:
                self.logger.error("Loader `%s` unknown, skipping", loader_name)
                continue
            loader = interface()
            loader.load_values(**self._join_kwarg_defaults(kwargs))
            self.logger.debug("Loaded %d values.", len(loader.loaded_values))
            self._update_loaded_values(loader.loaded_values)
        self._push_to_environment()

    def _update_loaded_values(self, new_values: dict[str, str]) -> None:
        """Update/Create instance state of loaded values with new values"""
        self.loaded_values.update(new_values)

    def _push_to_environment(self) -> None:
        """Pushes loaded values to local environment vars, will overwrite existing"""
        for key, value in self.loaded_values.items():
            self.logger.debug("Push, %s : ***%s", key, value[-(len(value) // 4) :])
            os.environ[key] = value

    def _join_kwarg_defaults(self, new_kwargs: dict[str, str]) -> dict[str, str]:
        """Update default kwargs with specific while not mutating either"""
        return {**self.kwarg_defaults, **new_kwargs}
