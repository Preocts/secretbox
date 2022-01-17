"""Unit tests for aws secrect manager interactions"""
import importlib
import json
import sys
from datetime import datetime
from typing import Any
from typing import Generator
from unittest.mock import patch

import botocore.client
import botocore.session
import pytest
from botocore.client import BaseClient
from botocore.stub import Stubber
from secretbox import awssecret_loader as awssecret_loader_module
from secretbox.awssecret_loader import AWSSecretLoader

TEST_KEY_NAME = "TEST_KEY"
TEST_VALUE = "abcdefg"
TEST_STORE = "my_store"
TEST_STORE_INVALID = "store_not_found"
TEST_REGION = "us-east-1"


@pytest.fixture
def mockclient() -> Generator[BaseClient, None, None]:
    """
    Mocks `get_secret_value` for AWS client.

    Has two responses in order:
        - Valid response for SecretId=TEST_STORE
        - ClientError response for SecretId=TEST_STORE_INVALID

    """
    secret_values = json.dumps({TEST_KEY_NAME: TEST_VALUE})

    # Create our mock secretstore response
    valid_response = {
        "ARN": f"arn:aws:secretsmanager:{TEST_REGION}:123456789012:{TEST_STORE}",
        "Name": TEST_STORE,
        "VersionId": "12345678901234567890123456789012",
        "SecretBinary": b"",
        "SecretString": secret_values,
        "VersionStages": ["mock_stage"],
        "CreatedDate": datetime(2021, 1, 17),
    }

    # Create mock secretstore session
    session = botocore.session.get_session().create_client(
        service_name="secretsmanager",
        region_name=TEST_REGION,
    )

    with Stubber(session) as stubber:
        stubber.add_response(
            method="get_secret_value",
            service_response=valid_response,
            expected_params={"SecretId": TEST_STORE},
        )
        stubber.add_client_error(
            method="get_secret_value",
            service_error_code="ResourceNotFoundException",
            service_message="Mock secret not found",
            http_status_code=404,
            expected_params={"SecretId": TEST_STORE_INVALID},
        )
        yield session


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


def test_load_aws_client_no_region(
    awssecret_loader: AWSSecretLoader,
    caplog: Any,
) -> None:
    with patch.object(awssecret_loader, "get_aws_client", return_value=None):
        assert not awssecret_loader.load_values(
            aws_sstore_name=TEST_STORE,
            aws_region_name=TEST_REGION,
        )
    assert "Invalid secrets manager client" in caplog.text


@pytest.mark.usefixtures("remove_aws_creds")
def test_get_client_without_region(
    awssecret_loader: AWSSecretLoader,
    caplog: Any,
) -> None:
    awssecret_loader.aws_region = None
    result = awssecret_loader.get_aws_client()
    assert result is None
    assert "No valid AWS region" in caplog.text


def test_load_aws_secrets_valid_store_and_invalid_store(
    awssecret_loader: AWSSecretLoader,
    mockclient: BaseClient,
) -> None:
    """Load a secret from mocked AWS secret server"""
    with patch.object(awssecret_loader, "get_aws_client", return_value=mockclient):

        # Test valid response
        awssecret_loader.load_values(
            aws_sstore_name=TEST_STORE,
            aws_region_name=TEST_REGION,
        )
        assert awssecret_loader.loaded_values.get(TEST_KEY_NAME) == TEST_VALUE

        # Reset and test invalid response
        awssecret_loader.loaded_values = {}
        awssecret_loader.load_values(
            aws_sstore_name=TEST_STORE_INVALID,
            aws_region_name=TEST_REGION,
        )
        assert awssecret_loader.loaded_values.get(TEST_KEY_NAME) is None


def test_boto3_not_installed_auto_load(awssecret_loader: AWSSecretLoader) -> None:
    """Skip loading AWS secrets manager if no boto3"""
    with patch.object(awssecret_loader_module, "boto3", None):
        assert not awssecret_loader.loaded_values
        awssecret_loader.load_values(
            aws_sstore_name=TEST_STORE,
            aws_region_name=TEST_REGION,
        )
        assert not awssecret_loader.loaded_values


def test_boto3_stubs_not_installed(
    awssecret_loader: AWSSecretLoader,
    mockclient: BaseClient,
) -> None:
    """Continue loading AWS secrets manager without boto3-stubs"""
    with patch.object(awssecret_loader, "get_aws_client", return_value=mockclient):
        with patch.object(awssecret_loader_module, "SecretsManagerClient", None):
            assert not awssecret_loader.loaded_values
            awssecret_loader.load_values(
                aws_sstore_name=TEST_STORE,
                aws_region_name=TEST_REGION,
            )
            assert awssecret_loader.loaded_values


def test_boto3_missing_import_catch() -> None:
    with patch.dict(sys.modules, {"boto3": None}):
        importlib.reload(awssecret_loader_module)
        assert awssecret_loader_module.boto3 is None
    # Reload after test to avoid polution
    importlib.reload(awssecret_loader_module)


def test_boto3_stubs_missing_import_catch() -> None:
    with patch.dict(sys.modules, {"mypy_boto3_secretsmanager.client": None}):
        importlib.reload(awssecret_loader_module)
        assert awssecret_loader_module.SecretsManagerClient is None
    # Reload after test to avoid polution
    importlib.reload(awssecret_loader_module)
