"""Unit tests for aws parameter store interactions without boto3"""
from typing import Generator
from unittest.mock import patch

import pytest
from secretbox import awsparameterstore_loader as ssm_loader_module
from secretbox.awsparameterstore_loader import AWSParameterStore

TEST_PATH = "/my/parameter/prefix/"
TEST_REGION = "us-east-1"


@pytest.fixture
def loader() -> Generator[AWSParameterStore, None, None]:
    """Pass an unaltered loader"""
    loader = AWSParameterStore()
    yield loader


def test_empty_values_on_init(loader: AWSParameterStore) -> None:
    assert not loader.loaded_values


def test_fall_through_with_no_boto3(loader: AWSParameterStore) -> None:
    with patch.object(ssm_loader_module, "boto3", None):
        assert not loader.load_values(aws_sstore=TEST_PATH, aws_region=TEST_REGION)
        assert not loader.loaded_values


def test_none_client_no_region(loader: AWSParameterStore) -> None:
    assert loader.get_aws_client() is None
