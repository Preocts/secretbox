"""Unit tests for aws secrect manager interactions"""
import importlib
import json
import sys
from typing import Any
from typing import Generator
from unittest.mock import patch

import pytest
from boto3.session import Session
from moto.secretsmanager import mock_secretsmanager
from mypy_boto3_secretsmanager.client import SecretsManagerClient
from secretbox import awssecret_loader as awssecret_loader_module
from secretbox.awssecret_loader import AWSSecretLoader

TEST_KEY_NAME = "TEST_KEY"
TEST_VALUE = "abcdefg"
TEST_STORE = "my_store"
TEST_REGION = "us-east-1"


@pytest.fixture
def secretsmanager() -> Generator[SecretsManagerClient, None, None]:
    """Populate mock secretsmanager with TEST_SECRET_KEY in us-east-1"""
    secret_values = json.dumps({TEST_KEY_NAME: TEST_VALUE})

    with mock_secretsmanager():
        session = Session()
        client = session.client(
            service_name="secretsmanager",
            region_name=TEST_REGION,
        )
        client.create_secret(Name=TEST_STORE, SecretString=secret_values)

        yield client


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
    expected: Any,
) -> None:
    """Load a secret from mocked AWS secret server"""
    assert not awssecret_loader.loaded_values.get(TEST_KEY_NAME)
    awssecret_loader.load_values(aws_sstore_name=store, aws_region_name=region)
    assert awssecret_loader.loaded_values.get(TEST_KEY_NAME) == expected


@pytest.mark.usefixtures("mask_aws_creds", "secretsmanager")
def test_boto3_not_installed_auto_load(awssecret_loader: AWSSecretLoader) -> None:
    """Skip loading AWS secrets manager if no boto3"""
    with patch.object(awssecret_loader_module, "boto3", None):
        assert not awssecret_loader.loaded_values
        awssecret_loader.load_values(
            aws_sstore_name=TEST_STORE,
            aws_region_name=TEST_REGION,
        )
        assert not awssecret_loader.loaded_values


@pytest.mark.usefixtures("mask_aws_creds", "secretsmanager")
def test_boto3_stubs_not_installed(awssecret_loader: AWSSecretLoader) -> None:
    """Continue loading AWS secrets manager without boto3-stubs"""
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
