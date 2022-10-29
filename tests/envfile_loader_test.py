"""Unit tests for .env file loader"""
# import os
from __future__ import annotations

from collections.abc import Generator

import pytest
from secretbox.envfile_loader import EnvFileLoader

from tests.conftest import ENV_FILE_EXPECTED


@pytest.fixture
def envfile_loader() -> Generator[EnvFileLoader, None, None]:
    """Create us a fixture"""
    loader = EnvFileLoader()
    assert not loader.values
    yield loader


def test_load_env_file(mock_env_file: str, envfile_loader: EnvFileLoader) -> None:
    """Load and confirm expected values"""
    envfile_loader._load_values(filename=mock_env_file)
    for key, value in ENV_FILE_EXPECTED.items():
        assert envfile_loader.values.get(key) == value, f"{key}, {value}"


def test_load_missing_file(envfile_loader: EnvFileLoader) -> None:
    """Confirm clean run if file is missing"""
    result = envfile_loader._load_values(filename="BYWHATCHANGEWOULDTHISSEXIST")
    assert not result


def test_run_loads_environ(mock_env_file: str, envfile_loader: EnvFileLoader) -> None:
    envfile_loader._filename = mock_env_file
    envfile_loader.run()
    for key, value in ENV_FILE_EXPECTED.items():
        assert envfile_loader._loaded_values[key] == value, f"{key}, {value}"
        # assert os.getenv(key) == value, f"{key}, {value}"
