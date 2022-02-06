"""Unit tests for aws loader"""
import importlib
import logging
import os
import sys
from typing import Any
from typing import Generator
from unittest.mock import patch

import pytest
from secretbox import aws_loader as loader_module
from secretbox.aws_loader import AWSLoader


@pytest.fixture
def awsloader() -> Generator[AWSLoader, None, None]:
    """Create a fixture to test with"""
    loader = AWSLoader()
    assert not loader.loaded_values
    yield loader


@pytest.fixture
def noboto() -> Generator[None, None, None]:
    """Dirty module to remove botocore and assert import catches"""
    with patch.dict(sys.modules, {"botocore.awsrequest": None}):
        importlib.reload(loader_module)
        yield None
    importlib.reload(loader_module)


@pytest.mark.usefixtures("noboto")
def test_catch_botocore_missing_import_on_module_load() -> None:
    assert issubclass(loader_module.HeadersDict, dict)


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


def test_secret_filter(caplog: Any) -> None:
    logger = logging.getLogger("secrets")
    logger.addFilter(AWSLoader.secrets_filter)
    logger.setLevel("DEBUG")
    secret_dict = {"allYour": "Passwords"}
    secret_tuple = ("I am a plain-text secrets",)
    secret_string = "Your password is 12345"

    logger.debug("Reponse body: %s", secret_dict)
    logger.debug("Reponse body: %s", secret_tuple)
    logger.debug("Reponse body: %s", secret_string)
    logger.debug("Response body:")
    logger.debug("Standard log")

    logger.info("Safe Info")

    assert "Passwords" not in caplog.text
    assert "plain-text" not in caplog.text
    assert "12345" not in caplog.text
    assert "Standard log" in caplog.text
    assert "Safe Info" in caplog.text


def test_log_aws_error_with_nonaws_error(awsloader: AWSLoader, caplog: Any) -> None:
    try:
        raise Exception("Manufactored exception")
    except Exception as err:
        awsloader.log_aws_error(err)
    assert "Manufactored exception" in caplog.text
