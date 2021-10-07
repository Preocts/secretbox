"""
Load secrets from an AWS secret manager

Author  : Preocts <Preocts#8196>
Git Repo: https://github.com/Preocts/secretbox
"""
import json
import logging
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

from secretbox.loader import Loader


class AWSLoader(Loader):
    """Load secrets from an AWS secret manager"""

    logger = logging.getLogger(__name__)

    def __init__(self) -> None:
        super().__init__()
        self.aws_sstore: Optional[str] = None
        self.aws_region: Optional[str] = None

    def get_values(self) -> Dict[str, str]:
        return self.loaded_values

    def reset_values(self) -> None:
        self.loaded_values = {}

    def load_values(self, **kwargs: Optional[str]) -> bool:
        """Load all secrets from AWS secret store"""
        if boto3 is None:
            self.logger.debug("Skipping AWS loader, boto3 is not available.")
            return False

        self.reset_values()
        self.aws_sstore = kwargs.get("aws_sstore")
        self.aws_region = kwargs.get("aws_region")

        secrets: Dict[str, str] = {}
        aws_client = self.connect_aws_client()
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

    def connect_aws_client(self) -> Optional[SecretsManagerClient]:
        """Make connection"""
        client: Optional[SecretsManagerClient] = None
        session = boto3.session.Session()

        if self.aws_region is None:
            self.logger.debug("No valid AWS region, cannot create client.")

        else:
            try:
                client = session.client(
                    service_name="secretsmanager",
                    region_name=self.aws_region,
                )
            except (ValueError, InvalidRegionError, NoRegionError) as err:
                self.logger.error("Error creating AWS Secrets client: %s", err)

        return client
