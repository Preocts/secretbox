"""
Load secrets from an AWS secret manager

Author  : Preocts <Preocts#8196>
Git Repo: https://github.com/Preocts/secretbox
"""
from __future__ import annotations

import json
from typing import Any

try:
    import boto3
    from botocore.exceptions import ClientError
    from botocore.exceptions import NoCredentialsError
except ImportError:
    boto3 = None

try:
    from mypy_boto3_secretsmanager.client import SecretsManagerClient
except ImportError:
    SecretsManagerClient = None

from secretbox.aws_loader import AWSLoader


class AWSSecretLoader(AWSLoader):
    def __init__(
        self,
        aws_sstore_name: str | None = None,
        aws_region_name: str | None = None,
    ) -> None:
        """
        Load secrets from an AWS secret manager.

        Args:
            aws_sstore: Name of the secret store (not the arn)
                Can be provided through environ `AWS_SSTORE_NAME`
            aws_region: Regional location of secret store
                Can be provided through environ `AWS_REGION_NAME` or `AWS_REGION`
        """
        self.aws_sstore = aws_sstore_name
        self.aws_region = aws_region_name

        self._loaded_values: dict[str, str] = {}

    @property
    def values(self) -> dict[str, str]:
        """Copy of loaded values"""
        return self._loaded_values.copy()

    def run(self) -> bool:
        """Load all secrets from given AWS secret store."""
        has_loaded = self._load_values()

        for key, value in self._loaded_values.items():
            self.logger.debug("Found, %s : ***%s", key, value[-(len(value) // 4) :])

        return has_loaded

    def _load_values(
        self,
        aws_sstore_name: str | None = None,
        aws_region_name: str | None = None,
        **kwargs: Any,
    ) -> bool:
        """
        Load all secrets from AWS secret store.

        Parameter values set at class instantiation are used if values
        are not provided here.

        Args:
            aws_sstore: Name of the secret store (not the arn)
                Can be provided through environ `AWS_SSTORE_NAME`
            aws_region: Regional location of secret store
                Can be provided through environ `AWS_REGION_NAME` or `AWS_REGION`

        Keyword Args:
            Deprecated.
        """
        if boto3 is None:
            self.logger.error("Required boto3 modules missing, can't load AWS secrets")
            return False

        aws_sstore = aws_sstore_name or self.aws_sstore
        aws_region = aws_region_name or self.aws_region

        self.populate_region_store_names(aws_sstore, aws_region, **kwargs)
        if self.aws_sstore is None:
            self.logger.error("Missing secret store name")
            return False

        aws_client = self.get_aws_client()
        if aws_client is None:
            self.logger.error("Invalid secrets manager client")
            return False

        secrets: dict[str, str] = {}
        try:
            # ensure that boto3 doesn't write sensitive payload to the logger
            with self.disable_debug_logging():
                response = aws_client.get_secret_value(SecretId=self.aws_sstore)

        except NoCredentialsError as err:
            self.logger.error("Missing AWS credentials (%s)", err)

        except ClientError as err:
            self.log_aws_error(err)

        else:
            secrets = self._resolve_response(response)
            self._loaded_values.update(secrets)

        return bool(secrets)

    def _resolve_response(self, response: Any) -> dict[str, str]:
        """Resolve response body to json."""
        try:
            secrets = json.loads(response.get("SecretString", "{}"))
        except json.JSONDecodeError:
            secrets = {response.get("Name", ""): response.get("SecretString", "")}
        self.logger.debug("Found %s values from AWS.", len(secrets))

        return secrets

    def get_aws_client(self) -> SecretsManagerClient | None:
        """Return Secrets Manager client"""

        if not self.aws_region:
            self.logger.error("No valid AWS region, cannot create client.")
            return None

        with self.disable_debug_logging():
            client = boto3.client(
                service_name="secretsmanager",
                region_name=self.aws_region,
            )

        return client
