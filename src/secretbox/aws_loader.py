"""
Super class for AWS secrets manager and parameter store loaders

Author  : Preocts <preocts#8196>
Git Repo: https://github.com/Preocts/secretbox
"""
import logging
import os
from typing import Any
from typing import Dict
from typing import Optional

try:
    from botocore.awsrequest import HeadersDict
except ImportError:
    HeadersDict = Dict

from secretbox.loader import Loader


class AWSLoader(Loader):
    """Super class with mutual methods of AWS loaders, inherits Loader"""

    logger = logging.getLogger(__name__)
    # Override filter_secrets to False to allow full debug logging of boto3.parsers
    filter_secrets = True

    def __init__(self) -> None:
        super().__init__()
        self.aws_sstore: Optional[str] = None
        self.aws_region: Optional[str] = None

    def get_aws_client(self) -> Any:
        """Returns correct AWS client for low-level API requests"""
        # NOTE: Override in client specific implementation
        raise NotImplementedError  # pragma: no cover

    def populate_region_store_names(self, **kwargs: Any) -> None:
        """Populates store/region name"""
        kw_sstore = kwargs.get("aws_sstore_name")
        kw_region = kwargs.get("aws_region_name")
        os_sstore = os.getenv("AWS_SSTORE_NAME")
        os_region = os.getenv("AWS_REGION_NAME", os.getenv("AWS_REGION"))  # Lambda's

        # Use the keyword over the os, default to None
        self.aws_sstore = kw_sstore if kw_sstore is not None else os_sstore
        self.aws_region = kw_region if kw_region is not None else os_region
        self.logger.debug("Using store name '%s'", self.aws_sstore)
        self.logger.debug("Using region name '%s'", self.aws_region)

    def log_aws_error(self, err: Any) -> None:
        """Verbose AWS error log output. If not an AWS error, generic repl of err"""
        if (
            hasattr(err, "response")  # assert attribute exists or fail early
            and "Error" in err.response
            and "ResponseMetadata" in err.response
        ):
            self.logger.error(
                "%s - %s (%s)",
                err.response["Error"]["Code"],
                err.response["Error"]["Message"],
                err.response["ResponseMetadata"],
            )
        else:
            self.logger.error("Unexpected error occurred: '%s'", str(err))

    @staticmethod
    def secrets_filter(record: logging.LogRecord) -> bool:
        """
        Hide botocore.parsers responses which include decrypted secrets

        https://github.com/boto/botocore/issues/1211#issuecomment-327799341
        """
        if record.levelno > logging.DEBUG or not AWSLoader.filter_secrets:
            return True
        if "body" in record.msg or "headers" in record.msg:
            if isinstance(record.args, tuple):
                record.args = ("REDACTED",) * len(record.args)
            elif isinstance(record.args, (dict, HeadersDict)):
                record.args = {key: "REDACTED" for key in record.args}
            else:
                record.args = ("REDACTED",)
        return True
