"""Unit tests for .env file loader"""
from secretbox.envfile_loader import EnvFileLoader

from tests.conftest import ENV_FILE_EXPECTED


def test_load_env_file(mock_env_file: str, envfile_loader: EnvFileLoader) -> None:
    """Load and confirm expected values"""
    envfile_loader.load_values(filename=mock_env_file)
    for key, value in ENV_FILE_EXPECTED.items():
        assert envfile_loader.loaded_values.get(key) == value, f"{key}, {value}"


def test_load_missing_file(envfile_loader: EnvFileLoader) -> None:
    """Confirm clean run if file is missing"""
    result = envfile_loader.load_values(filename="BYWHATCHANGEWOULDTHISSEXIST")
    assert not result