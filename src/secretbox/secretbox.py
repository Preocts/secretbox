"""
Loads various environment variables/secrets for use

Author  : Preocts <Preocts#8196>
Git Repo: https://github.com/Preocts/secretbox
"""
import logging
import os
from typing import Dict
from typing import Optional

from secretbox.aws_loader import AWSLoader
from secretbox.envfile_loader import EnvFileLoader
from secretbox.environ_loader import EnvironLoader


class SecretBox:
    """Loads various environment variables/secrets for use"""

    logger = logging.getLogger(__name__)
    environ = EnvironLoader()
    envfile = EnvFileLoader()
    awssecrets = AWSLoader()

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
        self.loaded_values: Dict[str, str] = {}
        self.aws_region = env_region if aws_region_name is None else aws_region_name
        self.aws_sstore = env_sstore if aws_sstore_name is None else aws_sstore_name
        if auto_load:
            self.load()

    def get(self, key: str, default: str = "") -> str:
        """Get a value by key, will return default if not found"""
        return self.loaded_values[key] if key in self.loaded_values else default

    def load(self) -> None:
        """Runs all available loaders"""
        # TODO (preocts): Determine available loaders at runtime
        self.load_env_vars()
        self.load_env_file()
        self.load_aws_store()
        self.push_to_environment()

    def load_env_vars(self) -> None:
        """Load environ values"""
        self.environ.load_values()
        self.loaded_values.update(self.environ.get_values())

    def load_env_file(self) -> None:
        """Load env file values"""
        self.envfile.load_values(filename=self.filename)
        self.loaded_values.update(self.envfile.get_values())

    def load_aws_store(self) -> None:
        """Load secrets from AWS secret manager"""
        self.awssecrets.load_values(
            aws_sstore=self.aws_sstore,
            aws_region=self.aws_region,
        )
        self.loaded_values.update(self.awssecrets.get_values())

    def push_to_environment(self) -> None:
        """Pushes loaded values to local environment vars, will overwrite existing"""
        for key, value in self.loaded_values.items():
            self.logger.debug("Push, %s : ***%s", key, value[-(len(value) // 4) :])
            os.environ[key] = value
