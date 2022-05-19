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
    """Load secrets from an AWS secret manager"""

    def load_values(self, **kwargs: Any) -> bool:
        """
        Load all secrets from AWS secret store
        Requires `aws_sstore_name` and `aws_region_name` keywords to be
        provided or for those values to be in the environment variables
        under `AWS_SSTORE_NAME` and `AWS_REGION_NAME`.

        `aws_sstore_name` is the name of the store, not the arn.
        """
        if boto3 is None:
            self.logger.error("Required boto3 modules missing, can't load AWS secrets")
            return False

        self.populate_region_store_names(**kwargs)
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
            self.loaded_values.update(secrets)

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
