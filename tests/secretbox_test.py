"""Unit tests against secretbox.py"""
import os
from typing import Any
from unittest.mock import patch

from secretbox import SecretBox

from tests.conftest import ENV_FILE_EXPECTED


def test_load_from_with_unknown(secretbox: SecretBox, mock_env_file: str) -> None:
    """Load secrets, throw an unknown loader in to ensure clean fall-through"""
    assert not secretbox.loaded_values
    secretbox.load_from(["envfile", "unknown"], filename=mock_env_file)
    assert secretbox.loaded_values


def test_load_order_file_over_environ(secretbox: SecretBox, mock_env_file: str) -> None:
    """Loaded file should override existing environ values"""
    altered_expected = {key: f"{value} ALT" for key, value in ENV_FILE_EXPECTED.items()}
    with patch.dict(os.environ, altered_expected):
        secretbox.load_from(["environ", "envfile"], filename=mock_env_file)
        for key, value in ENV_FILE_EXPECTED.items():
            assert secretbox.get(key) == value, f"Expected: {key}, {value}"


def test_load_order_environ_over_file(secretbox: SecretBox, mock_env_file: str) -> None:
    """Loaded environ should override file values"""
    altered_expected = {key: f"{value} ALT" for key, value in ENV_FILE_EXPECTED.items()}
    with patch.dict(os.environ, altered_expected):
        secretbox.load_from(["envfile", "environ"], filename=mock_env_file)
        for key, value in ENV_FILE_EXPECTED.items():
            assert secretbox.get(key) == f"{value} ALT", f"Expected: {key}, {value} ALT"


def test_update_loaded_values(secretbox: SecretBox) -> None:
    """Ensure we are updating state correctly"""
    secretbox._update_loaded_values({"TEST": "TEST01"})
    assert secretbox.get("TEST") == "TEST01"

    secretbox._update_loaded_values({"TEST": "TEST02"})
    assert secretbox.get("TEST") == "TEST02"


def test_join_kwarg_defaults(secretbox: SecretBox) -> None:
    """Mutables are fun, this should never create side-effects"""
    secretbox.kwarg_defaults = {"TEST": "TEST01"}
    new_kwargs = {"TEST": "TEST02"}
    final_kwargs = secretbox._join_kwarg_defaults(new_kwargs)
    assert secretbox.kwarg_defaults == {"TEST": "TEST01"}
    assert new_kwargs == {"TEST": "TEST02"}
    assert final_kwargs == new_kwargs


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
