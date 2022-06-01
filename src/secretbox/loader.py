from __future__ import annotations

from abc import ABC
from abc import abstractmethod
from typing import Any


class Loader(ABC):
    """Abstract Base Class for all loaders"""

    @property
    @abstractmethod
    def values(self) -> dict[str, str]:
        """Property: loaded values."""
        raise NotImplementedError()

    @abstractmethod
    def run(self) -> bool:
        """Call .load_values and inject values to environ."""
        raise NotImplementedError()

    @abstractmethod
    def _load_values(self, **kwargs: Any) -> bool:
        """Load from source, store values with class instance."""
        raise NotImplementedError()
