from retrievers.iretriever import IRetriever
from intent_servers.i_intent_server import IIntentServer
import pandas as pd
import json
import logging
from logging_config import setup_logging
from typing import Any, Dict

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)


class InventoryServer(IIntentServer):
    def __init__(self, qb_inventory_retriever: IRetriever):
        self.qb_inventory_retriever = qb_inventory_retriever

    def serve(self) -> pd.DataFrame:
        responses = self.qb_inventory_retriever.retrieve()
        inventory_data = pd.DataFrame() #empty dataframe
        for response in responses:
            inventory_data = pd.concat([inventory_data, self._extract_cols(response)])
        logger.info(self._describe_for_logging(inventory_data))
        return inventory_data
    
    def _extract_cols(self, response: Dict[str, Any]) -> pd.DataFrame:
        inventory_data = []
        for item_data in response['QueryResponse'].get('Item', []):     
            inventory_info = {
                'product_name': item_data.get('FullyQualifiedName', 'N/A'),
                'inventory_price': item_data.get('UnitPrice', 0.0),
            }
            
            if inventory_info['product_name'] == 'N/A':
                continue
            inventory_data.append(inventory_info)
        
        return pd.DataFrame(inventory_data)
    
    def _describe_for_logging(self, df: pd.DataFrame) -> str:
        if df.empty:
            return "Got total:#0 inventory items across #0 unique products"
        
        return (
            f"Got total:#{len(df)} inventory items"
            f" across #{len(df['product_name'].unique())} unique products"
        )