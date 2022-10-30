"""Unit tests for aws loader"""
from __future__ import annotations

import logging
import os
from collections.abc import Generator
from typing import Any
from unittest.mock import patch

import pytest
from secretbox.aws_loader import AWSLoader
from secretbox.exceptions import LoaderException


@pytest.fixture
def awsloader() -> Generator[AWSLoader, None, None]:
    """Create a fixture to test with"""
    loader = AWSLoader()
    yield loader


def test_run_raises_with_flag(awsloader: AWSLoader) -> None:
    awsloader._capture_exceptions = False
    with patch.object(awsloader, "_run", side_effect=Exception) as run:

        with pytest.raises(LoaderException):
            awsloader.run()

    assert run.call_count == 1


def test_run_does_not_rause_with_flag(awsloader: AWSLoader) -> None:
    awsloader._capture_exceptions = True
    with patch.object(awsloader, "_run", side_effect=Exception) as run:

        result = awsloader.run()

    assert run.call_count == 1
    assert result is False


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
    prior_root_level = logging.getLogger().level
    logging.getLogger().setLevel("DEBUG")

    try:
        logger = logging.getLogger("secrets")

        logging.getLogger().debug("Baseline Start")
        with awsloader.disable_debug_logging():
            logger.debug("OHNO")
            logger.info("ALLGOOD")
        logging.getLogger().debug("Baseline End")

    finally:
        logging.getLogger().setLevel(prior_root_level)

    assert "Baseline Start" in caplog.text
    assert "Baseline End" in caplog.text
    assert "OHNO" not in caplog.text
    assert "ALLGOOD" in caplog.text


def test_filter_boto_debug_no_action(caplog: Any, awsloader: AWSLoader) -> None:
    logger = logging.getLogger("debug_enabled")

    with awsloader.disable_debug_logging():
        logger.debug("OHNO")
        logger.error("ALLGOOD")

    assert "OHNO" not in caplog.text
    assert "ALLGOOD" in caplog.text


def test_filter_boto_debug_disabled(caplog: Any, awsloader: AWSLoader) -> None:
    try:
        logger = logging.getLogger("debug_disabled")
        current_level = logger.root.level
        logger.root.setLevel("DEBUG")
        awsloader._hide_boto_debug = False

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
