from __future__ import annotations

from abc import ABC
from typing import Any


class Loader(ABC):
    """Abstract Base Class for all loaders"""

    def __init__(self) -> None:
        super().__init__()
        self.loaded_values: dict[str, str] = {}

    def load_values(self, **kwargs: Any) -> bool:
        """Override with loading optionation, store within self.loaded_values"""
        raise NotImplementedError()
