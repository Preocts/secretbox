"""
Super class for AWS secrets manager and parameter store loaders

Author  : Preocts <preocts#8196>
Git Repo: https://github.com/Preocts/secretbox
"""
from __future__ import annotations

import logging
import os
from collections.abc import Generator
from contextlib import contextmanager
from typing import Any

from secretbox.exceptions import LoaderException
from secretbox.loader import Loader


class AWSLoader(Loader):
    """Super class with mutual methods of AWS loaders, inherits Loader"""

    logger = logging.getLogger(__name__)

    def __init__(
        self,
        aws_sstore_name: str | None = None,
        aws_region_name: str | None = None,
        *,
        hide_boto_debug: bool = True,
        capture_exceptions: bool = True,
    ) -> None:
        """
        Load secrets from AWS parameter store.

        Args:
            aws_sstore: Name of parameter or path of parameters if endings with `/`
                Can be provided through environ `AWS_SSTORE_NAME`
            aws_region: Regional Location of parameter(s)
                Can be provided through environ `AWS_REGION_NAME` or `AWS_REGION`
            hide_boto_debug: Hides debug output while using boto libraries
            capture_exceptions: All inner exceptions are captured, logged, and ignored
        """
        self.aws_sstore = aws_sstore_name
        self.aws_region = aws_region_name

        self._loaded_values: dict[str, str] = {}
        self._hide_boto_debug = hide_boto_debug
        self._capture_exceptions = capture_exceptions

    def _load_values(self, **kwargs: Any) -> bool:
        """To be overrided in child classes"""
        raise NotImplementedError()

    @property
    def values(self) -> dict[str, str]:
        """To be overrided in child classes"""
        raise NotImplementedError()

    def run(self) -> bool:
        """
        Load secrets from AWS. Returns success.

        Raises:
            secretbox.exceptions.LoaderException

            NOTE: Only raises if `capture_exceptions` is False
        """
        try:
            return self._run()

        # We use a blanket Exception catch here on purpose.
        except Exception as err:
            self.log_aws_error(err)
            if not self._capture_exceptions:
                raise LoaderException(err) from err

        return False

    def _run(self) -> bool:
        """Internal run called from self.run()."""
        # NOTE: To be implemented in child classes.
        raise NotImplementedError()

    def get_aws_client(self) -> Any:
        """Returns correct AWS client for low-level API requests"""
        # NOTE: Override in client specific implementation
        raise NotImplementedError

    def populate_region_store_names(
        self,
        sstore: str | None = None,
        region: str | None = None,
        **kwargs: str,
    ) -> None:
        """Populate store/region values."""
        kw_sstore = sstore or kwargs.get("aws_sstore_name")
        kw_region = region or kwargs.get("aws_region_name")
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
    def disable_debug_logging(self) -> Generator[None, None, None]:
        """Context manager to enforce level 20 (INFO) logging minimum at root logger."""
        # This should prevent boto and botocore loggers from outputting
        # client secrets in plaintext if debug logging is on.
        prior_root_level = logging.getLogger().level

        if self._hide_boto_debug:
            self.logger.info("Forcing all loggers to > DEBUG level.")
            logging.getLogger().setLevel(logging.INFO)

        try:
            yield None

        finally:
            if self._hide_boto_debug:
                self.logger.info("Restoring previous loggers settings.")
                logging.getLogger().setLevel(prior_root_level)
