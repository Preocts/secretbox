"""
Load local .env from CWD or path, if provided

Current format for the `.env` file supports strings only and is parsed in
the following order:
- Each seperate line is considered a new possible key/value set
- Each set is delimted by the first `=` found
- Leading and trailing whitespace are removed
- Matched leading/trailing single quotes or double quotes will be
  stripped from values (not keys).

I'm open to suggestions on standards to follow here.

Author  : Preocts <Preocts#8196>
Git Repo: https://github.com/Preocts/secretbox
"""
import logging

from secretbox.loader import Loader


class EnvFileLoader(Loader):
    """Load local .env file"""

    logger = logging.getLogger(__name__)

    def load_values(self, **kwargs: str) -> bool:
        """
        Loads local .env from cwd or path, if provided

        Keywords:
            filename : [str] Alternate filename to load over `.env`
        """
        filename = kwargs.get("filename", ".env")
        self.logger.debug("Reading vars from '%s'", filename)
        try:
            with open(filename, "r", encoding="utf-8") as input_file:
                self.parse_env_file(input_file.read())
        except FileNotFoundError:
            return False
        return True

    def parse_env_file(self, input_file: str) -> None:
        """Parses env file into key-pair values"""
        for line in input_file.split("\n"):
            if not line or line.strip().startswith("#") or len(line.split("=", 1)) != 2:
                continue
            key, value_dirty = line.split("=", 1)

            value = self.remove_lt_dbl_quotes(value_dirty.strip())
            value = self.remove_lt_sgl_quotes(value)

            self.loaded_values[key.strip()] = value

    def remove_lt_dbl_quotes(self, in_: str) -> str:
        """Removes matched leading and trailing double quotes"""
        return in_.strip('"') if in_.startswith('"') and in_.endswith('"') else in_

    def remove_lt_sgl_quotes(self, in_: str) -> str:
        """Removes matched leading and trailing double quotes"""
        return in_.strip("'") if in_.startswith("'") and in_.endswith("'") else in_
