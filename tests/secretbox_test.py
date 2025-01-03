from __future__ import annotations

import pytest

from secretbox import SecretBox


class MockLoader:
    name = "MockLoader"

    def __init__(self, mock_values: dict[str, str]) -> None:
        self._values = mock_values

    def run(self) -> dict[str, str]:
        return self._values


@pytest.fixture
def simple_box() -> SecretBox:
    # Create a SecretBox with a simple value loaded for testing
    simple_values = {
        "foo": "bar",
        "biz": "baz",
        "answer": "42",
        "funny_number": "69.420",
        "ballin": "1",
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

    simple_box["redbird"] = expected_value

    updated_value = simple_box["redbird"]
    assert updated_value == expected_value


def test_set_item_raises_with_invalid_value(simple_box: SecretBox) -> None:
    # SecretBox should only accept strings as values
    with pytest.raises(TypeError):
        simple_box["FOO"] = 1  # type: ignore


def test_set_item_raises_with_invalid_key(simple_box: SecretBox) -> None:
    # SecretBox should only accept strings as keys
    with pytest.raises(TypeError):
        simple_box[1] = "flapjack"  # type: ignore


def test_set_item_raises_key_error_on_overwrite(simple_box: SecretBox) -> None:
    # Raises a key error if the key being set already exists
    with pytest.raises(KeyError):
        simple_box["foo"] = "baz"


def test_load_with_multiple_loaders_strict_raises(simple_box: SecretBox) -> None:
    # In strict mode (default) conflicting keys should raise
    loader_one = MockLoader({"luz": "human"})
    loader_two = MockLoader({"luz": "good witch"})

    with pytest.raises(KeyError):
        simple_box.load(loader_one, loader_two)


def test_load_with_multiple_loaders_not_strict() -> None:
    # Multiple loaders should overwrite the loaded values of the prior
    simple_box = SecretBox(raise_on_overwrite=False)
    loader_one = MockLoader({"luz": "human", "owl": "lady"})
    loader_two = MockLoader({"luz": "good witch", "boiling": "sea"})

    simple_box.load(loader_one, loader_two)
    values = simple_box.loaded_values

    assert values["luz"] == "good witch"
    assert values["owl"] == "lady"
    assert values["boiling"] == "sea"


@pytest.mark.parametrize(
    "method, key, expected",
    (
        ("get", "foo", "bar"),
        ("get_int", "answer", 42),
        ("get_float", "funny_number", 69.420),
        ("get_bool", "ballin", True),
    ),
)
def test_get_methods_return_expected_value(
    method: str,
    key: str,
    expected: str | int | float | bool,
    simple_box: SecretBox,
) -> None:
    # Paramaterized to test all get methods
    # .get("foo") should work the same as ["foo"] when the key exists
    value = getattr(simple_box, method)(key)

    assert value == expected


@pytest.mark.parametrize(
    "method, expected",
    (
        ("get", "goblins"),
        ("get_int", 37337),
        ("get_float", 3.14),
        ("get_bool", False),
    ),
)
def test_get_methods_return_default_when_key_not_exists(
    method: str,
    expected: str,
    simple_box: SecretBox,
) -> None:
    # Like .get() on dictionaries, return the default if provided
    # when the key doens't exist.
    value = getattr(simple_box, method)("missing_key", expected)

    assert value == expected


@pytest.mark.parametrize(
    "method",
    (
        ("get"),
        ("get_int"),
        ("get_float"),
        ("get_bool"),
    ),
)
def test_get_methods_raise_keyerror_when_key_not_exists(
    method: str,
    simple_box: SecretBox,
) -> None:
    # Unlike dictionaries, if the default value is not provided None will not
    # be returned. Secretbox enforces a string return value.
    with pytest.raises(KeyError):
        getattr(simple_box, method)("missing_key")


@pytest.mark.parametrize(
    "method, default",
    (
        ("get", 42),
        ("get_int", 3.13),
        ("get_float", 0),
        ("get_bool", "true"),
    ),
)
def test_get_methods_raise_typeerror_on_invalid_default(
    method: str,
    default: str,
    simple_box: SecretBox,
) -> None:
    # Type guarding the default value to ensure .get() always returns correct type
    with pytest.raises(TypeError):
        getattr(simple_box, method)("foo", default)


@pytest.mark.parametrize(
    "method, key",
    (
        ("get_int", "foo"),
        ("get_float", "foo"),
        ("get_bool", "foo"),
    ),
)
def test_get_methods_raise_valueerror_on_convert_error(
    method: str,
    key: str,
    simple_box: SecretBox,
) -> None:
    # If the value cannot be converted to the requested type, raise ValueError
    with pytest.raises(ValueError):
        getattr(simple_box, method)(key)


def test_get_int_fails_when_value_is_float(simple_box: SecretBox) -> None:
    # We do not want type coercion to happen
    with pytest.raises(ValueError):
        simple_box.get_int("funny_number")


def test_get_float_fails_when_value_is_ing(simple_box: SecretBox) -> None:
    # We do not want type coercion to happen
    with pytest.raises(ValueError):
        simple_box.get_float("answer")
