from __future__ import annotations

import os
from unittest.mock import patch

import pytest

from secretbox import SecretBox


@pytest.fixture
def simple_box() -> SecretBox:
    # Create a SecretBox with a simple value loaded for testing
    simple_values = {
        "foo": "bar",
        "biz": "baz",
    }
    with patch.dict(os.environ, simple_values, clear=True):
        sb = SecretBox(load_environ=True)

    return sb


def test_loaded_value_property_is_copy(simple_box: SecretBox) -> None:
    # Ensure the property is not returning a reference to the internal dict
    first_values = simple_box.loaded_values
    first_values["foo"] = "baz"

    second_values = simple_box.loaded_values

    assert first_values != second_values


def test_init_loads_environment_variables() -> None:
    # Test that we load the existing environment variables and nothing
    # else at the time of initialization.

    expected_values = {"FOO": "bar"}

    with patch.dict(os.environ, expected_values, clear=True):
        sb = SecretBox(load_environ=True)
    loaded_values = sb.loaded_values

    assert loaded_values == expected_values


def test_init_is_empty_when_created() -> None:
    # Creating a SecretBox instance should yield an empty box
    sb = SecretBox()

    loaded_values = sb.loaded_values

    assert loaded_values == {}


def test_get_item_returns_expected(simple_box: SecretBox) -> None:
    # SecretBox should behave like a dictionary when needed
    expected_key = "FOO"
    expected_value = "bar"

    value = simple_box[expected_key]

    assert value == expected_value


def test_get_item_is_case_sensitive(simple_box: SecretBox) -> None:
    # Always raise a KeyError if the key is not found
    invalid_key = "foo"

    with pytest.raises(KeyError):
        simple_box[invalid_key]


def test_set_item_accepts_valid_values(simple_box: SecretBox) -> None:
    # SecretBox should behave like a dictionary when needed
    # Keys should be normalized to upper-case
    expected_value = "flapjack"

    simple_box["foo"] = expected_value

    updated_value = simple_box["FOO"]
    assert updated_value == expected_value


def test_set_item_raises_with_invalid_value(simple_box: SecretBox) -> None:
    # SecretBox should only accept strings as values
    with pytest.raises(TypeError):
        simple_box["foo"] = 1  # type: ignore


def test_set_item_raises_with_invalid_key(simple_box: SecretBox) -> None:
    # SecretBox should only accept strings as keys
    with pytest.raises(TypeError):
        simple_box[1] = "flapjack"  # type: ignore
