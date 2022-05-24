"""
Author      : James McKain (@jjmckain)
Created     : 2021-12-10
SCM Repo    : https://github.com/Preocts/secretbox
"""
from __future__ import annotations

from typing import Any

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


class AWSParameterStoreLoader(AWSLoader):
    """Load secrets from an AWS Parameter Store"""

    def __init__(
        self,
        aws_sstore_name: str | None = None,
        aws_region_name: str | None = None,
    ) -> None:
        """
        Load secrets from AWS parameter store.

        Args:
            aws_sstore: Name of parameter or path of parameters if endings with `/`
                Can be provided through environ `AWS_SSTORE_NAME`
            aws_region: Regional Location of parameter(s)
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
        """Load secrets from given AWS parameter store."""
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
        Load all secrets from AWS parameter store.

        Parameter values set at class instantiation are used if values
        are not provided here.

        Args:
            aws_sstore: Name of parameter or path of parameters if endings with `/`
                Can be provided through environ `AWS_SSTORE_NAME`
            aws_region: Regional Location of parameter(s)
                Can be provided through environ `AWS_REGION_NAME` or `AWS_REGION`

        Keyword Args:
            Deprecated.
        """
        if boto3 is None:
            self.logger.debug("Skipping AWS loader, boto3 is not available.")
            return False

        aws_sstore = aws_sstore_name or self.aws_sstore
        aws_region = aws_region_name or self.aws_region

        self.populate_region_store_names(aws_sstore, aws_region, **kwargs)
        if self.aws_sstore is None:
            self.logger.warning("Missing parameter name")
            return True  # this isn't a failure on our part

        aws_client = self.get_aws_client()
        if aws_client is None:
            self.logger.error("Invalid SSM client")
            return False

        # if the prefix contains forward slashes treat the last token as the key name
        do_split = "/" in self.aws_sstore

        args: dict[str, Any] = {
            "Path": self.aws_sstore,
            "Recursive": True,
            "MaxResults": 10,
            "WithDecryption": True,
        }

        # loop through next page tokens, page size caps at 10
        while True:

            try:
                # ensure that boto3 doesn't write sensitive payload to the logger
                with self.disable_debug_logging():
                    resp = aws_client.get_parameters_by_path(**args)

            except ClientError as err:
                self.log_aws_error(err)
                return False

            # Process results, break if finished
            for param in resp["Parameters"] or []:
                # remove the prefix
                # we want /path/to/DB_PASSWORD to populate os.env.DB_PASSWORD
                key = param["Name"].split("/")[-1] if do_split else param["Name"]
                self._loaded_values[key] = param["Value"]

            args["NextToken"] = resp.get("NextToken")

            if not args["NextToken"]:
                break

            self.logger.debug("fetching next page: %s", args["NextToken"])

        self.logger.info(
            "loaded %d parameters matching %s",
            len(self._loaded_values),
            self.aws_sstore,
        )
        return True

    def get_aws_client(self) -> SSMClient | None:
        """Make the connection"""

        if self.aws_region is None:
            self.logger.debug("Missing AWS region, cannot create client")
            return None

        with self.disable_debug_logging():
            client = boto3.client(
                service_name="ssm",
                region_name=self.aws_region,
            )

        return client
