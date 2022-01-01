"""
Author      : James McKain (@jjmckain)
Created     : 2021-12-10
SCM Repo    : https://github.com/Preocts/secretbox
"""
import logging
from typing import Any
from typing import Optional

from secretbox.aws_loader import AWSLoader

try:
    import boto3
    from botocore.exceptions import ClientError
except ImportError:
    boto3 = None

try:
    from mypy_boto3_ssm.client import SSMClient
except ImportError:
    SSMClient = None


class AWSParameterStore(AWSLoader):
    """Load secrets from an AWS Parameter Store"""

    def __init__(self) -> None:
        super().__init__()

    def load_values(self, **kwargs: Any) -> bool:
        """
        Load all secrets from AWS parameter store
        Requires `aws_sstore_name` and `aws_region_name` keywords to be
        provided or for those values to be in the environment variables
        under `AWS_SSTORE_NAME` and `AWS_REGION_NAME`.

        `aws_sstore_name` is the parameter name or prefix.
        """
        if boto3 is None:
            self.logger.debug("Skipping AWS loader, boto3 is not available.")
            return False

        self.populate_region_store_names(**kwargs)
        if self.aws_sstore is None:
            self.logger.warning("Missing parameter name")
            return True  # this isn't a failure on our part

        aws_client = self.get_aws_client()
        if aws_client is None:
            self.logger.error("Invalid SSM client")
            return False

        # if the prefix contains forward slashes treat the last token as the key name
        do_split = "/" in self.aws_sstore

        try:
            # ensure the http client doesn't write our sensitive payload to the logger
            logging.getLogger("botocore.parsers").addFilter(self.secrets_filter)

            args = {
                "Path": self.aws_sstore,
                "Recursive": True,
                "MaxResults": 10,
                "WithDecryption": True,
            }

            # loop through next page tokens, page size caps at 10
            while True:
                resp = aws_client.get_parameters_by_path(**args)
                for param in resp["Parameters"] or []:
                    # remove the prefix
                    # we want /path/to/DB_PASSWORD to populate os.env.DB_PASSWORD
                    key = param["Name"].split("/")[-1] if do_split else param["Name"]
                    self.loaded_values[key] = param["Value"]

                if "NextToken" in resp and resp["NextToken"]:
                    args["NextToken"] = resp["NextToken"]
                    self.logger.debug("fetching next page: %s", args["NextToken"])
                else:
                    break

        except ClientError as err:
            self.log_aws_error(err)
            return False

        finally:
            # remove our logging filter
            logging.getLogger("botocore.parsers").removeFilter(self.secrets_filter)

        self.logger.info(
            "loaded %d parameters matching %s", len(self.loaded_values), self.aws_sstore
        )
        return True

    def get_aws_client(self) -> Optional[SSMClient]:
        """Make the connection"""

        if self.aws_region is None:
            self.logger.debug("Missing AWS region, cannot create client")
            return None

        try:
            # session = boto3.session.Session()
            return boto3.client(
                service_name="ssm",
                region_name=self.aws_region,
            )
        except ClientError as err:
            self.log_aws_error(err)
            return None
