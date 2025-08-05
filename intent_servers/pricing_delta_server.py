import json
import os
import pandas as pd
import traceback
from datetime import datetime, timedelta
import pytz
from pretty_html_table import build_table
import io
import base64

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

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
        report_dt: datetime = datetime.now()
    ) -> 'PricingDeltaServer':
        # Use absolute paths that work in deployed environment
        current_dir = os.getcwd()
        # inventory_save_file_path = os.path.join(current_dir, 'retrievers', 'tests', 'mock_inventory_response.jsonl')
        # purchase_transactions_save_file_path = os.path.join(current_dir, 'retrievers', 'tests', 'mock_purchase_transactions_response.jsonl')

        inventory_save_file_path = None
        purchase_transactions_save_file_path = None

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
                report_dt=report_dt,
                save_file_path=purchase_transactions_save_file_path
            ))
        return PricingDeltaServer(
            purchase_transactions_server=purchase_transactions_server,
            inventory_server=inventory_server,
            realm_id=realm_id,
            email_sender = PricingDeltaServer.get_email_sender(realm_id, email, report_dt)
        )

    @staticmethod
    def get_email_sender(realm_id: str, email: str, report_dt: datetime) -> CompanyEmailSender:
        return CompanyEmailSender(
            email_to=email, 
            subject=f"QuickBooks Pricing Markup Report for {report_dt.strftime('%Y-%m-%d')} transactions", 
            company_id=realm_id
        )

    @staticmethod
    def init_with_file_retrievers(
        inventory_file_path: str,
        purchase_transactions_file_path: str,
        realm_id: str,
        email: str,
        report_dt: datetime = datetime.now()
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
            email_sender = PricingDeltaServer.get_email_sender(realm_id, email, report_dt)
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
        
        logger.info(f"Generating report for company {self.realm_id}")
        
        try:
            # Get pricing delta data
            purchase_transactions_df = self.purchase_transactions_server.serve()
            inventory_pricing_df = self.inventory_server.serve()
            pricing_delta_df = pd.DataFrame()

            # Handle empty DataFrames
            if purchase_transactions_df.empty:
                html = self.get_empty_table_html("No purchase transactions found")
                excel_data = ""
            elif inventory_pricing_df.empty:
                html = self.get_empty_table_html("No inventory pricing found")
                excel_data = ""
            else:
                pricing_delta_df = self.get_pricing_delta(purchase_transactions_df, inventory_pricing_df)
                html, excel_data = self.format_pricing_delta_to_html(pricing_delta_df)
            
            logger.info(self._describe_for_logging(pricing_delta_df, purchase_transactions_df, inventory_pricing_df))
        
            # Send email
            self.email_sender.send_email(html, excel_data)
        
        except Exception as e:
            logger.error(f"Error generating report: {e}")
            traceback.print_exc()
            raise e
        
        return True

    def get_pricing_delta(
        self, 
        purchase_transactions_df: pd.DataFrame, 
        inventory_pricing_df: pd.DataFrame
    ) -> pd.DataFrame:
        
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
        
        #html to be added to the email contains the transaction date and then the table
        transaction_date_html = f"<p>This report computes price markup between {pricing_delta['Purchase Date'].iloc[0]} bill transactions and current inventory prices.</p>"
        html_table = transaction_date_html + html_table

        # Create Excel data in memory and encode as base64
        excel_buffer = io.BytesIO()
        pricing_delta_excel.to_excel(excel_buffer, index=False)
        excel_buffer.seek(0)
        excel_data = base64.b64encode(excel_buffer.getvalue()).decode('utf-8')
        
        return html_table, excel_data

    def get_empty_table_html(self, message: str) -> str:
        return f"<p>{message}</p>"
    
    def _describe_for_logging(
        self, 
        pricing_delta: pd.DataFrame, 
        purchase_transactions_df: pd.DataFrame, 
        inventory_pricing_df: pd.DataFrame
    ) -> str:
        if pricing_delta.empty:
            return (
                f"Pricing delta total rows: 0 w/ nan inventory price: 0 products with nan inventory price: []"
                f"purchase transactions total rows: {len(purchase_transactions_df)}"
                f"inventory pricing total rows: {len(inventory_pricing_df)}"
            )
        
        return (
            f"Pricing delta total rows: {len(pricing_delta)} "
            f"w/ nan inventory price: {pricing_delta['inventory_price'].isna().sum()}"
            f" products with nan inventory price: {pricing_delta[pricing_delta['matched'] == 'left_only']['product_name'].unique()}"
        )