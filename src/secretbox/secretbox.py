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
from typing import Optional
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
        filename: str = ".env",
        aws_sstore_name: Optional[str] = None,
        aws_region_name: Optional[str] = None,
        auto_load: bool = False,
        debug_flag: bool = False,
    ) -> None:
        """
        Creates an unloaded instance of class

        Order of loading is environment -> .env file -> aws secrets

        Args:
            filename : You can specify a `.env` formatted file and location,
                overriding the default behavior to load the `.env` from the
                working directory
            aws_sstore_name : When provided, an attempt to load values from
                named AWS secrets manager will be made. Can be provided with
                the `AWS_SSTORE_NAME` environment variable.
                Requires `boto3` and `boto3-stubs[secretsmanager]` to be installed.
            aws_region_name : When provided, an attempt to load values from the given
                AWS secrets manager found in this region will be made. Can be provided
                with the `AWS_REGION_NAME` environment variable.
                Requires `boto3` and `boto3-stubs[secretsmanager]` to be installed
            auto_load : If true, the `load()` method will be auto-executed
            load_debug : When true, internal logger level is set to DEBUG

        """
        self.logger.setLevel(level="DEBUG" if debug_flag else "ERROR")
        self.logger.debug("Debug flag passed.")
        env_region = os.getenv("AWS_REGION_NAME")
        env_sstore = os.getenv("AWS_SSTORE_NAME")
        self.filename: str = filename
        self.aws_region = env_region if aws_region_name is None else aws_region_name
        self.aws_sstore = env_sstore if aws_sstore_name is None else aws_sstore_name

        self.loaded_values: Dict[str, str] = {}

        if auto_load:
            self.load()

    def get(self, key: str, default: str = "") -> str:
        """Get a value by key, will return default if not found"""
        return self.loaded_values[key] if key in self.loaded_values else default

    def load_from(self, loaders: List[str], **kwargs: Any) -> None:
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
                `AWS_REGION_NAME`. `aws_sstore` is the name of the store, not the arn.
        """
        for loader_name in loaders:
            self.logger.debug("Loading from interface: `%s`", loader_name)
            interface = LOADERS.get(loader_name)
            if interface is None:
                self.logger.warning("Loader `%s` unknown, skipping", loader_name)
                continue
            loader = interface()
            loader.load_values(**kwargs)
            self.logger.debug("Loaded %d values.", len(loader.loaded_values))
            self.loaded_values.update(loader.loaded_values)
            self.push_to_environment()

    # TODO(preocts): Left to preserve v1 API. Remove in v2
    def load(self) -> None:
        """Runs all available loaders"""
        self.load_env_vars()
        self.load_env_file()
        self.load_aws_store()
        self.push_to_environment()

    # TODO(preocts): Left to preserve v1 API. Remove in v2
    def load_env_vars(self) -> None:
        """Loads all existing `os.environ` values into state"""
        self.load_from(["environ"])

    # TODO(preocts): Left to preserve v1 API. Remove in v2
    def load_env_file(self) -> None:
        """Loads `.env` file or file provided"""
        self.load_from(["envfile"], filename=self.filename)

    # TODO(preocts): Left to preserve v1 API. Remove in v2
    def load_aws_store(self) -> None:
        """Loads secrets from AWS secret manager"""
        self.load_from(
            ["awssecret"],
            aws_sstore=self.aws_sstore,
            aws_region=self.aws_region,
        )

    def push_to_environment(self) -> None:
        """Pushes loaded values to local environment vars, will overwrite existing"""
        for key, value in self.loaded_values.items():
            self.logger.debug("Push, %s : ***%s", key, value[-(len(value) // 4) :])
            os.environ[key] = value
