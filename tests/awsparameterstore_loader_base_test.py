"""Unit tests for aws parameter store interactions without boto3"""

from __future__ import annotations

from collections.abc import Generator
from unittest.mock import patch

import pytest

from secretbox import awsparameterstore_loader as ssm_loader_module
from secretbox.awsparameterstore_loader import AWSParameterStoreLoader

TEST_PATH = "/my/parameter/prefix/"
TEST_REGION = "us-east-1"


@pytest.fixture
def loader() -> Generator[AWSParameterStoreLoader, None, None]:
    """Pass an unaltered loader"""
    loader = AWSParameterStoreLoader()
    yield loader


def test_empty_values_on_init(loader: AWSParameterStoreLoader) -> None:
    assert not loader._loaded_values


def test_fall_through_with_no_boto3(loader: AWSParameterStoreLoader) -> None:
    with patch.object(ssm_loader_module, "boto3", None):
        assert not loader._load_values(aws_sstore=TEST_PATH, aws_region=TEST_REGION)
        assert not loader._loaded_values


def test_none_client_no_region(loader: AWSParameterStoreLoader) -> None:
    assert loader.get_aws_client() is None
