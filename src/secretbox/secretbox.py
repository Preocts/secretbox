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
