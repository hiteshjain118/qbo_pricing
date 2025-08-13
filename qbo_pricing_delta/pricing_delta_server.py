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

from qbo.qbo_authenticator import QBOHTTPConnection
from qbo.qbo_user import QBOUser
from qbo.qbo_inventory_server.Inventory_price_process_node import InventoryPriceProcessNode
from qbo.qbo_pricing_delta.pricing_delta_process_node import PricingDeltaProcessNode
from qbo.qbo_purchase_transactions.purchase_transactions_process_node import PurchaseTransactionsProcessNode
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.iintent_server import IIntentServer
from qbo.qbo_inventory_server.Inventory_price_process_node import InventoryPriceProcessNode
from qbo.qbo_purchase_transactions.purchase_transactions_process_node import PurchaseTransactionsProcessNode
from qbo_inventory_server.qb_inventory_api_retriever import QBInventoryAPIRetriever
from qbo_purchase_transactions.qb_purchase_transactions_api_retriever import QBPurchaseTransactionsAPIRetriever
from core.jsonl_file_retriever import JsonlFileRetriever
from qbo_request_auth_params import QBORequestAuthParams, is_prod_environment
from email_sender import CompanyEmailSender
from core.logging_config import setup_logging
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
        report_dt: datetime = datetime.now(pytz.timezone('America/Los_Angeles'))
    ) -> 'PricingDeltaServer':
        # Use absolute paths that work in deployed environment
        current_dir = os.getcwd()
        # inventory_save_file_path = os.path.join(current_dir, 'retrievers', 'tests', 'mock_inventory_response.jsonl')
        # purchase_transactions_save_file_path = os.path.join(current_dir, 'retrievers', 'tests', 'mock_purchase_transactions_response.jsonl')

        inventory_save_file_path = None
        purchase_transactions_save_file_path = None
        
        connection = PricingDeltaServer.http_connection(auth_params, realm_id)
        qbo_user = PricingDeltaServer.qbo_user(realm_id)
        
        inventory_process_node = InventoryPriceProcessNode(
            qb_inventory_retriever=QBInventoryAPIRetriever(
                connection=connection,
                qbo_user=qbo_user,
                save_file_path=inventory_save_file_path
            )
        )
        purchase_transactions_process_node = PurchaseTransactionsProcessNode(
            qb_purchase_transactions_retriever=QBPurchaseTransactionsAPIRetriever(
                connection=connection,
                qbo_user=qbo_user,
                report_dt=report_dt,
                save_file_path=purchase_transactions_save_file_path
            ))
        return PricingDeltaServer(
            pricing_delta_process_node=PricingDeltaProcessNode(
                purchase_transactions_process_node=purchase_transactions_process_node,
                inventory_process_node=inventory_process_node
            ),
            qbo_user=qbo_user,
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
        inventory_save_file_path: str,
        purchase_transactions_save_file_path: str,
        realm_id: str,
        email: str,
        report_dt: datetime = datetime.now(pytz.timezone('America/Los_Angeles'))
    ) -> 'PricingDeltaServer':
        return PricingDeltaServer(
                pricing_delta_process_node=PricingDeltaProcessNode(
                    purchase_transactions_process_node=PurchaseTransactionsProcessNode(
                    qb_purchase_transactions_retriever=JsonlFileRetriever(
                        file_path=purchase_transactions_save_file_path
                    )
                ),
                inventory_process_node=InventoryPriceProcessNode(
                    qb_inventory_retriever=JsonlFileRetriever(
                        file_path=inventory_save_file_path
                    )
                )
            ),
            qbo_user=PricingDeltaServer.qbo_user(realm_id),
            email_sender = PricingDeltaServer.get_email_sender(realm_id, email, report_dt)
        )

    @staticmethod
    def http_connection(
        auth_params: QBORequestAuthParams, 
        realm_id: str,
    ):
        return QBOHTTPConnection(auth_params, realm_id)

    @staticmethod
    def qbo_user(
        realm_id: str,
    ) -> QBOUser:
        return QBOUser(
            realm_id=realm_id, 
            user_timezone="America/Los_Angeles"
        )

    def __init__(
        self, 
        # purchase_transactions_server: PurchaseTransactionsServer,
        pricing_delta_process_node: PricingDeltaProcessNode,
        qbo_user: QBOUser,
        email_sender: CompanyEmailSender,
    ):
        # self.purchase_transactions_server = purchase_transactions_server
        self.pricing_delta_process_node = pricing_delta_process_node
        self.qbo_user = qbo_user
        self.email_sender = email_sender
        
    def serve(self) -> bool:
        """Generate balance sheet report and send via email"""
        
        logger.info(f"Generating report for company {self.qbo_user.realm_id}")
        
        try:
            # Get pricing delta data
            pricing_delta_df = self.pricing_delta_process_node.process()

            # Handle empty DataFrames
            if pricing_delta_df.empty:
                empty_reason = self.pricing_delta_process_node.empty_value_reason()
                html = self.get_empty_table_html(empty_reason)
                excel_data = ""
            else:
                html, excel_data = self.format_pricing_delta_to_html(pricing_delta_df)
            
            # Send email
            self.email_sender.send_email(html, excel_data)
        
        except Exception as e:
            logger.error(f"Error generating report: {e}")
            traceback.print_exc()
            raise e
        
        return True
    
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