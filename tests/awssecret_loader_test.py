"""Unit tests for aws secrect manager interactions"""
import importlib
import logging
import os
import sys
from typing import Any
from typing import Generator
from unittest.mock import patch

import pytest
from secretbox import awssecret_loader as awssecret_loader_module
from secretbox.awssecret_loader import AWSSecretLoader

from tests.conftest import TEST_KEY_NAME
from tests.conftest import TEST_REGION
from tests.conftest import TEST_STORE
from tests.conftest import TEST_VALUE


@pytest.fixture
def awssecret_loader() -> Generator[AWSSecretLoader, None, None]:
    """Create a fixture to test with"""
    loader = AWSSecretLoader()
    assert not loader.loaded_values
    yield loader


@pytest.mark.usefixtures("remove_aws_creds")
def test_load_aws_no_credentials(awssecret_loader: AWSSecretLoader) -> None:
    """Cause a NoCredentialsError to be handled"""
    assert not awssecret_loader.loaded_values
    awssecret_loader.load_values(
        aws_sstore_name=TEST_STORE,
        aws_region_name=TEST_REGION,
    )
    assert not awssecret_loader.loaded_values


@pytest.mark.parametrize(
    ("store", "region", "expected"),
    (
        (TEST_STORE, TEST_REGION, TEST_VALUE),
        (TEST_STORE, None, None),
        (None, TEST_REGION, None),
        (None, None, None),
        ("store/not/found", TEST_REGION, None),
        (TEST_STORE, "", None),
    ),
)
@pytest.mark.usefixtures("mask_aws_creds", "secretsmanager")
def test_load_aws_secrets(
    awssecret_loader: AWSSecretLoader,
    store: str,
    region: str,
    expected: str,
) -> None:
    """Load a secret from mocked AWS secret server"""
    assert not awssecret_loader.loaded_values.get(TEST_KEY_NAME)
    awssecret_loader.load_values(aws_sstore_name=store, aws_region_name=region)
    assert awssecret_loader.loaded_values.get(TEST_KEY_NAME) == expected


@pytest.mark.usefixtures("mask_aws_creds", "secretsmanager")
def test_boto3_not_installed_auto_load(awssecret_loader: AWSSecretLoader) -> None:
    """Silently skip loading AWS secrets manager if no boto3"""
    with patch.object(awssecret_loader_module, "boto3", None):
        assert not awssecret_loader.loaded_values
        awssecret_loader.load_values(aws_sstore=TEST_STORE, aws_region=TEST_REGION)
        assert not awssecret_loader.loaded_values


def test_boto3_missing_import_catch() -> None:
    """Reload loadenv without boto3"""
    with patch.dict(sys.modules, {"boto3": None}):
        importlib.reload(awssecret_loader_module)
        assert awssecret_loader_module.boto3 is None
    # Reload after test to avoid polution
    importlib.reload(awssecret_loader_module)


def test_populate_region_store_names_none(awssecret_loader: AWSSecretLoader) -> None:
    """Nothing provided"""
    with patch.dict(os.environ):
        os.environ.pop("AWS_SSTORE_NAME", None)
        os.environ.pop("AWS_REGION_NAME", None)
        awssecret_loader.populate_region_store_names()
        assert awssecret_loader.aws_sstore is None
        assert awssecret_loader.aws_region is None


def test_populate_region_store_names_os(awssecret_loader: AWSSecretLoader) -> None:
    """values in environ"""
    with patch.dict(os.environ):
        os.environ["AWS_SSTORE_NAME"] = "MockStore"
        os.environ["AWS_REGION_NAME"] = "MockRegion"
        awssecret_loader.populate_region_store_names()
        assert awssecret_loader.aws_sstore == "MockStore"
        assert awssecret_loader.aws_region == "MockRegion"


def test_populate_region_store_names_kw(awssecret_loader: AWSSecretLoader) -> None:
    """values in environ but keywords given"""
    with patch.dict(os.environ):
        os.environ["AWS_SSTORE_NAME"] = "MockStore"
        os.environ["AWS_REGION_NAME"] = "MockRegion"
        awssecret_loader.populate_region_store_names(
            aws_sstore_name="NewStore",
            aws_region_name="NewRegion",
        )
        assert awssecret_loader.aws_sstore == "NewStore"
        assert awssecret_loader.aws_region == "NewRegion"


def test_secret_filter(caplog: Any) -> None:
    logger = logging.getLogger("secrets")
    logger.addFilter(AWSSecretLoader.secrets_filter)
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
