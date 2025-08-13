import pandas as pd
from core.iprocess_node import IProcessNode
from qbo.qbo_inventory_server.Inventory_price_process_node import InventoryPriceProcessNode
from qbo.qbo_purchase_transactions.purchase_transactions_process_node import PurchaseTransactionsProcessNode

class PricingDeltaProcessNode(IProcessNode):
    def __init__(
            self, 
            purchase_transactions_process_node: PurchaseTransactionsProcessNode, 
            inventory_process_node: InventoryPriceProcessNode
        ):
        self.purchase_transactions_process_node = purchase_transactions_process_node
        self.inventory_process_node = inventory_process_node
        self.purchase_transactions_df = pd.DataFrame()
        self.inventory_pricing_df = pd.DataFrame()

    def process(self):
        self.purchase_transactions_df = self.purchase_transactions_slot_extractor.process()
        self.inventory_pricing_df = self.inventory_slot_extractor.process()
            
        if self.purchase_transactions_df.empty or self.inventory_pricing_df.empty:
            return pd.DataFrame()
        
        # Merge the two dataframes on the product_name column
        merged_df = pd.merge(
            self.purchase_transactions_df, 
            self.inventory_pricing_df, 
            on='product_name', 
            how='left',
            indicator='matched'
        )
        
        # Calculate the pricing delta
        merged_df['pricing_delta'] = (merged_df['inventory_price'] - merged_df['purchase_price'])

        merged_df['pricing_perc_delta'] = round(
            merged_df['pricing_delta'] / merged_df['purchase_price'] * 100, 2
        )
        self._describe_for_logging(
            merged_df
        )
        return merged_df


    def empty_value_reason(self) -> str:
        if self.purchase_transactions_df.empty:
            return "No purchase transactions found"
        if self.inventory_pricing_df.empty:
            return "No inventory pricing found"
        return "slot extraction error"


    def _describe_for_logging(
        self,
        output: pd.DataFrame,
    ) -> str:
        pricing_delta_df = output
        
        if pricing_delta_df.empty:
            return (
                f"Pricing delta total rows: 0 w/ nan inventory price: 0 products with nan inventory price: []"
                f"purchase transactions total rows: {len(self.purchase_transactions_df)}"
                f"inventory pricing total rows: {len(self.inventory_pricing_df)}"
            )
        
        return (
            f"Pricing delta total rows: {len(pricing_delta_df)} "
            f"w/ nan inventory price: {pricing_delta_df['inventory_price'].isna().sum()}"
            f" products with nan inventory price: {pricing_delta_df[pricing_delta_df['matched'] == 'left_only']['product_name'].unique()}"
        )