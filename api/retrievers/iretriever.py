from abc import ABC, abstractmethod
import json
from typing import Any

import pandas as pd
class IRetriever(ABC):
    @abstractmethod
    def retrieve(self) -> Any:
        pass

    @abstractmethod
    def _call_api(self) -> str:
        """
        Call the API and return the response
        """
        pass

    @abstractmethod
    def _extract_cols(self, response: str) -> pd.DataFrame:
        pass

    @abstractmethod
    def _describe_for_logging(self, df: pd.DataFrame) -> str:
        pass