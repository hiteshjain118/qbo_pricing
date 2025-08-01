from datetime import datetime, timedelta
import json
from typing import Any, Dict, List, Tuple

import pandas as pd
import pytz
import requests
from retrievers.qb_api_retriever import QBAPIRetriever
from qbo_request_auth_params import QBORequestAuthParams
from logging_config import setup_logging
import logging

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

class QBPurchaseTransactionsAPIRetriever(QBAPIRetriever):
    
    def __init__(
            self, 
            auth_params: QBORequestAuthParams, 
            realm_id: str, 
            report_dt: datetime,
            save_file_path: str=None
        ):
        super().__init__(auth_params, realm_id, save_file_path)
        
        self.report_date = report_dt.astimezone(pytz.timezone('America/Los_Angeles')).strftime("%Y-%m-%d")
    
    def _call_api_once(self) -> Tuple[Dict[str, Any], int]:
        """
        Call the API and return the response as a dictionary
        """
        # Query Bill transactions
        logger.info(
            f"Making API call to get bill transactions for company {self.realm_id} "
            f"for {self.report_date} "
        )
        
        # Build the API URL for bills for the report date - 1 day ago
        url = f"{self.auth_params.qbo_base_url}/v3/company/{self.realm_id}/query"
        
        # Query for bills within the date range
        query = (
            f"SELECT * FROM Bill WHERE TxnDate >= '{self.report_date}' "
        )
        
        params = {
            "query": query,
            "minorversion": "65"
        }
        
        response = requests.get(url, headers=self.get_headers(), params=params)
        response.raise_for_status()
        
        # Log intuit_tid if present in response headers
        intuit_tid = response.headers.get('intuit_tid')
        if intuit_tid:
            logger.info(f"Bill Transactions API Response - intuit_tid: {intuit_tid}")
        else:
            logger.info("Bill Transactions API Response - no intuit_tid found in headers")
        
        response_json = response.json()
        return response_json, len(response_json['QueryResponse']['Bill'])

    def _describe_for_logging(self, responses: List[Dict[str, Any]]) -> str:
        return (
            f"On {self.report_date},"
            f" got total:#{len(responses)} purchase transaction responses "
        )
    