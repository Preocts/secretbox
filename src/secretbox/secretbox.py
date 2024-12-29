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
        if not isinstance(key, str) or not isinstance(value, str):
            msg = f"Keys and values of a Secretbox object must be of type str. You provided: {type(key).__name__}:{type(value).__name__}"
            raise TypeError(msg)

        self._loaded_values[key] = value

    def get(self, key: str, default: str | None = None) -> str:
        """
        Get a value from the SecretBox. If default is provided and the value is not found, return the default instead.

        Args:
            key: Key index to lookup
            default: A default return value. If provided, must be a string

        Raises:
            ValueError: If default is provided but not as a string
            KeyError: If the key is not present and the default value is None
        """
        if default is not None and not isinstance(default, str):
            msg = f"Default value must be provided as a str. Given {type(default).__name__} instead."
            raise ValueError(msg)

        try:
            value = self._loaded_values[key]

        except KeyError as err:
            if default is not None:
                value = default

            else:
                raise err

        return value
