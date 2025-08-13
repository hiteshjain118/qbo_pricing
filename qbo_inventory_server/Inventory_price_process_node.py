from core.iretriever import IRetriever
from core.iprocess_node import IProcessNode
import pandas as pd
import json
import logging
from core.logging_config import setup_logging
from typing import Any, Dict

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)


class InventoryPriceProcessNode(IProcessNode):
    def __init__(self, qb_inventory_retriever: IRetriever):
        self.qb_inventory_retriever = qb_inventory_retriever

    def process(self) -> pd.DataFrame:
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
    
    def empty_value_reason(self) -> str:
        return "No inventory items found"
    
    def _describe_for_logging(self, output: pd.DataFrame) -> str:
        if output.empty:
            return "Got total:#0 inventory items across #0 unique products"
        
        return (
            f"Got total:#{len(output)} inventory items"
            f" across #{len(output['product_name'].unique())} unique products"
        )