import json
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
import requests
from core.iauthenticator import IHTTPConnection
from core.http_retriever import HTTPRetriever
from qbo.qbo_user import QBOUser
from qbo.qbo_authenticator import QBOHTTPConnection
from oauth_manager import QBOOAuthManager
from qbo_request_auth_params import QBORequestAuthParams, is_prod_environment
from core.logging_config import setup_logging
import logging

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)


class QBInventoryAPIRetriever(HTTPRetriever):
    def api_summary(self) -> str:
        return f"Retrieves inventory from the QBO HTTP query API"

    @staticmethod
    def init_for_ephemeral_chat(
        connection: IHTTPConnection, 
        qbo_user: QBOUser, 
        save_file_path: Optional[str] = None
    ):
        return QBInventoryAPIRetriever(connection, qbo_user, save_file_path)

    def __init__(
            self, 
            connection: IHTTPConnection,
            qbo_user: QBOUser,
            save_file_path: Optional[str] = None
        ):
        super().__init__(connection, qbo_user, save_file_path)
        self.qbo_user = qbo_user

    def _cache_key(self) -> str:
        return f"inventory_api_retriever_{self.qbo_user.realm_id}_{self.start_pos}"
    
    def _get_endpoint(self) -> str:
        return "query"
    
    def _get_params(self) -> Dict[str, Any]:
        query = f"SELECT * FROM Item STARTPOSITION {self.start_pos} MAXRESULTS {self.page_size}"
        return {
            "query": query,
            "minorversion": "65"
        }
         
    def _to_json(self, response: requests.Response) -> Tuple[Dict[str, Any], int]:
        intuit_tid = response.headers.get('intuit_tid')
        if intuit_tid:
            logger.info(f"Successfully got {self.api_summary()} API Response - intuit_tid: {intuit_tid}")
        else:
            logger.info(f"Failed to get {self.api_summary()} API Response - no intuit_tid found in headers")
        
        response_json = response.json()
        return response_json, len(response_json['QueryResponse'].get('Item', []))

