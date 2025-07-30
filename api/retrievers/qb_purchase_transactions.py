from datetime import datetime, timedelta
import json
from typing import Any

import pandas as pd
import requests
from api.retrievers.qb_retriever import QBRetriever
from qbo_request_auth_params import QBORequestAuthParams
from logging_config import setup_logging
import logging

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

class QBPurchaseTransactionsRetriever(QBRetriever):
    
    def __init__(self, auth_params: QBORequestAuthParams, realm_id: str, report_date: str = None):
        super().__init__(auth_params, realm_id)
        self.report_date = report_date

    def _extract_cols(self, response: str) -> pd.DataFrame:
        """
        Extract specific columns from bill transactions JSON
        
        Returns:
            List of dictionaries with columns: product_name, quantity, rate, amount, transaction_date
            raise exception if query_response is not a valid json or not in the expected format
        """
        extracted_data = []
            
        response_json = json.loads(response)
        bills = response_json['QueryResponse']['Bill']
        
        for bill in bills:
            # Get transaction date
            transaction_date = bill.get('TxnDate', 'N/A')
            
            # Get line items
            line_items = bill.get('Line', [])
            
            for line in line_items:
                # Initialize default values
                product_name = 'Unknown'
                quantity = 0
                rate = 0.0
                amount = line.get('Amount', 0.0)
                
                # Extract from ItemBasedExpenseLineDetail
                if 'ItemBasedExpenseLineDetail' in line:
                    item_detail = line['ItemBasedExpenseLineDetail']
                    item_ref = item_detail.get('ItemRef', {})
                    product_name = item_ref.get('name', 'Unknown Item')
                    quantity = item_detail.get('Qty', 0)
                    rate = item_detail.get('UnitPrice', 0.0)
                
                # Add description if available
                description = line.get('Description', '')
                if description:
                    product_name = f"{product_name} - {description}"
                
                extracted_data.append({
                    'product_name': product_name,
                    # 'quantity': quantity,
                    'purchase_price': rate,
                    # 'amount': amount,
                    # 'transaction_date': transaction_date
                })
        
        logger.info(f"Extracted {len(extracted_data)} line items")
        return pd.DataFrame(extracted_data)

    def _call_api(self) -> str:
        """
        Query QuickBooks for bill transactions from the last 10 days
        
        Args:
            report_date: Date in YYYY-MM-DD format (defaults to last 10 days)
            
        Returns:
            Formatted string containing bill transactions
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
        
        return response.text

    def _describe_for_logging(self, df: pd.DataFrame) -> str:
        return (
            f"On {self.report_date},"
            f" got total:#{len(df)} bill transactions "
            f"across #{len(df['product_name'].unique())} unique products"
        )
    