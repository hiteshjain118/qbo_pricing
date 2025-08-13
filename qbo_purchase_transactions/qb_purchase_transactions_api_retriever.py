from datetime import datetime, timedelta
import json
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
import pytz
import requests
from core.iauthenticator import IHTTPConnection
from core.http_retriever import HTTPRetriever
from qbo.qbo_user import QBOUser
from core.logging_config import setup_logging
import logging

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

class QBPurchaseTransactionsAPIRetriever(HTTPRetriever):
    def api_summary(self) -> str:
        return f"Retrieves purchase transactions from the QBO HTTP query API"
    
    @staticmethod
    def init_for_ephemeral_chat(
        connection: IHTTPConnection, 
        qbo_user: QBOUser, 
        save_file_path: Optional[str] = None
    ):
        report_dt = datetime.now().astimezone(pytz.timezone(qbo_user.user_timezone))
        return QBPurchaseTransactionsAPIRetriever(connection, qbo_user, report_dt, save_file_path)

    def __init__(
            self,
            connection: IHTTPConnection,
            qbo_user: QBOUser,
            report_dt: datetime,
            save_file_path: Optional[str] = None
        ):
        super().__init__(connection, qbo_user, save_file_path)
        self.qbo_user = qbo_user
        self.report_date = report_dt.astimezone(pytz.timezone(self.qbo_user.user_timezone)).strftime("%Y-%m-%d")

    def _cache_key(self) -> str:
        return f"purchase_transactions_api_retriever_{self.qbo_user.realm_id}_{self.report_date}"

    def _get_endpoint(self) -> str:
        return "query"
    
    def _get_params(self) -> Dict[str, Any]:
        query = (
            f"SELECT * FROM Bill WHERE TxnDate >= '{self.report_date}' and TxnDate <= '{self.report_date}' "
        )
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
        return response_json, len(response_json['QueryResponse'].get('Bill', []))

