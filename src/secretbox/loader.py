from __future__ import annotations

from abc import ABC
from abc import abstractmethod
from typing import Any


class Loader(ABC):
    """Abstract Base Class for all loaders"""

    loaded_values: dict[str, str]

    @abstractmethod
    def run(self) -> bool:
        """Call .load_values and inject values to environ."""
        raise NotImplementedError()

    @abstractmethod
    def load_values(self, **kwargs: Any) -> bool:
        """Load from source, store values with class instance."""
        raise NotImplementedError()
