from abc import ABC
from typing import Dict


class Loader(ABC):
    """Abstract Base Class for all loaders"""

    def __init__(self) -> None:
        super().__init__()
        self.loaded_values: Dict[str, str] = {}

    # TODO (preocts): Need a better method of passing required values in parameters
    def load_values(self, **kwargs: str) -> bool:
        """Override with loading optionation, store within self.loaded_values"""
        raise NotImplementedError()  # pragma: no cover

    def reset_values(self) -> None:
        """Override with a reset process for returning to baseline"""
        raise NotImplementedError()  # pragma: no cover

    def get_values(self) -> Dict[str, str]:
        """Override, as needed, to return loaded values as a dictionary of str:str"""
        raise NotImplementedError()  # pragma: no cover
