"""Global fixtures"""
import json
import os
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

AWS_ENV_KEYS = [
    "AWS_ACCESS_KEY",
    "AWS_SECRET_ACCESS_KEY",
    "AWS_SECURITY_TOKEN",
    "AWS_SESSION_TOKEN",
]


@pytest.fixture(scope="function", name="secretbox")
def fixture_secretbox() -> Generator[loadenv.LoadEnv, None, None]:
    """Default instance of LoadEnv"""
    yield loadenv.LoadEnv()


@pytest.fixture(scope="function", name="secretbox_aws")
def fixture_secretbox_aws() -> Generator[loadenv.LoadEnv, None, None]:
    """Default instance of LoadEnv"""
    yield loadenv.LoadEnv(aws_region=TEST_REGION, aws_sstore_name=TEST_STORE)


@pytest.fixture(scope="function", name="mask_aws_creds")
def fixture_mask_aws_creds() -> Generator[None, None, None]:
    """Mask local AWS creds to avoid moto calling out"""
    with patch.dict(os.environ):
        for key in AWS_ENV_KEYS:
            os.environ[key] = "masked"
        yield None


@pytest.fixture(scope="function", name="remove_aws_creds")
def fixture_remove_aws_creds() -> Generator[None, None, None]:
    """Removes AWS cresd from environment"""
    with patch.dict(os.environ):
        for key in AWS_ENV_KEYS:
            os.environ.pop(key, None)
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
