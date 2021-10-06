"""Unit tests for aws secrect manager interactions"""
import importlib
import sys
from typing import Generator
from unittest.mock import patch

import pytest
from secretbox import aws_loader  # This is what we test on!
from secretbox.aws_loader import AWSLoader  # For typing only

from tests.conftest import TEST_KEY_NAME
from tests.conftest import TEST_REGION
from tests.conftest import TEST_STORE
from tests.conftest import TEST_VALUE


@pytest.fixture(scope="function", name="loader")
def fixtures_loader() -> Generator[AWSLoader, None, None]:
    """Create a fixture to test with"""
    yield aws_loader.AWSLoader()


@pytest.mark.usefixtures("remove_aws_creds")
def test_load_aws_no_credentials(loader: AWSLoader) -> None:
    """Cause a NoCredentialsError to be handled"""
    assert not loader.loaded_values
    loader.load_values(aws_sstore=TEST_STORE, aws_region=TEST_REGION)
    assert not loader.loaded_values


@pytest.mark.parametrize(
    ("store", "region", "expected"),
    (
        (TEST_STORE, TEST_REGION, TEST_VALUE),
        (TEST_STORE, None, None),
        (None, TEST_REGION, None),
        (None, None, None),
        ("store/not/found", TEST_REGION, None),
        (TEST_STORE, "", None),
    ),
)
@pytest.mark.usefixtures("mask_aws_creds", "secretsmanager")
def test_load_aws_secrets(
    loader: AWSLoader,
    store: str,
    region: str,
    expected: str,
) -> None:
    """Load a secret from mocked AWS secret server"""
    assert not loader.loaded_values.get(TEST_KEY_NAME)
    loader.load_values(aws_sstore=store, aws_region=region)
    assert loader.loaded_values.get(TEST_KEY_NAME) == expected


# def test_boto3_not_installed_load_aws(loader: AWSLoader) -> None:
#     """Stop and raise if manual load_aws_store() is called without boto3"""
#     with patch.object(aws_loader, "boto3", None):
#         with pytest.raises(NotImplementedError):
#             assert not secretbox_aws.load_aws_store()


@pytest.mark.usefixtures("mask_aws_creds", "secretsmanager")
def test_boto3_not_installed_auto_load(loader: AWSLoader) -> None:
    """Silently skip loading AWS secrets manager if no boto3"""
    with patch.object(aws_loader, "boto3", None):
        assert not loader.loaded_values
        loader.load_values(aws_sstore=TEST_STORE, aws_region=TEST_REGION)
        assert not loader.loaded_values


def test_boto3_missing_import_catch() -> None:
    """Reload loadenv without boto3"""
    with patch.dict(sys.modules, {"boto3": None}):
        importlib.reload(aws_loader)
        assert aws_loader.boto3 is None
    # Reload after test to avoid polution
    importlib.reload(aws_loader)
