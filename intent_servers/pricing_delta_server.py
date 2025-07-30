import logging
from typing import Dict, List, Any
from api.retrievers.qb_inventory_retriever import QBInventoryRetriever
from api.retrievers.qb_purchase_transactions import QBPurchaseTransactionsRetriever
from email_sender import CompanyEmailSender
from oauth_manager import QBOOAuthManager
from qbo_request_auth_params import QBORequestAuthParams
from qbo_balance_sheet_getter import QBOBalanceSheetGetter
from datetime import datetime, timedelta
import requests
import json
from logging_config import setup_logging
import pandas as pd
from pretty_html_table import build_table

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)


class PricingDeltaServer:
    def __init__(self, auth_params: QBORequestAuthParams, realm_id: str):
        self.auth_params = auth_params
        self.realm_id = realm_id
        self.oauth_manager = QBOOAuthManager(auth_params)
        self.qb_inventory_retriever = QBInventoryRetriever(auth_params, realm_id)
        self.qb_purchase_transactions_retriever = QBPurchaseTransactionsRetriever(
            auth_params=auth_params, 
            realm_id=realm_id,
            report_date=(datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        )
        
        
    def generate_and_send_report(self, email: str) -> bool:
        """Generate balance sheet report and send via email"""
        
        print(f"Generating report for company {self.realm_id}")
        
        # Get pricing delta data
        pricing_delta = self.get_pricing_delta()
        
        # Send email
        email_sender = CompanyEmailSender(
            email_to=email, 
            subject=f"QuickBooks Pricing Delta Report - {self.realm_id}", 
            report_html=pricing_delta, 
            company_id=self.realm_id
        )
        if email_sender.send_email():
            print(f"✅ Report sent to {email} for company {self.realm_id}")
            return True
        else:
            print(f"❌ Failed to send report to {email} for company {self.realm_id}")
            return False


    def get_pricing_delta(self) -> str:
        purchase_transactions_df = self.qb_purchase_transactions_retriever.retrieve()
        inventory_pricing_df = self.qb_inventory_retriever.retrieve()
        
        # Merge the two dataframes on the product_name column
        merged_df = pd.merge(
            purchase_transactions_df, 
            inventory_pricing_df, 
            on='product_name', 
            how='left'
        )
        
        # Calculate the pricing delta
        merged_df['pricing_perc_delta'] = round(
            (merged_df['inventory_price'] - merged_df['purchase_price']) / 
            merged_df['inventory_price'] * 100, 2
        )
        
        return self.format_pricing_delta_to_html(merged_df)
    
    def format_pricing_delta_to_html(self, pricing_delta: pd.DataFrame) -> str:
        pricing_delta = pricing_delta.sort_values(by='pricing_perc_delta', ascending=False)
        html_table = build_table(pricing_delta, 'blue_light')

        return html_table