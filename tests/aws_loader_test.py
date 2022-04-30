"""Unit tests for aws loader"""
import logging
import os
from typing import Any
from typing import Generator
from unittest.mock import patch

import pytest
from secretbox.aws_loader import AWSLoader


@pytest.fixture
def awsloader() -> Generator[AWSLoader, None, None]:
    """Create a fixture to test with"""
    loader = AWSLoader()
    assert not loader.loaded_values
    yield loader


def test_populate_region_store_names_none(awsloader: AWSLoader) -> None:
    """Nothing provided"""
    with patch.dict(os.environ):
        os.environ.pop("AWS_SSTORE_NAME", None)
        os.environ.pop("AWS_REGION_NAME", None)
        awsloader.populate_region_store_names()
        assert awsloader.aws_sstore is None
        assert awsloader.aws_region is None


def test_populate_region_store_names_os(awsloader: AWSLoader) -> None:
    """values in environ"""
    with patch.dict(os.environ):
        os.environ["AWS_SSTORE_NAME"] = "MockStore"
        os.environ["AWS_REGION_NAME"] = "MockRegion"
        awsloader.populate_region_store_names()
        assert awsloader.aws_sstore == "MockStore"
        assert awsloader.aws_region == "MockRegion"


def test_populate_region_store_names_kw(awsloader: AWSLoader) -> None:
    """values in environ but keywords given"""
    with patch.dict(os.environ):
        os.environ["AWS_SSTORE_NAME"] = "MockStore"
        os.environ["AWS_REGION_NAME"] = "MockRegion"
        awsloader.populate_region_store_names(
            aws_sstore_name="NewStore",
            aws_region_name="NewRegion",
        )
        assert awsloader.aws_sstore == "NewStore"
        assert awsloader.aws_region == "NewRegion"


def test_filter_boto_debug(caplog: Any, awsloader: AWSLoader) -> None:
    try:
        logger = logging.getLogger("secrets")
        logger.setLevel("DEBUG")
        error_logger = logging.getLogger("errors")
        error_logger.setLevel("ERROR")
        current_level = logger.root.level
        # logger.root.setLevel("DEBUG")

        with awsloader.disable_debug_logging():
            logger.debug("OHNO")
            logger.info("ALLGOOD")

    finally:
        logger.root.level = current_level

    assert "OHNO" not in caplog.text
    assert "ALLGOOD" in caplog.text
    assert logger.level == logging.DEBUG
    assert error_logger.level == logging.ERROR


def test_filter_boto_debug_no_action(caplog: Any, awsloader: AWSLoader) -> None:
    logger = logging.getLogger("secrets")

    with awsloader.disable_debug_logging():
        logger.debug("OHNO")
        logger.error("ALLGOOD")

    assert "OHNO" not in caplog.text
    assert "ALLGOOD" in caplog.text


def test_filter_boto_debug_disabled(caplog: Any, awsloader: AWSLoader) -> None:
    try:
        logger = logging.getLogger("secrets")
        current_level = logger.root.level
        logger.root.setLevel("DEBUG")
        awsloader.hide_boto_debug = False

        with awsloader.disable_debug_logging():
            logger.debug("DEBUG")
            logger.info("INFO")

    finally:
        logger.root.level = current_level

    assert "DEBUG" in caplog.text
    assert "INFO" in caplog.text


def test_log_aws_error_with_nonaws_error(awsloader: AWSLoader, caplog: Any) -> None:
    try:
        raise Exception("Manufactored exception")
    except Exception as err:
        awsloader.log_aws_error(err)
    assert "Manufactored exception" in caplog.text
