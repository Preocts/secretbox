"""
Loads various environment variables/secrets for use

Author  : Preocts
Discord : Preocts#8196
Git Repo: https://github.com/Preocts/secretbox
"""
import json
import logging
import os
from typing import Dict
from typing import Optional

try:
    import boto3
    from botocore.exceptions import ClientError
    from botocore.exceptions import InvalidRegionError
    from botocore.exceptions import NoCredentialsError
    from botocore.exceptions import NoRegionError
    from mypy_boto3_secretsmanager.client import SecretsManagerClient
except ImportError:
    boto3 = None
    SecretsManagerClient = None


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
        self.loaded_values: Dict[str, str] = {}
        self.aws_region = env_region if aws_region_name is None else aws_region_name
        self.aws_sstore = env_sstore if aws_sstore_name is None else aws_sstore_name
        if auto_load:
            self.load()

    def get(self, key: str, default: str = "") -> str:
        """Get a value by key, will return default if not found"""
        return self.loaded_values[key] if key in self.loaded_values else default

    def load(self) -> None:
        """
        Runs all available loaders

        Order of loading: local environment -> .env file -> aws secrets
        """
        self.load_env_vars()
        self.load_env_file()
        if boto3 is not None and (self.aws_region and self.aws_sstore):
            self.load_aws_store()
        self.push_to_environment()

    def load_env_vars(self) -> None:
        """Loads all visible environmental variables"""
        self.logger.debug("Reading %s environ variables", len(os.environ))
        for key, value in os.environ.items():
            self.loaded_values[key] = value

    def load_env_file(self) -> bool:
        """Loads local .env or from path if provided"""
        self.logger.debug("Reading vars from '%s'", self.filename)
        try:
            with open(self.filename, "r", encoding="utf-8") as input_file:
                self.__parse_env_file(input_file.read())
        except FileNotFoundError:
            return False
        return True

    def load_aws_store(self) -> bool:
        """Load all secrets from AWS secret store"""
        secrets: Dict[str, str] = {}
        aws_client = self.__connect_aws_client()
        if aws_client is None or self.aws_sstore is None:
            self.logger.debug("Cannot load AWS secrets, no valid client.")
            return False

        try:
            response = aws_client.get_secret_value(SecretId=self.aws_sstore)

        except NoCredentialsError as err:
            self.logger.error("Error routing message! %s", err)

        except ClientError as err:
            code = err.response["Error"]["Code"]
            self.logger.error("ClientError: %s, (%s)", err, code)

        else:
            self.logger.debug("Found %s values from AWS.", len(secrets))
            secrets = json.loads(response.get("SecretString", "{}"))
            for key, value in secrets.items():
                self.loaded_values[key] = value
        return bool(secrets)

    def push_to_environment(self) -> None:
        """Pushes loaded values to local environment vars, will overwrite existing"""
        for key, value in self.loaded_values.items():
            self.logger.debug("Push, %s : ***%s", key, value[-(len(value) // 4) :])
            os.environ[key] = value

    def __parse_env_file(self, input_file: str) -> None:
        """Parses env file into key-pair values"""
        for line in input_file.split("\n"):
            if not line or line.strip().startswith("#") or len(line.split("=", 1)) != 2:
                continue
            key, value_dirty = line.split("=", 1)

            value = self.__remove_lt_dbl_quotes(value_dirty.strip())
            value = self.__remove_lt_sgl_quotes(value)

            self.loaded_values[key.strip()] = value

    def __remove_lt_dbl_quotes(self, in_: str) -> str:
        """Removes matched leading and trailing double quotes"""
        return in_.strip('"') if in_.startswith('"') and in_.endswith('"') else in_

    def __remove_lt_sgl_quotes(self, in_: str) -> str:
        """Removes matched leading and trailing double quotes"""
        return in_.strip("'") if in_.startswith("'") and in_.endswith("'") else in_

    def __connect_aws_client(self) -> Optional[SecretsManagerClient]:
        """Make connection"""
        client: Optional[SecretsManagerClient] = None
        if self.aws_region is None:
            return client

        if boto3 is not None:
            session = boto3.session.Session()
        else:
            raise NotImplementedError(
                "Need to 'pip install secretbox[aws] to use 'load_aws_store()'"
            )

        try:
            client = session.client(
                service_name="secretsmanager",
                region_name=self.aws_region,
            )

        except (ValueError, InvalidRegionError, NoRegionError) as err:
            self.logger.error("Error creating AWS Secrets client: %s", err)

        return client
