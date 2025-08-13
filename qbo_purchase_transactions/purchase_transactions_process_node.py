import pandas as pd
from core.iretriever import IRetriever
from core.iprocess_node import IProcessNode
import json
import logging
from core.logging_config import setup_logging
from typing import Any, Dict

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)


class PurchaseTransactionsProcessNode(IProcessNode):
    def __init__(self, qb_purchase_transactions_retriever: IRetriever):
        self.qb_purchase_transactions_retriever = qb_purchase_transactions_retriever

    def process(self) -> pd.DataFrame:
        responses = self.qb_purchase_transactions_retriever.retrieve()
        purchase_transactions = pd.DataFrame()
        for response in responses:
            purchase_transactions = pd.concat([purchase_transactions, self._extract_cols(response)])
        logger.info(self._describe_for_logging(purchase_transactions))
        return purchase_transactions
    
    def _extract_cols(self, response: Dict[str, Any]) -> pd.DataFrame:
        """
        Extract specific columns from bill transactions JSON
        
        Returns:
            List of dictionaries with columns: product_name, quantity, rate, amount, transaction_date
            raise exception if query_response is not a valid json or not in the expected format
        """
        extracted_data = []
        
        bills = response['QueryResponse'].get('Bill', [])
        
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

                if product_name == 'Unknown Item' or quantity == 0 or rate == 0.0 or amount == 0.0:
                    continue
                
                extracted_data.append({
                    'product_name': product_name,
                    'purchase_quantity': quantity,
                    'purchase_price': rate,
                    'purchase_amount': amount,
                    'purchase_transaction_date': transaction_date
                })
        
        logger.info(f"Extracted {len(extracted_data)} line items")
        return pd.DataFrame(extracted_data)

    def empty_value_reason(self) -> str:
        return "No purchase transactions found"
    
    def _describe_for_logging(self, output: pd.DataFrame) -> str:
        if output.empty:
            return "Got total:#0 purchase transactions across #0 unique products"
        
        return (
            f"Got total:#{len(output)} purchase transactions"
            f" across #{len(output['product_name'].unique())} unique products"
        )