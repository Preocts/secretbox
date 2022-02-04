"""Unit tests for aws parameter store interactions with boto3"""
from typing import Any
from typing import Dict
from typing import Generator
from typing import List
from unittest.mock import patch

import pytest
from secretbox.awsparameterstore_loader import AWSParameterStore

boto3_lib = pytest.importorskip("boto3", reason="boto3")
mypy_boto3 = pytest.importorskip("mypy_boto3_ssm", reason="mypy_boto3")

if True:
    import botocore.client
    import botocore.session
    from botocore.client import BaseClient
    from botocore.exceptions import StubAssertionError
    from botocore.stub import Stubber


TEST_VALUE = "abcdefg"
TEST_LIST = ",".join([TEST_VALUE, TEST_VALUE, TEST_VALUE])
TEST_PATH = "/my/parameter/prefix/"
TEST_REGION = "us-east-1"
TEST_STORE = "my_store"
TEST_STORE2 = "my_store2"
TEST_STORE3 = "my_store3"
TEST_VALUE = "abcdefg"


@pytest.fixture
def valid_ssm() -> Generator[BaseClient, None, None]:
    """
    Creates a mock ssm for testing. Response valids are shortened for test

    Supports three calls
        - .get_parameters_by_path
            - No `NextToken`
            - `NextToken` exists
            - `NextToken` exists
    """

    # Matches args in class
    expected_parameters = {
        "Recursive": True,
        "MaxResults": 10,
        "WithDecryption": True,
        "Path": TEST_PATH,
    }

    responses: List[Dict[str, str]] = []
    responses.append(
        {
            "Name": f"{TEST_PATH}{TEST_STORE}",
            "Value": TEST_VALUE,
            "Type": "String",
        }
    )
    # Build enough responses to test pagination
    for idx in range(0, 26):
        responses.append(
            {
                "Name": f"{TEST_PATH}{TEST_STORE}/{idx}",
                "Value": TEST_VALUE,
                "Type": "String",
            }
        )
    # Add additonal cases, asserting we collect pagination correctly
    responses.append(
        {
            "Name": f"{TEST_PATH}{TEST_STORE2}",
            "Value": TEST_VALUE,
            "Type": "SecureString",
        }
    )
    responses.append(
        {
            "Name": f"{TEST_PATH}{TEST_STORE3}",
            "Value": TEST_LIST,
            "Type": "StringList",
        }
    )

    call_one = {"Parameters": responses[0:9], "NextToken": "callone"}
    call_two = {"Parameters": responses[10:19], "NextToken": "calltwo"}
    call_three = {"Parameters": responses[20:29]}

    ssm_session = botocore.session.get_session().create_client(
        service_name="ssm",
        region_name=TEST_REGION,
    )

    with Stubber(ssm_session) as stubber:
        stubber.add_response(
            method="get_parameters_by_path",
            service_response=call_one,
            expected_params=expected_parameters,
        )
        stubber.add_response(
            method="get_parameters_by_path",
            service_response=call_two,
            expected_params=dict(**expected_parameters, NextToken="callone"),
        )
        stubber.add_response(
            method="get_parameters_by_path",
            service_response=call_three,
            expected_params=dict(**expected_parameters, NextToken="calltwo"),
        )
        yield ssm_session


@pytest.fixture
def invalid_ssm() -> Generator[BaseClient, None, None]:
    """
    Creates a mock ssm for testing. Response is a ClientError
    """

    # Matches args in class
    expected_parameters = {
        "Recursive": True,
        "MaxResults": 10,
        "WithDecryption": True,
        "Path": TEST_PATH,
    }

    ssm_session = botocore.session.get_session().create_client(
        service_name="ssm",
        region_name=TEST_REGION,
    )

    with Stubber(ssm_session) as stubber:
        stubber.add_client_error(
            method="get_parameters_by_path",
            service_error_code="ResourceNotFoundException",
            service_message="Mock Client Error",
            http_status_code=404,
            expected_params=expected_parameters,
        )
        yield ssm_session


@pytest.fixture
def loader() -> Generator[AWSParameterStore, None, None]:
    """Pass an unaltered loader"""
    loader = AWSParameterStore()
    yield loader


@pytest.fixture
def stub_loader(valid_ssm: BaseClient) -> Generator[AWSParameterStore, None, None]:
    """Wraps AWS client with Stubber"""
    store = AWSParameterStore()
    with patch.object(store, "get_aws_client", return_value=valid_ssm):
        yield store


@pytest.fixture
def broken_loader(invalid_ssm: BaseClient) -> Generator[AWSParameterStore, None, None]:
    """Pass a loader that raises ClientError"""
    store = AWSParameterStore()
    with patch.object(store, "get_aws_client", return_value=invalid_ssm):
        yield store


def test_stubber_passed_for_client(stub_loader: AWSParameterStore) -> None:
    assert isinstance(stub_loader.get_aws_client(), BaseClient)


def test_parameter_values_success_load(stub_loader: AWSParameterStore) -> None:
    assert stub_loader.load_values(
        aws_sstore_name=TEST_PATH,
        aws_region_name=TEST_REGION,
    )
    assert stub_loader.loaded_values.get(TEST_STORE) == TEST_VALUE
    assert stub_loader.loaded_values.get(TEST_STORE2) == TEST_VALUE
    assert stub_loader.loaded_values.get(TEST_STORE3) == TEST_LIST


def test_loading_wrong_prefix(stub_loader: AWSParameterStore) -> None:
    # Catch this as an unhappy path. Outside of a stubber this would return nothing
    with pytest.raises(StubAssertionError):
        assert stub_loader.load_values(
            aws_sstore_name=TEST_STORE,
            aws_region_name=TEST_REGION,
        )


def test_missing_store_name(loader: AWSParameterStore, caplog: Any) -> None:
    assert loader.load_values()
    assert "Missing parameter name" in caplog.text


def test_missing_region(loader: AWSParameterStore, caplog: Any) -> None:
    assert not loader.load_values(aws_sstore_name=TEST_STORE)
    assert "Invalid SSM client" in caplog.text


def test_client_error_catch_on_load(broken_loader: AWSParameterStore) -> None:
    assert not broken_loader.load_values(
        aws_sstore_name=TEST_PATH,
        aws_region_name=TEST_REGION,
    )


def test_client_with_region(loader: AWSParameterStore) -> None:
    loader.aws_region = TEST_REGION
    assert loader.get_aws_client() is not None
