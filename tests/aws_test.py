"""Unit tests for aws secrect manager interactions"""
import importlib
import json
import os
import sys
from typing import Dict
from typing import Generator
from unittest.mock import patch

import pytest
from boto3.session import Session
from moto.secretsmanager import mock_secretsmanager
from mypy_boto3_secretsmanager.client import SecretsManagerClient
from secretbox import loadenv

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
    secretbox = loadenv.LoadEnv(
        aws_sstore_name=TEST_STORE,
        aws_region=TEST_REGION,
    )
    assert not secretbox.loaded_values
    secretbox.load_aws_store()
    assert not secretbox.loaded_values


@pytest.mark.parametrize(
    ("store", "region", "expected"),
    (
        (TEST_STORE, TEST_REGION, TEST_VALUE),
        (TEST_STORE, None, ""),
        (None, TEST_REGION, ""),
        (None, None, ""),
        ("store/not/found", TEST_REGION, ""),
        (TEST_STORE, "", ""),
    ),
)
@pytest.mark.usefixtures("mask_aws_creds", "secretsmanager")
def test_load_aws_secrets(store: str, region: str, expected: str) -> None:
    """Load a secret from mocked AWS secret server"""
    # Dirty restore as testing target has side-effects in os.environ
    if TEST_KEY_NAME in os.environ:
        os.environ.pop(TEST_KEY_NAME)

    secrets = loadenv.LoadEnv(
        aws_sstore_name=store,
        aws_region=region,
    )

    assert not secrets.get(TEST_KEY_NAME)
    secrets.load()
    assert secrets.get(TEST_KEY_NAME) == expected


def test_boto3_not_installed_load_aws() -> None:
    """Stop and raise if manual load_aws_store() is called without boto3"""
    secrets = loadenv.LoadEnv(aws_sstore_name=TEST_STORE, aws_region=TEST_REGION)
    with patch.object(loadenv, "boto3", None):
        with pytest.raises(NotImplementedError):
            secrets.load_aws_store()


def test_boto3_not_installed_auto_load() -> None:
    """Silently skip loading AWS secrets manager if no boto3"""
    secrets = loadenv.LoadEnv(aws_sstore_name=TEST_STORE, aws_region=TEST_REGION)
    with patch.object(loadenv, "boto3", None):
        assert secrets.loaded_values == {}
        # TODO: This is dangerous as we are assuming something will load
        secrets.load()
        assert secrets.loaded_values


def test_boto3_missing_import_catch() -> None:
    """Reload loadenv without boto3"""
    with patch.dict(sys.modules, {"boto3": None}):
        importlib.reload(loadenv)
        assert loadenv.boto3 is None
