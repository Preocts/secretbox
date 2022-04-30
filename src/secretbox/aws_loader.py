"""
Super class for AWS secrets manager and parameter store loaders

Author  : Preocts <preocts#8196>
Git Repo: https://github.com/Preocts/secretbox
"""
from __future__ import annotations

import logging
import os
from contextlib import contextmanager
from typing import Any
from typing import Generator

try:
    from botocore.awsrequest import HeadersDict
except ImportError:
    HeadersDict = dict

from secretbox.loader import Loader


class AWSLoader(Loader):
    """Super class with mutual methods of AWS loaders, inherits Loader"""

    logger = logging.getLogger(__name__)

    # Override hide_boto_debug to False to allow full debug logging of boto3 libraries
    # NOTE: This exposes sensitive data and should never be in production
    hide_boto_debug = True

    def __init__(self) -> None:
        super().__init__()
        self.aws_sstore: str | None = None
        self.aws_region: str | None = None

    def get_aws_client(self) -> Any:
        """Returns correct AWS client for low-level API requests"""
        # NOTE: Override in client specific implementation
        raise NotImplementedError

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

    @contextmanager
    def filter_boto_debug(self) -> Generator[None, None, None]:
        """Context manager to enforce level 20 (INFO) logging minimum at root logger."""
        current_level = self.logger.root.level
        if self.hide_boto_debug and self.logger.root.level < logging.INFO:
            self.logger.root.level = logging.INFO

        try:
            yield None
        finally:
            self.logger.root.level = current_level
