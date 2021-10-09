"""
Load system environ values

Author  : Preocts <Preocts#8196>
Git Repo: https://github.com/Preocts/secretbox
"""
import logging
import os

from secretbox.loader import Loader


class EnvironLoader(Loader):
    """Load environ values"""

    logger = logging.getLogger(__name__)

    def load_values(self, **kwargs: str) -> bool:
        """Loads all visible environmental variables"""
        self.logger.debug("Reading %s environ variables", len(os.environ))
        for key, value in os.environ.items():
            self.loaded_values[key] = value
        return True
