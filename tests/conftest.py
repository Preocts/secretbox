"""Global fixtures"""
import os
import tempfile
from typing import Generator
from unittest.mock import patch

import pytest


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


@pytest.fixture
def mock_env_file() -> Generator[str, None, None]:
    """Builds and returns filename of a mock .env file"""
    try:
        file_desc, path = tempfile.mkstemp()
        with os.fdopen(file_desc, "w", encoding="utf-8") as temp_file:
            temp_file.write("\n".join(ENV_FILE_CONTENTS))
        yield path
    finally:
        os.remove(path)


@pytest.fixture(autouse=True)
def mask_aws_creds() -> Generator[None, None, None]:
    """Mask local AWS creds to avoid moto calling out"""
    with patch.dict(os.environ):
        for key in AWS_ENV_KEYS:
            os.environ[key] = "masked"
        yield None


@pytest.fixture
def remove_aws_creds() -> Generator[None, None, None]:
    """Removes AWS cresd from environment"""
    with patch.dict(os.environ):
        for key in AWS_ENV_KEYS:
            os.environ.pop(key, None)
        yield None
