import json
import logging
from typing import Dict
from typing import Optional

import boto3
from botocore.exceptions import ClientError
from botocore.exceptions import InvalidRegionError
from botocore.exceptions import NoCredentialsError
from botocore.exceptions import NoRegionError
from mypy_boto3_secretsmanager.client import SecretsManagerClient

# boto3[secretsmanager]
# boto3-stubs[secretsmanager]


class AWS:

    logger = logging.getLogger(__name__)
    aws_client: Optional[SecretsManagerClient] = None

    def __init__(self) -> None:
        self.region: Optional[str] = None
        self.sstore: Optional[str] = None
        self.secrets: Dict[str, str] = {}

    def connect_aws_client(self) -> None:
        """Make connection"""

        if self.aws_client is not None or self.region is not None:
            return

        session = boto3.session.Session()

        try:
            client = session.client(
                service_name="secretsmanager",
                region_name="self.region",
            )
            self.aws_client = client
        except (ValueError, InvalidRegionError, NoRegionError) as err:
            self.logger.error("Error creating AWS Secrets client: %s", err)

    def load_aws_store(self) -> None:
        """Load all secrets from AWS secret store"""

        self.connect_aws_client()
        if self.aws_client is None or self.sstore is None:
            self.logger.warning("Cannot load AWS secrets, no valid client.")
            return

        secrets = {}

        try:
            response = self.aws_client.get_secret_value(SecretId=self.sstore)
        except NoCredentialsError as err:
            self.logger.error("Error routing message! %s", err)
        except ClientError as err:
            code = err.response["Error"]["Code"]
            self.logger.error("ClientError: %s, (%s)", err, code)
        else:
            secrets = json.loads(response.get("SecretString", "{}"))

        self.secrets.update(secrets)
