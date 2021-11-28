"""Global fixtures"""
import json
import os
import tempfile
from typing import Generator
from unittest.mock import patch

import pytest
from boto3.session import Session
from moto.secretsmanager import mock_secretsmanager
from mypy_boto3_secretsmanager.client import SecretsManagerClient
from secretbox.envfile_loader import EnvFileLoader
from secretbox.environ_loader import EnvironLoader
from secretbox.secretbox import SecretBox

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

ENV_FILE_CONTENTS = [
    "SECRETBOX_TEST_PROJECT_ENVIRONMENT=sandbox",
    "#What type of .env supports comments?",
    "",
    "BROKEN KEY",
    "VALID==",
    "SUPER_SECRET  =          12345",
    "PASSWORD = correct horse battery staple",
    'USER_NAME="not_admin"',
    "MESSAGE = '    Totally not an \"admin\" account logging in'",
    "  SINGLE_QUOTES = 'test'",
    "export NESTED_QUOTES = \"'Double your quotes, double your fun'\"",
    '   eXport SHELL_COMPATIBLE = "well, that happened"',
]

ENV_FILE_EXPECTED = {
    "SECRETBOX_TEST_PROJECT_ENVIRONMENT": "sandbox",
    "VALID": "=",
    "SUPER_SECRET": "12345",
    "PASSWORD": "correct horse battery staple",
    "USER_NAME": "not_admin",
    "MESSAGE": '    Totally not an "admin" account logging in',
    "SINGLE_QUOTES": "test",
    "NESTED_QUOTES": "'Double your quotes, double your fun'",
    "SHELL_COMPATIBLE": "well, that happened",
}

##############################################################################
# Base fixtures
##############################################################################


@pytest.fixture(scope="function", name="envfile_loader")
def fixtures_envfile_loader() -> Generator[EnvFileLoader, None, None]:
    """Create us a fixture"""
    loader = EnvFileLoader()
    assert not loader.loaded_values
    yield loader


@pytest.fixture(scope="function", name="environ_loader")
def fixture_environ_loader() -> Generator[EnvironLoader, None, None]:
    """A fixture because this is what we do"""
    loader = EnvironLoader()
    assert not loader.loaded_values
    yield loader


@pytest.fixture(scope="function", name="secretbox")
def fixture_secretbox() -> Generator[SecretBox, None, None]:
    """Default instance of LoadEnv"""
    secrets = SecretBox()
    assert not secrets.loaded_values
    yield secrets


##############################################################################
# Mocking .env file loading
##############################################################################


@pytest.fixture(scope="function", name="mock_env_file")
def fixture_mock_env_file() -> Generator[str, None, None]:
    """Builds and returns filename of a mock .env file"""
    try:
        file_desc, path = tempfile.mkstemp()
        with os.fdopen(file_desc, "w", encoding="utf-8") as temp_file:
            temp_file.write("\n".join(ENV_FILE_CONTENTS))
        yield path
    finally:
        os.remove(path)


##############################################################################
# AWS Fixtures
##############################################################################


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
