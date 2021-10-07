"""Simple test to ensure we read environ"""
import os
from unittest.mock import patch

from secretbox.environ_loader import EnvironLoader

from tests.conftest import ENV_FILE_EXPECTED


def test_load_env_vars(environ_loader: EnvironLoader) -> None:
    """Load and confirm values from environ"""
    with patch.dict(os.environ, ENV_FILE_EXPECTED):
        environ_loader.load_values()
        for key, value in ENV_FILE_EXPECTED.items():
            assert environ_loader.loaded_values.get(key) == value, f"{key}, {value}"
