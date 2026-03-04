import os
from typing import Optional, Dict

class DotEnv:
    def __init__(self, dotenv_path: str, verbose: bool = False, encoding: Optional[str] = "utf-8") -> None:
        self.dotenv_path = dotenv_path
        self._verbose = verbose
        self.encoding = encoding
        self.dict: Dict[str, Optional[str]] = {}

    def set_as_environment_variables(self) -> bool:
        if not self.dict:
            return False

        for k, v in self.dict.items():
            if k in os.environ:
                continue
            if v is not None:
                os.environ[k] = v

        return True

    def _get_stream(self):
        try:
            return open(self.dotenv_path, encoding=self.encoding)
        except OSError:
            if self._verbose:
                print(f"File not found: {self.dotenv_path}")
            return None
