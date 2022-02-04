"""Unit tests for aws secrect manager interactions"""
from typing import Any
from typing import Generator
from unittest.mock import patch

import pytest
from secretbox import awssecret_loader as awssecret_loader_module
from secretbox.awssecret_loader import AWSSecretLoader

TEST_KEY_NAME = "TEST_KEY"
TEST_VALUE = "abcdefg"
TEST_STORE = "my_store"
TEST_STORE_INVALID = "store_not_found"
TEST_REGION = "us-east-1"


@pytest.fixture
def awssecret_loader() -> Generator[AWSSecretLoader, None, None]:
    """Create a fixture to test with"""
    loader = AWSSecretLoader()
    assert not loader.loaded_values
    yield loader


@pytest.mark.usefixtures("remove_aws_creds")
def test_load_aws_no_credentials(awssecret_loader: AWSSecretLoader) -> None:
    """Cause a NoCredentialsError to be handled"""
    awssecret_loader.load_values(
        aws_sstore_name=TEST_STORE,
        aws_region_name=TEST_REGION,
    )
    assert not awssecret_loader.loaded_values


@pytest.mark.usefixtures("remove_aws_creds")
def test_load_aws_no_secret_store_defined(awssecret_loader: AWSSecretLoader) -> None:
    awssecret_loader.load_values(
        aws_sstore_name=None,
        aws_region_name=TEST_REGION,
    )
    assert not awssecret_loader.loaded_values


@pytest.mark.usefixtures("remove_aws_creds")
def test_get_client_without_region(
    awssecret_loader: AWSSecretLoader,
    caplog: Any,
) -> None:
    awssecret_loader.aws_region = None
    result = awssecret_loader.get_aws_client()
    assert result is None
    assert "No valid AWS region" in caplog.text


def test_boto3_not_installed_auto_load(awssecret_loader: AWSSecretLoader) -> None:
    """Skip loading AWS secrets manager if no boto3"""
    with patch.object(awssecret_loader_module, "boto3", None):
        assert not awssecret_loader.loaded_values
        awssecret_loader.load_values(
            aws_sstore_name=TEST_STORE,
            aws_region_name=TEST_REGION,
        )
        assert not awssecret_loader.loaded_values
