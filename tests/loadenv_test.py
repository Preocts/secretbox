"""Unit tests against loadenv.py"""
import os
from unittest.mock import patch

from secretbox.loadenv import LoadEnv

from tests.conftest import ENV_FILE_EXPECTED


def test_load_env_file(mock_env_file: str, secretbox: LoadEnv) -> None:
    """Load and confirm expected values"""
    secretbox.filename = mock_env_file
    secretbox.load()
    for key, value in ENV_FILE_EXPECTED.items():
        assert secretbox.get(key) == value, f"Expected: {key}, {value}"


def test_load_env_vars(secretbox: LoadEnv) -> None:
    """Load and confirm values from environ"""
    with patch.dict(os.environ, ENV_FILE_EXPECTED):
        secretbox.load()
        for key, value in ENV_FILE_EXPECTED.items():
            assert secretbox.get(key) == value, f"Expected: {key}, {value}"


def test_load_order_file_over_environ(secretbox: LoadEnv, mock_env_file: str) -> None:
    """Loaded file should override existing environ values"""
    secretbox.filename = mock_env_file
    altered_expected = {key: f"{value} ALT" for key, value in ENV_FILE_EXPECTED.items()}
    with patch.dict(os.environ, altered_expected):
        secretbox.load()
        for key, value in ENV_FILE_EXPECTED.items():
            assert secretbox.get(key) == value, f"Expected: {key}, {value}"


def test_load_missing_file(secretbox: LoadEnv) -> None:
    """Confirm clean run if file is missing"""
    secretbox.filename = "BYWHATCHANCEWOULDTHISSEXIST.DERP"
    result = secretbox.load_env_file()
    assert not result


def test_autoload_tempfile(mock_env_file: str) -> None:
    """One less line of code needed"""
    secretbox = LoadEnv(filename=mock_env_file, auto_load=True)
    for key, value in ENV_FILE_EXPECTED.items():
        assert secretbox.get(key) == value


def test_missing_key_is_empty(secretbox: LoadEnv) -> None:
    """Missing key? Check behind the milk"""
    assert secretbox.get("BYWHATCHANCEWOULDTHISSEXIST") == ""
