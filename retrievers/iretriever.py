from abc import ABC, abstractmethod
import json
from typing import Any

import pandas as pd

from qbo_request_auth_params import QBORequestAuthParams
class IRetriever(ABC):
    @abstractmethod
    def retrieve(self) -> Any:
        pass

    @abstractmethod
    def _describe_for_logging(self, output: Any) -> str:
        pass