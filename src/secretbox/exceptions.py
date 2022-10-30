"""Custom Exceptions."""
from __future__ import annotations


class LoaderException(Exception):
    """Custom Exception for all loader exceptions."""

    def __init__(self, *args: object) -> None:
        super().__init__(*args)
