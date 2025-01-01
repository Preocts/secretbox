from __future__ import annotations

import contextlib
from collections.abc import Generator

_BOOLEAN_CONVERTION = {
    "true": True,
    "1": True,
    "false": False,
    "0": False,
    True: True,
    False: False,
}


@contextlib.contextmanager
def _handle_exception(_type: type) -> Generator[None, None, None]:
    """
    Handle KeyError and ValueError as expected while getting values from loaded_values.

    Args:
        _type: The expected final type of the value being fetched

    Returns:
        None

    Raises:
        TypeError: If default is provided but is not an bool
        KeyError: If the key is not present and the default value is None
    """
    try:
        yield None

    except KeyError as err:
        msg = f"Requested key '{err}' does not exist and no default was provided."
        raise KeyError(msg) from None

    except ValueError:
        msg = f"Failed to convert value to a '{_type.__name__}'"
        raise ValueError(msg) from None


class SecretBox:
    """A key-value store optionally loaded from the local environment and other sources."""

    def __init__(self) -> None:
        """Create an empty SecretBox."""
        self._loaded_values: dict[str, str] = {}

    @property
    def loaded_values(self) -> dict[str, str]:
        return self._loaded_values.copy()

    def __getitem__(self, key: str) -> str:
        """
        Get a loaded value by key.

        Args:
            key: Key to lookup for requested value

        Returns:
            str

        Raises:
            KeyError
        """
        return self._loaded_values[key]

    def __setitem__(self, key: str, value: str) -> None:
        """
        Set a value assigned to a key. The key and value must be a string.

        Args:
            key: Key index of the value
            value: Value stored at the provided key index

        Returns:
            None

        Raises:
            ValueError: If the key or value are not a string
        """
        self._validate_type(key, str, "key")
        self._validate_type(value, str, "value")

        self._loaded_values[key] = value

    @_handle_exception(str)
    def get(self, key: str, default: str | None = None) -> str:
        """
        Get a value from the SecretBox.

        If default is provided and the value is not found, return the default instead.

        Args:
            key: Key index to lookup
            default: A default return value. If provided, must be a string

        Raises:
            TypeError: If default is provided but not as a string
            KeyError: If the key is not present and the default value is None
        """
        self._validate_type(default, str, "default")

        value = self._loaded_values.get(key, default)
        if value is None:
            raise KeyError(key)

        return value

    @_handle_exception(int)
    def get_int(self, key: str, default: int | None = None) -> int:
        """
        Get a value from SecretBox, converting it to an int.

        If default is provided and the value is not found, return the default instead.

        Args:
            key: Key index to lookup
            default: A default return value. If provided, must be an int

        Raises:
            ValueError: If the discovered value cannot be converted to an int
            TypeError: If default is provided but is not an int
            KeyError: If the key is not present and the default value is None
        """
        self._validate_type(default, int, "default")

        value = self._loaded_values.get(key, default)
        if value is None:
            raise KeyError(key)

        return int(value)

    @_handle_exception(float)
    def get_float(self, key: str, default: float | None = None) -> float:
        """
        Get a value from SecretBox, converting it to an float.

        If default is provided and the value is not found, return the default instead.

        Args:
            key: Key index to lookup
            default: A default return value. If provided, must be a float

        Raises:
            ValueError: If the discovered value is not a float
            TypeError: If default is provided but is not a float
            KeyError: If the key is not present and the default value is None
        """
        self._validate_type(default, float, "default")

        fetch_value = self._loaded_values.get(key)

        if fetch_value is None and default is not None:
            return default

        elif fetch_value is None:
            raise KeyError(key)

        elif fetch_value.isdigit():
            raise ValueError()

        return float(fetch_value)

    @_handle_exception(bool)
    def get_bool(self, key: str, default: bool | None = None) -> bool:
        """
        Get a value from SecretBox, converting it to an bool.

        Valid boolean values are "true", "false", "1", "0" (case insensitive)

        If default is provided and the value is not found, return the default instead.

        Args:
            key: Key index to lookup
            default: A default return value. If provided, must be an bool

        Raises:
            ValueError: If the discovered value cannot be converted to an bool
            TypeError: If default is provided but is not an bool
            KeyError: If the key is not present and the default value is None
        """
        self._validate_type(default, bool, "default")

        _value = self._loaded_values.get(key, default)
        if _value is None:
            raise KeyError(key)

        value = _BOOLEAN_CONVERTION.get(_value)
        if value is None:
            raise ValueError()

        return value

    @staticmethod
    def _validate_type(obj: object | None, _type: type, label: str) -> None:
        """
        Validate that the given obj is an instance of the given type.

        This check is skipped if obj is None.

        Args:
            obj: Any object
            _type: Any single type to check for isinstance()
            label: Name of object, used for raised exception

        Returns:
            None

        Raises:
            TypeError: When obj is not an instance of _type
        """
        if obj is not None and not isinstance(obj, _type):
            msg = f"Expected a {_type.__name__} for '{label}', given {type(obj).__name__}."
            raise TypeError(msg)

        return None
