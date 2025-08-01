import json
from typing import Any, Dict, List, Tuple

import pandas as pd
import requests
from retrievers.qb_api_retriever import QBAPIRetriever
from oauth_manager import QBOOAuthManager
from qbo_request_auth_params import QBORequestAuthParams
from logging_config import setup_logging
import logging

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)


class QBInventoryAPIRetriever(QBAPIRetriever):
    def __init__(
            self, 
            auth_params: QBORequestAuthParams, 
            realm_id: str,
            save_file_path: str=None
        ):
        super().__init__(auth_params, realm_id, save_file_path)

    def _call_api_once(self) -> Tuple[Dict[str, Any], int]:
        """
        Call the API and return the response as a dictionary
        """
        logger.info(
            f"Retrieving inventory for company {self.realm_id} "
            f"start_pos: {self.start_pos} "
            f"page_size: {self.page_size}"
        )
        url = f"{self.auth_params.qbo_base_url}/v3/company/{self.realm_id}/query"
        query = f"SELECT * FROM Item STARTPOSITION {self.start_pos} MAXRESULTS {self.page_size}"
        
        params = {
            "query": query,
            "minorversion": "65"
        }
        
        response = requests.get(url, headers=self.get_headers(), params=params)
        response.raise_for_status()

        response_json = response.json()
        return response_json, len(response_json['QueryResponse']['Item'])

    def _describe_for_logging(self, responses: List[Dict[str, Any]]) -> str:
        return (
            f" got total:#{len(responses)} inventory responses "
        )