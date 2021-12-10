"""
Author      : James McKain (@jjmckain)
Created     : 2021-12-10
SCM Repo    : https://github.com/Preocts/secretbox
"""
import boto3
import logging
from typing import Any, Optional
from secretbox.awssecret_loader import AWSSecretLoader


class AWSParameterStore(AWSSecretLoader):
    """Load secrets from an AWS Parameter Store"""

    logger = logging.getLogger(__name__)

    def __init__(self) -> None:
        super().__init__()

    def load_values(self, **kwargs: Any) -> bool:
        """
        Load all secrets from AWS secret store
        Requires `aws_sstore_name` and `aws_region_name` keywords to be
        provided or for those values to be in the environment variables
        under `AWS_SSTORE_NAME` and `AWS_REGION_NAME`.

        `aws_sstore_name` is the name of the store, not the arn.
        """
        self.populate_region_store_names(**kwargs)
        aws_client = self.connect_aws_client()

        if aws_client is None or self.aws_sstore is None:
            self.logger.error("Cannot load AWS secrets, invalid client.")
            return False

        try:
            # ensure the http client doesn't write our sensitive payload to the logger
            logging.getLogger("botocore.parsers").addFilter(self.secrets_filter)

            args = {
                "Path": self.aws_sstore,
                "Recursive": True,
                "MaxResults": 10,
                "WithDecryption": True
            }

            # loop through next page tokens, page size caps at 10
            while True:
                resp = aws_client.get_parameters_by_path(**args)
                for param in resp.Parameters or []:
                    self.loaded_values[param['Name']] = param['Value']

                if resp.NextToken:
                    args['NextToken'] = resp.NextToken
                    self.logger.debug("fetching next page: %s", args['NextToken'])
                else:
                    break

        except Exception as err:
            self.logger.error("Error retrieving from parameter store: %s", err)
            return False

        finally:
            # remove our logging filter
            logging.getLogger("botocore.parsers").removeFilter(self.secrets_filter)

        self.logger.info(
            "loaded %d parameters matching %s",
            len(self.loaded_values),
            self.aws_sstore
        )
        return True

    def connect_aws_client(self) -> Optional[SecretsManagerClient]:
        """Make connection"""
        client: Optional[SecretsManagerClient] = None
        session = boto3.session.Session()

        if self.aws_region is None:
            self.logger.debug("No valid AWS region, cannot create client.")

        else:
            try:
                client = session.client(
                    service_name="ssm",
                    region_name=self.aws_region,
                )
            except (ValueError, InvalidRegionError, NoRegionError) as err:
                self.logger.error("Error creating AWS Secrets client: %s", err)

        return client
