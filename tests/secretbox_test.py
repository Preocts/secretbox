from __future__ import annotations

import pytest

from secretbox import SecretBox


@pytest.fixture
def simple_box() -> SecretBox:
    # Create a SecretBox with a simple value loaded for testing
    simple_values = {
        "foo": "bar",
        "biz": "baz",
    }
    sb = SecretBox()

    for key, value in simple_values.items():
        sb[key] = value

    return sb


def test_loaded_value_property_is_copy(simple_box: SecretBox) -> None:
    # Ensure the property is not returning a reference to the internal dict
    first_values = simple_box.loaded_values
    first_values["foo"] = "baz"

    second_values = simple_box.loaded_values

    assert first_values != second_values


def test_init_is_empty_when_created() -> None:
    # Creating a SecretBox instance should yield an empty box
    sb = SecretBox()

    loaded_values = sb.loaded_values

    assert loaded_values == {}


def test_get_item_returns_expected(simple_box: SecretBox) -> None:
    # SecretBox should behave like a dictionary when needed
    expected_key = "foo"
    expected_value = "bar"

    value = simple_box[expected_key]

    assert value == expected_value


def test_get_item_is_case_sensitive(simple_box: SecretBox) -> None:
    # Always raise a KeyError if the key is not found
    invalid_key = "FOO"

    with pytest.raises(KeyError):
        simple_box[invalid_key]


def test_set_item_accepts_valid_values(simple_box: SecretBox) -> None:
    # SecretBox should behave like a dictionary when needed
    # Keys should be normalized to upper-case
    expected_value = "flapjack"

    simple_box["foo"] = expected_value

    updated_value = simple_box["foo"]
    assert updated_value == expected_value


def test_set_item_raises_with_invalid_value(simple_box: SecretBox) -> None:
    # SecretBox should only accept strings as values
    with pytest.raises(TypeError):
        simple_box["FOO"] = 1  # type: ignore


def test_set_item_raises_with_invalid_key(simple_box: SecretBox) -> None:
    # SecretBox should only accept strings as keys
    with pytest.raises(TypeError):
        simple_box[1] = "flapjack"  # type: ignore


def test_get_returns_expected_value(simple_box: SecretBox) -> None:
    # .get("foo") should work the same as ["foo"] when the key exists
    expected_value = "bar"

    value = simple_box.get("foo")

    assert value == expected_value


def test_get_returns_default_when_key_not_exists(simple_box: SecretBox) -> None:
    # Like .get() on dictionaries, return the default if provided when the key
    # doens't exist
    expected_value = "flapjack"

    value = simple_box.get("cardinal", expected_value)

    assert value == expected_value


def test_get_raises_keyerror_when_key_not_exists(simple_box: SecretBox) -> None:
    # Unlike dictionaries, if the default value is not provided None will not
    # be returned. Secretbox enforces a string return value.
    with pytest.raises(KeyError):
        simple_box.get("cardinal")


def test_get_raises_valueerror_default_is_not_string(simple_box: SecretBox) -> None:
    # Type guarding the default value to ensure .get() always returns a string
    with pytest.raises(ValueError):
        simple_box.get("answer", 42)  # type: ignore
