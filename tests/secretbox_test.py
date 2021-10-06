"""Unit tests against secretbox.py"""
import os
from typing import Any
from unittest.mock import patch

from secretbox import SecretBox

from tests.conftest import ENV_FILE_EXPECTED


def test_load_env_file(mock_env_file: str, secretbox: SecretBox) -> None:
    """Load and confirm expected values"""
    secretbox.filename = mock_env_file
    secretbox.load()
    for key, value in ENV_FILE_EXPECTED.items():
        assert secretbox.get(key) == value, f"Expected: {key}, {value}"


def test_load_env_vars(secretbox: SecretBox) -> None:
    """Load and confirm values from environ"""
    with patch.dict(os.environ, ENV_FILE_EXPECTED):
        secretbox.load()
        for key, value in ENV_FILE_EXPECTED.items():
            assert secretbox.get(key) == value, f"Expected: {key}, {value}"


def test_load_order_file_over_environ(secretbox: SecretBox, mock_env_file: str) -> None:
    """Loaded file should override existing environ values"""
    secretbox.filename = mock_env_file
    altered_expected = {key: f"{value} ALT" for key, value in ENV_FILE_EXPECTED.items()}
    with patch.dict(os.environ, altered_expected):
        secretbox.load()
        for key, value in ENV_FILE_EXPECTED.items():
            assert secretbox.get(key) == value, f"Expected: {key}, {value}"


def test_load_missing_file(secretbox: SecretBox) -> None:
    """Confirm clean run if file is missing"""
    secretbox.filename = "BYWHATCHANCEWOULDTHISSEXIST.DERP"
    secretbox.load_env_file()


def test_autoload_tempfile(mock_env_file: str) -> None:
    """One less line of code needed"""
    secretbox = SecretBox(filename=mock_env_file, auto_load=True)
    for key, value in ENV_FILE_EXPECTED.items():
        assert secretbox.get(key) == value


def test_missing_key_is_empty(secretbox: SecretBox) -> None:
    """Missing key? Check behind the milk"""
    assert secretbox.get("BYWHATCHANCEWOULDTHISSEXIST") == ""


def test_default_missing_key(secretbox: SecretBox) -> None:
    """Missing key? Return the provided default instead"""
    assert secretbox.get("BYWHATCHANCEWOULDTHISSEXIST", "Hello") == "Hello"


def test_load_debug_flag(caplog: Any) -> None:
    """Ensure logging is silentish"""
    _ = SecretBox()

    assert "Debug flag passed." not in caplog.text

    _ = SecretBox(debug_flag=True)

    assert "Debug flag passed." in caplog.text
