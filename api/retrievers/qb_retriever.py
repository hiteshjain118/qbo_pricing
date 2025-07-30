from abc import ABC, abstractmethod
import json
from typing import Any, Dict

import pandas as pd

from oauth_manager import QBOOAuthManager
from qbo_request_auth_params import QBORequestAuthParams

from api.retrievers.iretriever import IRetriever
from logging_config import setup_logging
import logging

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)


class QBRetriever(IRetriever):
    def __init__(self, auth_params: QBORequestAuthParams, realm_id: str):
        self.auth_params = auth_params
        self.realm_id = realm_id
        self.oauth_manager = QBOOAuthManager(auth_params)

    def retrieve(self) -> Any:
        if not self.oauth_manager.is_company_connected(self.realm_id):
            print(f"Company {self.realm_id} is no longer connected")
            raise Exception(f"Company {self.realm_id} is no longer connected")
        
        cols = self.call_api_and_extract_cols()
        logger.info(self._describe_for_logging(cols))
        return cols

    def call_api_and_extract_cols(self) -> pd.DataFrame:
        response = self._call_api()
        return self._extract_cols(response)
    
    def get_headers(self)-> Dict[str, str]:
        access_token = self.oauth_manager.get_valid_access_token_not_throws(self.realm_id)
        if not access_token:
            raise Exception(f"No valid access token for company {self.realm_id}")
        
        return {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/json",
            "Content-Type": "application/json"
        }

    @abstractmethod
    def _extract_cols(self, response: str) -> pd.DataFrame:
        pass
    
    @abstractmethod
    def _call_api(self) -> str:
        """
        Call the API and return the response
        """
        pass 