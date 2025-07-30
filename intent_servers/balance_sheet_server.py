import traceback
from typing import Optional
from email_sender import CompanyEmailSender
from qbo_balance_sheet_getter import QBOBalanceSheetGetter
from oauth_manager import QBOOAuthManager
from qbo_request_auth_params import QBORequestAuthParams
import logging
from logging_config import setup_logging

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

class BalanceSheetServer:
    
    def __init__(self, auth_params: QBORequestAuthParams, realm_id: str):
        self.auth_params = auth_params
        self.oauth_manager = QBOOAuthManager(auth_params)
        self.realm_id = realm_id
        
    def get_balance_sheet(self) -> Optional[str]:
        """Get balance sheet report for a company"""
        # Get valid access token
        
        # Initialize QBO API
        access_token = self.oauth_manager.get_valid_access_token_not_throws(self.realm_id)
        qbo = QBOBalanceSheetGetter(self.auth_params, self.realm_id, access_token)
        
        # Query Balance Sheet
        try:
            logger.info(f"Making API call to get balance sheet for company {self.realm_id}")
            balance_sheet = qbo.query_balance_sheet_report()
            logger.info(f"Raw balance sheet data: {balance_sheet}")
            formatted = qbo.format_balance_sheet(balance_sheet)
            logger.info(f"Formatted balance sheet: {len(formatted)} characters")
            return formatted
        except Exception as e:
            #print stack trace
            logging.error(f"Error querying balance sheet for company {self.realm_id}: {e}")
            logging.error(traceback.format_exc())
            # logging.error(f"Error querying balance sheet for company {self.realm_id}: {e}")
            return None
                 
    def generate_and_send_report(self, email: str) -> bool:
        """Generate balance sheet report and send via email"""
        # Check if company is still connected
        if not self.oauth_manager.is_company_connected(self.realm_id):
            print(f"Company {self.realm_id} is no longer connected")
            return False
        
        print(f"Generating report for company {self.realm_id}")
        
        # Get balance sheet data
        balance_sheet = self.get_balance_sheet()
        
        if not balance_sheet:
            print(f"Failed to retrieve balance sheet for company {self.realm_id}")
            return False
        logger.info(f"Balance sheet retrieved for company {self.realm_id} balance sheet: {len(balance_sheet)} characters")
        # Send email
        email_sender = CompanyEmailSender(
            email_to=email, 
            subject=f"QuickBooks Balance Sheet Report - {self.realm_id}", 
            report_html=balance_sheet, 
            company_id=self.realm_id
        )
        if email_sender.send_email():
            print(f"✅ Report sent to {email} for company {self.realm_id}")
            return True
        else:
            print(f"❌ Failed to send report to {email} for company {self.realm_id}")
            return False
