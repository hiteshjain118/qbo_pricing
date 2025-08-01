import json
import os
import pandas as pd
import traceback
from datetime import datetime, timedelta
import pytz
from pretty_html_table import build_table
import io
import base64

from intent_servers.i_intent_server import IIntentServer
from intent_servers.inventory_server import InventoryServer
from intent_servers.purchase_transactions_server import PurchaseTransactionsServer
from retrievers.qb_api_retriever import QBAPIRetriever
from retrievers.qb_inventory_api_retriever import QBInventoryAPIRetriever
from retrievers.qb_purchase_transactions_api_retriever import QBPurchaseTransactionsAPIRetriever
from retrievers.qb_file_retriever import QBFileRetriever
from qbo_request_auth_params import QBORequestAuthParams
from email_sender import CompanyEmailSender
from logging_config import setup_logging
import logging

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

class PricingDeltaServer(IIntentServer):
    @staticmethod
    def init_with_api_retrievers(
        auth_params: QBORequestAuthParams, 
        realm_id: str, 
        email: str,
    ) -> 'PricingDeltaServer':
        # Use absolute paths that work in deployed environment
        current_dir = os.getcwd()
        inventory_save_file_path = os.path.join(current_dir, 'retrievers', 'tests', 'mock_inventory_response.jsonl')
        purchase_transactions_save_file_path = os.path.join(current_dir, 'retrievers', 'tests', 'mock_purchase_transactions_response.jsonl')

        inventory_server = InventoryServer(
            qb_inventory_retriever=QBInventoryAPIRetriever(
                auth_params=auth_params,
                realm_id=realm_id,
                save_file_path=inventory_save_file_path
            )
        )
        purchase_transactions_server = PurchaseTransactionsServer(
            qb_purchase_transactions_retriever=QBPurchaseTransactionsAPIRetriever(
                auth_params=auth_params,
                realm_id=realm_id,
                report_dt=datetime.now(),
                save_file_path=purchase_transactions_save_file_path
            ))
        return PricingDeltaServer(
            purchase_transactions_server=purchase_transactions_server,
            inventory_server=inventory_server,
            realm_id=realm_id,
            email_sender = CompanyEmailSender(
                email_to=email, 
                subject=f"QuickBooks Pricing Delta Report - {realm_id}", 
                company_id=realm_id
            )
        )

    @staticmethod
    def init_with_file_retrievers(
        inventory_file_path: str,
        purchase_transactions_file_path: str,
        realm_id: str,
        email: str
    ) -> 'PricingDeltaServer':
        return PricingDeltaServer(
            purchase_transactions_server=PurchaseTransactionsServer(
                qb_purchase_transactions_retriever=QBFileRetriever(
                    file_path=purchase_transactions_file_path
                )
            ),
            inventory_server=InventoryServer(
                qb_inventory_retriever=QBFileRetriever(
                    file_path=inventory_file_path
                )
            ),
            realm_id=realm_id,
            email_sender = CompanyEmailSender(
                email_to=email, 
                subject=f"QuickBooks Pricing Delta Report - {realm_id}", 
                company_id=realm_id
            )
        )

    def __init__(
        self, 
        purchase_transactions_server: PurchaseTransactionsServer,
        inventory_server: InventoryServer,
        realm_id: str,
        email_sender: CompanyEmailSender,
    ):
        self.purchase_transactions_server = purchase_transactions_server
        self.inventory_server = inventory_server
        self.realm_id = realm_id
        self.email_sender = email_sender
        
    def serve(self) -> bool:
        """Generate balance sheet report and send via email"""
        
        print(f"Generating report for company {self.realm_id}")
        
        # Get pricing delta data
        pricing_delta = self.get_pricing_delta()
        html_table, excel_data = self.format_pricing_delta_to_html(pricing_delta)
    
        # Send email
        self.email_sender.send_email(html_table, excel_data)
        return True

    def get_pricing_delta(self) -> pd.DataFrame:
        purchase_transactions_df = self.purchase_transactions_server.serve()
        inventory_pricing_df = self.inventory_server.serve()
        
        # Handle empty DataFrames
        if purchase_transactions_df.empty or inventory_pricing_df.empty:
            return pd.DataFrame()
        
        # Merge the two dataframes on the product_name column
        merged_df = pd.merge(
            purchase_transactions_df, 
            inventory_pricing_df, 
            on='product_name', 
            how='left',
            indicator='matched'
        )
        
        # Calculate the pricing delta
        merged_df['pricing_delta'] = (merged_df['inventory_price'] - merged_df['purchase_price'])

        merged_df['pricing_perc_delta'] = round(
            merged_df['pricing_delta'] / merged_df['purchase_price'] * 100, 2
        )
        logger.info(self._describe_for_logging(merged_df))

        return merged_df
    
    def format_pricing_delta_to_html(self, pricing_delta: pd.DataFrame) -> tuple[str, str]:
        # Handle empty DataFrame
        if pricing_delta.empty:
            return "", ""
        
        pricing_delta = pricing_delta.sort_values(by='pricing_perc_delta', ascending=False)
        
        rename_cols_map = {
            'product_name': 'Product Name',
            'purchase_quantity': 'Purchase Quantity',
            'purchase_amount': 'Purchase Amount',
            'purchase_price': 'Purchase Price',
            'purchase_transaction_date': 'Purchase Date',
            'inventory_price': 'Inventory Price',
            'pricing_delta': 'Markup (Inventory - Purchase)',
            'pricing_perc_delta': 'Markup % (Inventory - Purchase)/Purchase'
        }
        pricing_delta.rename(columns=rename_cols_map, inplace=True)
        
        # email columsn 
        email_columns = [
            'Product Name', 
            'Purchase Price', 
            'Inventory Price', 
            'Markup (Inventory - Purchase)', 
            'Markup % (Inventory - Purchase)/Purchase'
        ]
        
        # Filter to only include columns that exist in the dataframe
        # email columns + (rename_cols.values - emails_columns)
        pricing_delta_excel = pricing_delta[email_columns + list(set(rename_cols_map.values()) - set(email_columns))]
        
        # email html will have product name , purchase price, inventory price, pricing % delta
        # excel attachment will have all columns in the specified order
        html_table = build_table(pricing_delta[email_columns], 'blue_light')
        
        # Create Excel data in memory and encode as base64
        excel_buffer = io.BytesIO()
        pricing_delta_excel.to_excel(excel_buffer, index=False)
        excel_buffer.seek(0)
        excel_data = base64.b64encode(excel_buffer.getvalue()).decode('utf-8')
        
        return html_table, excel_data

    def _describe_for_logging(self, pricing_delta: pd.DataFrame) -> str:
        if pricing_delta.empty:
            return "Pricing delta total rows: 0 w/ nan inventory price: 0 products with nan inventory price: []"
        
        return (
            f"Pricing delta total rows: {len(pricing_delta)} "
            f"w/ nan inventory price: {pricing_delta['inventory_price'].isna().sum()}"
            f" products with nan inventory price: {pricing_delta[pricing_delta['matched'] == 'left_only']['product_name'].unique()}"
        )