from abc import ABC
from typing import Dict


class Loader(ABC):
    """Abstract Base Class for all loaders"""

    def __init__(self) -> None:
        super().__init__()
        self.loaded_values: Dict[str, str] = {}

    def load_values(self, **kwargs: str) -> bool:
        """Override with loading optionation, store within self.loaded_values"""
        raise NotImplementedError()  # pragma: no cover
