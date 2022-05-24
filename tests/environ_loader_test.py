"""Simple test to ensure we read environ"""
import os
from typing import Generator
from unittest.mock import patch

import pytest
from secretbox.environ_loader import EnvironLoader

MOCK_ENV = {
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
def environ_loader() -> Generator[EnvironLoader, None, None]:
    """A fixture because this is what we do"""
    loader = EnvironLoader()
    assert not loader._loaded_values
    yield loader


def test_load_env_vars(environ_loader: EnvironLoader) -> None:
    """Load and confirm values from environ"""
    with patch.dict(os.environ, MOCK_ENV):
        environ_loader.load_values()
        for key, value in MOCK_ENV.items():
            assert environ_loader._loaded_values.get(key) == value, f"{key}, {value}"


def test_run_load_values(environ_loader: EnvironLoader) -> None:
    with patch.dict(os.environ, MOCK_ENV):
        environ_loader.run()
        for key, value in MOCK_ENV.items():
            assert environ_loader._loaded_values.get(key) == value, f"{key}, {value}"
