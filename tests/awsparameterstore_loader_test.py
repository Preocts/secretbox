"""Unit tests for aws parameter store interactions"""
import importlib
import sys
from typing import Generator
from unittest.mock import patch

import pytest
from boto3.session import Session
from moto.ssm import mock_ssm
from mypy_boto3_ssm.client import SSMClient
from secretbox import awsparameterstore_loader as ssm_loader_module
from secretbox.awsparameterstore_loader import AWSParameterStore

TEST_VALUE = "abcdefg"
TEST_LIST = ",".join([TEST_VALUE, TEST_VALUE, TEST_VALUE])
TEST_PATH = "/my/parameter/prefix/"
TEST_REGION = "us-east-1"
TEST_STORE = "my_store"
TEST_STORE2 = "my_store2"
TEST_STORE3 = "my_store3"
TEST_VALUE = "abcdefg"


@pytest.fixture
def parameterstore() -> Generator[SSMClient, None, None]:
    """Populate mock parameterstore with two values we can load via prefix"""

    with mock_ssm():
        session = Session()
        client = session.client(
            service_name="ssm",
            region_name=TEST_REGION,
        )
        client.put_parameter(
            Name=f"{TEST_PATH}{TEST_STORE}", Value=TEST_VALUE, Type="String"
        )
        # Load enough so pagination can be tested
        for x in range(1, 31):
            client.put_parameter(
                Name=f"{TEST_PATH}{TEST_STORE}/{x}", Value=TEST_VALUE, Type="String"
            )
        client.put_parameter(
            Name=f"{TEST_PATH}{TEST_STORE2}", Value=TEST_VALUE, Type="SecureString"
        )
        client.put_parameter(
            Name=f"{TEST_PATH}{TEST_STORE3}",
            Value=TEST_LIST,
            Type="StringList",
        )

        yield client


@pytest.fixture
def loader() -> Generator[AWSParameterStore, None, None]:
    """Create a fixture to test with"""
    clazz = AWSParameterStore()
    assert not clazz.loaded_values
    yield clazz


@pytest.mark.usefixtures("mask_aws_creds", "parameterstore")
def test_boto3_not_installed_auto_load(loader: AWSParameterStore) -> None:
    """Silently skip loading AWS parameter store if no boto3"""
    with patch.object(ssm_loader_module, "boto3", None):
        assert not loader.loaded_values
        assert not loader.load_values(aws_sstore=TEST_PATH, aws_region=TEST_REGION)
        assert not loader.loaded_values


def test_boto3_missing_import_catch() -> None:
    """Reload loadenv without boto3"""
    with patch.dict(sys.modules, {"boto3": None}):
        importlib.reload(ssm_loader_module)
        assert ssm_loader_module.boto3 is None
    # Reload after test to avoid polution
    importlib.reload(ssm_loader_module)


def test_boto3_stubs_missing_import_catch() -> None:
    with patch.dict(sys.modules, {"mypy_boto3_ssm.client": None}):
        importlib.reload(ssm_loader_module)
        assert ssm_loader_module.SSMClient is None
    # Reload after test to avoid polution
    importlib.reload(ssm_loader_module)


@pytest.mark.parametrize(
    ("prefix", "region", "expectedCnt"),
    (
        (TEST_PATH, TEST_REGION, 33),  # correct, root node
        (f"{TEST_PATH}{TEST_STORE}/", TEST_REGION, 30),  # correct, child node
        (TEST_STORE, TEST_REGION, 0),  # wrong prefix
        (None, TEST_REGION, 0),  # no prefix
        (TEST_PATH, "us-east-2", 0),  # wrong region
        (TEST_PATH, None, 0),  # no region
    ),
)
@pytest.mark.usefixtures("mask_aws_creds", "parameterstore")
def test_count_parameters(
    loader: AWSParameterStore,
    prefix: str,
    region: str,
    expectedCnt: int,
) -> None:
    """Load a parameter from mocked loader"""
    # nothing has been loaded
    assert loader.loaded_values.get(prefix) is None

    # loading succeeded
    if expectedCnt > 0:
        # don't assert this if we're trying to make it fail!
        assert loader.load_values(aws_sstore_name=prefix, aws_region_name=region)
    else:
        loader.load_values(aws_sstore_name=prefix, aws_region_name=region)

    # loaded the proper number of parameters
    assert len(loader.loaded_values) == expectedCnt
