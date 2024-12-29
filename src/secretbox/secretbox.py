from __future__ import annotations

import logging
import os


class SecretBox:
    """
    A key-value store optionally loaded from the local environment and other sources.

    All keys will be normalized to upper-case. Key lookups are case-sensitive.
    """

    logger = logging.getLogger(__name__)

    def __init__(self, *, load_environ: bool = False) -> None:
        """
        Initialize SecretBox

        Keyword Args:
            load_environ : Load existing environment variables when True.
        """
        self._loaded_values: dict[str, str] = {}

        if load_environ:
            self._loaded_values = {
                key.upper(): value for key, value in os.environ.items()
            }

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

        NOTE: Keys will be normalized to upper-case.

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

        self._loaded_values[key.upper()] = value
