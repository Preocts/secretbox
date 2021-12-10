"""Unit tests for aws parameter store interactions"""
import importlib
import sys
from typing import Generator
from unittest.mock import patch

import pytest
from secretbox import awsparameterstore_loader as ssm_loader_module
from secretbox.awsparameterstore_loader import AWSParameterStore

from tests.conftest import TEST_LIST
from tests.conftest import TEST_PATH
from tests.conftest import TEST_REGION
from tests.conftest import TEST_STORE
from tests.conftest import TEST_STORE2
from tests.conftest import TEST_STORE3
from tests.conftest import TEST_VALUE


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


@pytest.mark.usefixtures("mask_aws_creds", "parameterstore")
def test_parameter_values(
    loader: AWSParameterStore,
) -> None:
    """compare parameters from mocked loader to what we put in there"""
    # loading succeeded
    assert loader.load_values(aws_sstore_name=TEST_PATH, aws_region_name=TEST_REGION)

    # both our parameters exist and have the expected value
    assert loader.loaded_values.get(f"{TEST_PATH}{TEST_STORE}") == TEST_VALUE
    assert loader.loaded_values.get(f"{TEST_PATH}{TEST_STORE2}") == TEST_VALUE
    assert loader.loaded_values.get(f"{TEST_PATH}{TEST_STORE3}") == TEST_LIST
