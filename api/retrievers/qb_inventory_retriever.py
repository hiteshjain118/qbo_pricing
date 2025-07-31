import json
from typing import Any, Dict

import pandas as pd
import requests
from api.retrievers.qb_retriever import QBRetriever
from oauth_manager import QBOOAuthManager
from qbo_request_auth_params import QBORequestAuthParams
from logging_config import setup_logging
import logging

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)


class QBInventoryRetriever(QBRetriever):
    def __init__(self, auth_params: QBORequestAuthParams, realm_id: str):
        super().__init__(auth_params, realm_id)
        self.page_size = 100
        self.start_pos = 1


    def call_api_and_extract_cols(self) -> pd.DataFrame:
        # handle paginated queries and response 
        cols = pd.DataFrame()
        while True:
            paginated_response = self._call_api()
            page_cols = self._extract_cols(paginated_response)
            cols = pd.concat([cols, page_cols])
            if len(page_cols) < self.page_size:
                break
            self.start_pos += self.page_size    

        return cols

    def _call_api(self) -> str:
        """
        Query QuickBooks for inventory pricing data for products from bill transactions
        
        Returns:
            Formatted string containing inventory pricing data
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

        return response.text

    def _extract_cols(self, response: str) -> pd.DataFrame:
        inventory_data = []
        response_json = json.loads(response)
        for item_data in response_json['QueryResponse']['Item']:
                    
            inventory_info = {
                # 'product_name': product_name,
                # 'product_name': item_data.get('Name', 'N/A'),
                'product_name': item_data.get('FullyQualifiedName', 'N/A'),
                # 'product_name': item_data.get('Id', 'N/A'),
                'inventory_price': item_data.get('UnitPrice', 0.0),
            }
                    
            inventory_data.append(inventory_info)
        
        return pd.DataFrame(inventory_data)
    
    def _describe_for_logging(self, df: pd.DataFrame) -> str:
        return (
            f"Got total:#{len(df)} inventory items"
            f" across #{len(df['product_name'].unique())} unique products"
        )