"""Unit tests for aws secrect manager interactions"""
import json
import os
from typing import Dict
from typing import Generator

import pytest
from boto3.session import Session
from moto.secretsmanager import mock_secretsmanager
from mypy_boto3_secretsmanager.client import SecretsManagerClient
from secretbox.loadenv import LoadEnv

TEST_KEY_NAME = "TEST_KEY"
TEST_VALUE = "abcdefg"
TEST_STORE = "my_store"
TEST_REGION = "us-east-1"


@pytest.fixture(scope="function", name="mask_aws_creds")
def fixture_mask_aws_creds() -> Generator[Dict[str, str], None, None]:
    """Mask local AWS creds to avoid moto calling out"""
    restore = {
        "AWS_ACCESS_KEY": "",
        "AWS_SECRET_ACCESS_KEY": "",
        "AWS_SECURITY_TOKEN": "",
        "AWS_SESSION_TOKEN": "",
    }
    for key in restore.keys():
        restore[key] = os.getenv(key, "")
        os.environ[key] = "testing"

    yield restore

    for key, value in restore.items():
        os.environ[key] = value


@pytest.fixture(scope="function", name="remove_aws_creds")
def fixture_remove_aws_creds(
    mask_aws_creds: Dict[str, str]
) -> Generator[None, None, None]:
    """Removes AWS cresd from environment"""
    for key in mask_aws_creds.keys():
        del os.environ[key]
    yield None


@pytest.fixture(scope="function", name="secretsmanager")
def fixture_secretsmanager() -> Generator[SecretsManagerClient, None, None]:
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


@pytest.mark.usefixtures("remove_aws_creds")
def test_load_aws_no_credentials() -> None:
    """Cause a NoCredentialsError to be handled"""
    secretbox = LoadEnv(
        aws_sstore_name=TEST_STORE,
        aws_region=TEST_REGION,
    )
    assert not secretbox.loaded_values
    secretbox.load_aws_store()
    assert not secretbox.loaded_values


@pytest.mark.usefixtures("mask_aws_creds")
def test_load_aws_invalid_region() -> None:
    """Cause an InvalidRegionError to be handled"""
    secrets = LoadEnv(
        aws_sstore_name=TEST_STORE,
        aws_region="",
        auto_load=True,
    )
    assert secrets.get(TEST_KEY_NAME) == ""


@pytest.mark.usefixtures("mask_aws_creds", "secretsmanager")
def test_load_aws_secrets() -> None:
    """Load a secret from mocked AWS secret server"""
    secrets = LoadEnv(
        aws_sstore_name=TEST_STORE,
        aws_region=TEST_REGION,
    )

    assert not secrets.get(TEST_KEY_NAME)
    secrets.load_aws_store()
    assert secrets.get(TEST_KEY_NAME) == TEST_VALUE


@pytest.mark.usefixtures("mask_aws_creds", "secretsmanager")
def test_load_aws_secrets_client_error() -> None:
    """Load a secret that doesn't exist to handle ClientError"""
    secrets = LoadEnv(
        aws_sstore_name="some/secrect/store/that/is/not/there",
        aws_region=TEST_REGION,
    )

    assert not secrets.get(TEST_KEY_NAME)
    secrets.load_aws_store()
    assert not secrets.get(TEST_KEY_NAME)
