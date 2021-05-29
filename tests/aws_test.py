"""Unit tests for aws secrect manager interactions"""
import importlib
import os
import sys
from unittest.mock import patch

import pytest
from secretbox import loadenv
from secretbox.loadenv import LoadEnv

from tests.conftest import TEST_KEY_NAME
from tests.conftest import TEST_REGION
from tests.conftest import TEST_STORE
from tests.conftest import TEST_VALUE


@pytest.mark.usefixtures("remove_aws_creds")
def test_load_aws_no_credentials(secretbox: LoadEnv) -> None:
    """Cause a NoCredentialsError to be handled"""
    secretbox.aws_sstore = TEST_STORE
    secretbox.aws_region = TEST_REGION

    assert not secretbox.loaded_values
    secretbox.load_aws_store()
    assert not secretbox.loaded_values


@pytest.mark.parametrize(
    ("store", "region", "expected"),
    (
        (TEST_STORE, TEST_REGION, TEST_VALUE),
        (TEST_STORE, None, ""),
        (None, TEST_REGION, ""),
        (None, None, ""),
        ("store/not/found", TEST_REGION, ""),
        (TEST_STORE, "", ""),
    ),
)
@pytest.mark.usefixtures("mask_aws_creds", "secretsmanager")
def test_load_aws_secrets(
    secretbox: LoadEnv,
    store: str,
    region: str,
    expected: str,
) -> None:
    """Load a secret from mocked AWS secret server"""
    secretbox.aws_sstore = store
    secretbox.aws_region = region

    assert not secretbox.get(TEST_KEY_NAME)
    secretbox.load()
    assert secretbox.get(TEST_KEY_NAME) == expected


def test_boto3_not_installed_load_aws(secretbox_aws: LoadEnv) -> None:
    """Stop and raise if manual load_aws_store() is called without boto3"""
    with patch.object(loadenv, "boto3", None):
        with pytest.raises(NotImplementedError):
            assert not secretbox_aws.load_aws_store()


def test_boto3_not_installed_auto_load(secretbox_aws: LoadEnv) -> None:
    """Silently skip loading AWS secrets manager if no boto3"""
    # fmt: off
    with patch.object(loadenv, "boto3", None), \
            patch.dict(os.environ, {"BOTO3_SAMPLE": "Good"}):
        # fmt: on
        assert secretbox_aws.loaded_values == {}
        secretbox_aws.load()
        assert secretbox_aws.get("BOTO3_SAMPLE") == "Good"


def test_boto3_missing_import_catch() -> None:
    """Reload loadenv without boto3"""
    with patch.dict(sys.modules, {"boto3": None}):
        importlib.reload(loadenv)
        assert loadenv.boto3 is None
    importlib.reload(loadenv)
