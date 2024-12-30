from __future__ import annotations


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

        try:
            value = self._loaded_values[key]

        except KeyError as err:
            if default is not None:
                value = default

            else:
                raise err

        return value

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

        try:
            value = int(self._loaded_values[key])

        except KeyError as err:
            if default is not None:
                value = default

            else:
                raise err

        except ValueError as err:
            msg = f"The value of '{key}` could not be converted to an int."
            raise ValueError(msg) from err

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
