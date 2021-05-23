"""Unit tests against loadenv.py"""
import os
import tempfile
from typing import Generator
from typing import List

import pytest
from secretbox.loadenv import LoadEnv


@pytest.fixture(scope="function", name="mock_env")
def fixture_mock_env() -> Generator[str, None, None]:
    """Builds and returns filename of a mock .env file"""
    env_contents: List[str] = [
        "SECRETBOX_TEST_PROJECT_ENVIRONMENT=sandbox",
        "#What type of .env supports comments?",
        "",
        "BROKEN KEY",
        "VALID==",
        "SUPER_SECRET  =          12345",
    ]
    try:
        file_desc, path = tempfile.mkstemp()
        with os.fdopen(file_desc, "w", encoding="utf-8") as temp_file:
            temp_file.write("\n".join(env_contents))
        yield path
    finally:
        os.remove(path)


def test_tempfile_exists(mock_env: str) -> None:
    """Sanity check"""
    assert os.path.isfile(mock_env)

    file_contents = open(mock_env, "r").read()

    assert file_contents


def test_load_everything(mock_env: str) -> None:
    """Assert order of operations and parsing"""
    try:
        os.environ["SECRETBOX_TEST_PROJECT_ENVIRONMENT"] = "testing"
        os.environ["bywhatchancewouldthisexist"] = "egg"

        secretbox = LoadEnv(mock_env)
        secretbox.load()

        # This should be overwritten to match the fixture .env value
        assert secretbox.get("SECRETBOX_TEST_PROJECT_ENVIRONMENT") == "sandbox"

        assert secretbox.get("bywhatchancewouldthisexist") == "egg"
        assert secretbox.get("SUPER_SECRET") == "12345"
        assert secretbox.get("VALID") == "="

    finally:
        # Don't contaminate other tests
        del os.environ["SECRETBOX_TEST_PROJECT_ENVIRONMENT"]
        del os.environ["bywhatchancewouldthisexist"]


def test_load_missing_file() -> None:
    """Confirm clean run if file is missing"""
    secretbox = LoadEnv("bywhatchancewouldthisexist.derp")
    result = secretbox.load_env_file()
    assert not result


def test_autoload_tempfile(mock_env: str) -> None:
    """One less line of code needed"""
    secretbox = LoadEnv(mock_env, auto_load=True)
    assert secretbox.get("SUPER_SECRET") == "12345"


def test_missing_key_is_none() -> None:
    """Missing key? Check behind the milk"""
    secretbox = LoadEnv()
    assert secretbox.get("bywhatchancewouldthisexist") is None


def test_load_local_environment() -> None:
    """Use an injected environ to test load"""
    secretbox = LoadEnv()
    try:
        os.environ["bywhatchancewouldthisexist"] = "egg"
        secretbox.load_env_vars()

        assert secretbox.get("bywhatchancewouldthisexist") == "egg"

    finally:
        del os.environ["bywhatchancewouldthisexist"]
