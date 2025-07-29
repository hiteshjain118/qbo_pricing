import requests
import json
from datetime import datetime, timedelta
import os
from typing import Dict, Any
import logging
from logging_config import setup_logging
from qbo_request_auth_params import QBORequestAuthParams

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

class QuickBooksOnlineAPI:
    """
    QuickBooks Online API client for querying reports
    """
    
    def __init__(self, params: QBORequestAuthParams, realm_id: str, access_token: str):
        """
        Initialize QBO API client
        
        Args:
            params: QBORequestAuthParams object containing client_id, client_secret, access_token, and base_url
        """
        self.params = params
        self.realm_id = realm_id
        self.access_token = access_token

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
        url = f"{self.params.qbo_base_url}/{self.params.api_version}/company/{self.realm_id}/reports/ProfitAndLoss"
        
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
            
        url = f"{self.params.qbo_base_url}/{self.params.api_version}/company/{self.realm_id}/reports/BalanceSheet"
        
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
        """Format balance sheet data into a readable string"""
        # Handle empty or None data
        if not balance_sheet_data or balance_sheet_data is None:
            return "No balance sheet data available"
            
        logger.info(f"Formatting balance sheet data: {len(str(balance_sheet_data))} characters")
        
        def format_amount(amount_str: str) -> str:
            """Format amount string to currency format"""
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
                
                # Handle Header sections (main sections like ASSETS, LIABILITIES AND EQUITY)
                if 'Header' in row and 'ColData' in row['Header']:
                    header_cols = row['Header']['ColData']
                    if header_cols and header_cols[0].get('value'):
                        title = header_cols[0]['value']
                        result += f"\n{indent}=== {title} ===\n"
                
                # Handle Data rows (actual account entries)
                if 'ColData' in row and 'type' in row and row['type'] == 'Data':
                    col_data = row['ColData']
                    if col_data:
                        account_name = col_data[0].get('value', 'Unknown Account')
                        amount = col_data[-1].get('value', '0') if len(col_data) > 1 else '0'
                        result += f"{indent}{account_name}: {format_amount(amount)}\n"
                
                # Handle Summary rows (totals)
                if 'Summary' in row and 'ColData' in row['Summary']:
                    summary_cols = row['Summary']['ColData']
                    if summary_cols:
                        summary_label = summary_cols[0].get('value', 'Total')
                        summary_amount = summary_cols[-1].get('value', '0') if len(summary_cols) > 1 else '0'
                        result += f"{indent}--- {summary_label}: {format_amount(summary_amount)} ---\n"
                
                # Process nested Rows
                if 'Rows' in row:
                    nested_rows = row['Rows']
                    if 'Row' in nested_rows:
                        result += process_rows(nested_rows['Row'], indent_level + 1)
                    else:
                        result += process_rows(nested_rows, indent_level + 1)
            
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
        
        logger.info(f"Formatted report length: {len(formatted_report)} characters")
        return formatted_report 