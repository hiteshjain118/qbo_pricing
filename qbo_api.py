import requests
import json
from datetime import datetime, timedelta
import os
from typing import Dict, Any
import logging
from logging_config import setup_logging

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

class QuickBooksOnlineAPI:
    """
    QuickBooks Online API client for querying reports
    """
    SANDBOX_URL = "https://sandbox-quickbooks.api.intuit.com"
    PRODUCTION_URL = "https://quickbooks.api.intuit.com"
    
    def __init__(self, client_id: str, client_secret: str, access_token: str, realm_id: str):
        """
        Initialize QBO API client
        
        Args:
            client_id: OAuth 2.0 client ID from Intuit Developer
            client_secret: OAuth 2.0 client secret from Intuit Developer
            access_token: Valid access token for authentication
            realm_id: Company ID (realm ID) from QBO
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.access_token = access_token
        self.realm_id = realm_id
        self.base_url = self.SANDBOX_URL
        self.api_version = "v3"
        
    def _get_headers(self) -> Dict[str, str]:
        """Get headers for API requests"""
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
    
    def query_profit_and_loss_report(self, start_date: str = None, end_date: str = None) -> Dict[str, Any]:
        """
        Query Profit and Loss report from QBO
        
        Args:
            start_date: Start date in YYYY-MM-DD format (defaults to 30 days ago)
            end_date: End date in YYYY-MM-DD format (defaults to today)
            
        Returns:
            Dictionary containing the P&L report data
        """
        if not start_date:
            start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        if not end_date:
            end_date = datetime.now().strftime("%Y-%m-%d")
            
        # QBO Report API endpoint for Profit and Loss
        url = f"{self.base_url}/{self.api_version}/company/{self.realm_id}/reports/ProfitAndLoss"
        
        # Query parameters for the report
        params = {
            "start_date": start_date,
            "end_date": end_date,
            "accounting_method": "Accrual",  # or "Cash"
            "minorversion": "65"  # API minor version
        }
        
        try:
            response = requests.get(url, headers=self._get_headers(), params=params)
            response.raise_for_status()
            
            # Log intuit_tid if present in response headers
            intuit_tid = response.headers.get('intuit_tid')
            if intuit_tid:
                logger.info(f"P&L Report API Response - intuit_tid: {intuit_tid}")
            else:
                logger.info("P&L Report API Response - no intuit_tid found in headers")
            
            return response.json()
            
        except requests.exceptions.RequestException as e:
            print(f"Error querying P&L report: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Response status: {e.response.status_code}")
                print(f"Response body: {e.response.text}")
                # Log intuit_tid even in error responses
                intuit_tid = e.response.headers.get('intuit_tid')
                if intuit_tid:
                    logger.error(f"P&L Report API Error Response - intuit_tid: {intuit_tid}")
                else:
                    logger.error("P&L Report API Error Response - no intuit_tid found in headers")
            return None
    
    def query_balance_sheet_report(self, as_of_date: str = None) -> Dict[str, Any]:
        """
        Query Balance Sheet report from QBO
        
        Args:
            as_of_date: As of date in YYYY-MM-DD format (defaults to today)
            
        Returns:
            Dictionary containing the Balance Sheet report data
        """
        if not as_of_date:
            as_of_date = datetime.now().strftime("%Y-%m-%d")
            
        url = f"{self.base_url}/{self.api_version}/company/{self.realm_id}/reports/BalanceSheet"
        
        params = {
            "as_of_date": as_of_date,
            "accounting_method": "Accrual",
            "minorversion": "65"
        }
        
        try:
            response = requests.get(url, headers=self._get_headers(), params=params)
            response.raise_for_status()
            
            # Log intuit_tid if present in response headers
            intuit_tid = response.headers.get('intuit_tid')
            if intuit_tid:
                logger.info(f"Balance Sheet Report API Response - intuit_tid: {intuit_tid}")
            else:
                logger.info("Balance Sheet Report API Response - no intuit_tid found in headers")
            
            return response.json()
            
        except requests.exceptions.RequestException as e:
            print(f"Error querying Balance Sheet report: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Response status: {e.response.status_code}")
                print(f"Response body: {e.response.text}")
                # Log intuit_tid even in error responses
                intuit_tid = e.response.headers.get('intuit_tid')
                if intuit_tid:
                    logger.error(f"Balance Sheet Report API Error Response - intuit_tid: {intuit_tid}")
                else:
                    logger.error("Balance Sheet Report API Error Response - no intuit_tid found in headers")
            return None
    
    @staticmethod
    def format_balance_sheet(balance_sheet_data: Dict[str, Any]) -> str:
        """
        Format balance sheet data into a readable string
        
        Args:
            balance_sheet_data: Raw balance sheet data from QBO API
            
        Returns:
            Formatted string representation of the balance sheet
        """
        logger.info(f"Formatting balance sheet data: {len(balance_sheet_data)}")
        if not balance_sheet_data:
            logger.warning("No balance sheet data available")
            return "No balance sheet data available"
        
        def format_amount(amount_str: str) -> str:
            """Format amount string for display"""
            try:
                amount = float(amount_str)
                return f"${amount:,.2f}"
            except (ValueError, TypeError):
                return amount_str
        
        def process_rows(row_data, indent_level=0):
            """Process rows recursively with proper indentation"""
            if not row_data:
                return ""
            
            result = ""
            indent = "  " * indent_level
            
            # Handle different row data structures
            if isinstance(row_data, dict):
                # Single row object
                rows_to_process = [row_data]
            elif isinstance(row_data, list):
                # List of row objects
                rows_to_process = row_data
            else:
                return ""
            
            for row in rows_to_process:
                if not isinstance(row, dict):
                    continue
                
                row_type = row.get('type', '')
                
                if row_type == 'Section':
                    # Section header
                    header = row.get('Header', {})
                    col_data = header.get('ColData', [])
                    title = col_data[0].get('value', 'Unknown Section') if col_data else 'Unknown Section'
                    result += f"\n{indent}=== {title} ===\n"
                    
                    # Process subsections
                    if 'Rows' in row:
                        result += process_rows(row['Rows'], indent_level + 1)
                    
                    # Process summary
                    summary = row.get('Summary', {})
                    if summary:
                        summary_cols = summary.get('ColData', [])
                        if summary_cols:
                            summary_label = summary_cols[0].get('value', 'Total')
                            summary_amount = summary_cols[-1].get('value', '0') if len(summary_cols) > 1 else '0'
                            result += f"{indent}--- {summary_label}: {format_amount(summary_amount)} ---\n"
                
                elif row_type == 'Data':
                    # Data row
                    col_data = row.get('ColData', [])
                    if col_data:
                        # Get the first column (account name)
                        account_name = col_data[0].get('value', 'Unknown Account')
                        # Get the last column (amount)
                        amount = col_data[-1].get('value', '0') if len(col_data) > 1 else '0'
                        
                        result += f"{indent}{account_name}: {format_amount(amount)}\n"
                
                elif row_type == 'Total':
                    # Total row
                    col_data = row.get('ColData', [])
                    if col_data:
                        total_label = col_data[0].get('value', 'Total')
                        total_amount = col_data[-1].get('value', '0') if len(col_data) > 1 else '0'
                        
                        result += f"{indent}--- {total_label}: {format_amount(total_amount)} ---\n"
                
                # Handle nested Row structures
                if 'Row' in row:
                    result += process_rows(row['Row'], indent_level)
            
            return result
        
        # Extract report data
        header = balance_sheet_data.get('Header', {})
        report_name = header.get('ReportName', 'Balance Sheet')
        report_date = header.get('DateMacro', 'N/A')
        currency = header.get('Currency', 'USD')
        
        # Start building the formatted report
        formatted_report = f"""
{report_name}
Generated: {report_date}
Currency: {currency}
{'=' * 50}
"""
        
        # Process the main rows
        rows = balance_sheet_data.get('Rows', {})
        logger.info(f"Balance sheet rows structure: {len(rows)}")
        
        # Handle the Row structure from QuickBooks API
        if 'Row' in rows:
            formatted_report += process_rows(rows['Row'])
        else:
            formatted_report += process_rows(rows)
        
        return formatted_report 