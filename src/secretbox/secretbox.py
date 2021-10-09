"""
Loads various environment variables/secrets for use

Author  : Preocts <Preocts#8196>
Git Repo: https://github.com/Preocts/secretbox
"""
import logging
import os
from typing import Any
from typing import Dict
from typing import List
from typing import Type

from secretbox.awssecret_loader import AWSSecretLoader
from secretbox.envfile_loader import EnvFileLoader
from secretbox.environ_loader import EnvironLoader
from secretbox.loader import Loader

LOADERS: Dict[str, Type[Loader]] = {
    "envfile": EnvFileLoader,
    "environ": EnvironLoader,
    "awssecret": AWSSecretLoader,
}


class SecretBox:
    """Loads various environment variables/secrets for use"""

    logger = logging.getLogger(__name__)

    def __init__(
        self,
        auto_load: bool = False,
        debug_flag: bool = False,
        **kwargs: Any,
    ) -> None:
        """
        Initialize SecretBox

        Args:
            auto_load : If true, environment vars and `.env` will be loaded
            load_debug : When true, internal logger level is set to DEBUG

        Keywords:
            These will be passed to all loaders when called
        """
        self.logger.setLevel(level="DEBUG" if debug_flag else "ERROR")
        self.logger.debug("Debug flag passed.")

        self.loaded_values: Dict[str, str] = {}
        self.kwarg_defaults = kwargs

        if auto_load:
            self.load_from(["environ", "envfile"])

    def get(self, key: str, default: str = "") -> str:
        """Get a value by key, will return default if not found"""
        return self.loaded_values[key] if key in self.loaded_values else default

    def load_from(
        self,
        loaders: List[str],
        **kwargs: Any,
    ) -> None:
        """
        Runs load_values from each of the listed loadered in the order they appear

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
                self.logger.warning("Loader `%s` unknown, skipping", loader_name)
                continue
            loader = interface()
            loader.load_values(**self._join_kwarg_defaults(kwargs))
            self.logger.debug("Loaded %d values.", len(loader.loaded_values))
            self._update_loaded_values(loader.loaded_values)
        self._push_to_environment()

    def _update_loaded_values(self, new_values: Dict[str, str]) -> None:
        """Update/Create instance state of loaded values with new values"""
        self.loaded_values.update(new_values)

    def _push_to_environment(self) -> None:
        """Pushes loaded values to local environment vars, will overwrite existing"""
        for key, value in self.loaded_values.items():
            self.logger.debug("Push, %s : ***%s", key, value[-(len(value) // 4) :])
            os.environ[key] = value

    def _join_kwarg_defaults(self, new_kwargs: Dict[str, str]) -> Dict[str, str]:
        """Update default kwargs with specific while not mutating either"""
        base = self.kwarg_defaults.copy()
        base.update(new_kwargs)
        return base
