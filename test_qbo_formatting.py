#!/usr/bin/env python3
"""
Unit tests for QBO API formatting functions
"""

import unittest
import json
import sys
import os

# Add the parent directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from qbo_balance_sheet_getter import QBOBalanceSheetGetter


class TestQBOFormatting(unittest.TestCase):
    """Test cases for QBO API formatting functions"""
    
    def setUp(self):
        """Set up test data"""
        # Sample QBO Balance Sheet API response based on actual data
        self.sample_balance_sheet_data = {
            'Header': {
                'Time': '2025-07-28T12:40:48-07:00',
                'ReportName': 'BalanceSheet',
                'DateMacro': 'this calendar year-to-date',
                'ReportBasis': 'Accrual',
                'StartPeriod': '2025-01-01',
                'EndPeriod': '2025-07-28',
                'SummarizeColumnsBy': 'Total',
                'Currency': 'USD',
                'Option': [
                    {'Name': 'AccountingStandard', 'Value': 'GAAP'},
                    {'Name': 'NoReportData', 'Value': 'false'}
                ]
            },
            'Columns': {
                'Column': [
                    {'ColTitle': '', 'ColType': 'Account', 'MetaData': [{'Name': 'ColKey', 'Value': 'account'}]},
                    {'ColTitle': 'Total', 'ColType': 'Money', 'MetaData': [{'Name': 'ColKey', 'Value': 'total'}]}
                ]
            },
            'Rows': {
                'Row': [
                    {
                        'Header': {'ColData': [{'value': 'ASSETS'}, {'value': ''}]},
                        'Rows': {
                            'Row': [
                                {
                                    'Header': {'ColData': [{'value': 'Current Assets'}, {'value': ''}]},
                                    'Rows': {
                                        'Row': [
                                            {
                                                'Header': {'ColData': [{'value': 'Bank Accounts'}, {'value': ''}]},
                                                'Rows': {
                                                    'Row': [
                                                        {'ColData': [{'value': 'Checking', 'id': '35'}, {'value': '1201.00'}], 'type': 'Data'},
                                                        {'ColData': [{'value': 'Savings', 'id': '36'}, {'value': '800.00'}], 'type': 'Data'}
                                                    ]
                                                },
                                                'Summary': {'ColData': [{'value': 'Total Bank Accounts'}, {'value': '2001.00'}]},
                                                'type': 'Section',
                                                'group': 'BankAccounts'
                                            },
                                            {
                                                'Header': {'ColData': [{'value': 'Accounts Receivable'}, {'value': ''}]},
                                                'Rows': {
                                                    'Row': [
                                                        {'ColData': [{'value': 'Accounts Receivable (A/R)', 'id': '84'}, {'value': '5281.52'}], 'type': 'Data'}
                                                    ]
                                                },
                                                'Summary': {'ColData': [{'value': 'Total Accounts Receivable'}, {'value': '5281.52'}]},
                                                'type': 'Section',
                                                'group': 'AR'
                                            },
                                            {
                                                'Header': {'ColData': [{'value': 'Other Current Assets'}, {'value': ''}]},
                                                'Rows': {
                                                    'Row': [
                                                        {'ColData': [{'value': 'Inventory Asset', 'id': '81'}, {'value': '596.25'}], 'type': 'Data'},
                                                        {'ColData': [{'value': 'Undeposited Funds', 'id': '4'}, {'value': '2062.52'}], 'type': 'Data'}
                                                    ]
                                                },
                                                'Summary': {'ColData': [{'value': 'Total Other Current Assets'}, {'value': '2658.77'}]},
                                                'type': 'Section',
                                                'group': 'OtherCurrentAssets'
                                            }
                                        ]
                                    },
                                    'Summary': {'ColData': [{'value': 'Total Current Assets'}, {'value': '9941.29'}]},
                                    'type': 'Section',
                                    'group': 'CurrentAssets'
                                },
                                {
                                    'Header': {'ColData': [{'value': 'Fixed Assets'}, {'value': ''}]},
                                    'Rows': {
                                        'Row': [
                                            {
                                                'Header': {'ColData': [{'value': 'Truck', 'id': '37'}, {'value': ''}]},
                                                'Rows': {
                                                    'Row': [
                                                        {'ColData': [{'value': 'Original Cost', 'id': '38'}, {'value': '13495.00'}], 'type': 'Data'}
                                                    ]
                                                },
                                                'Summary': {'ColData': [{'value': 'Total Truck'}, {'value': '13495.00'}]},
                                                'type': 'Section'
                                            }
                                        ]
                                    },
                                    'Summary': {'ColData': [{'value': 'Total Fixed Assets'}, {'value': '13495.00'}]},
                                    'type': 'Section',
                                    'group': 'FixedAssets'
                                }
                            ]
                        },
                        'Summary': {'ColData': [{'value': 'TOTAL ASSETS'}, {'value': '23436.29'}]},
                        'type': 'Section',
                        'group': 'TotalAssets'
                    },
                    {
                        'Header': {'ColData': [{'value': 'LIABILITIES AND EQUITY'}, {'value': ''}]},
                        'Rows': {
                            'Row': [
                                {
                                    'Header': {'ColData': [{'value': 'Liabilities'}, {'value': ''}]},
                                    'Rows': {
                                        'Row': [
                                            {
                                                'Header': {'ColData': [{'value': 'Current Liabilities'}, {'value': ''}]},
                                                'Rows': {
                                                    'Row': [
                                                        {
                                                            'Header': {'ColData': [{'value': 'Accounts Payable'}, {'value': ''}]},
                                                            'Rows': {
                                                                'Row': [
                                                                    {'ColData': [{'value': 'Accounts Payable (A/P)', 'id': '33'}, {'value': '1602.67'}], 'type': 'Data'}
                                                                ]
                                                            },
                                                            'Summary': {'ColData': [{'value': 'Total Accounts Payable'}, {'value': '1602.67'}]},
                                                            'type': 'Section',
                                                            'group': 'AP'
                                                        },
                                                        {
                                                            'Header': {'ColData': [{'value': 'Credit Cards'}, {'value': ''}]},
                                                            'Rows': {
                                                                'Row': [
                                                                    {'ColData': [{'value': 'Mastercard', 'id': '41'}, {'value': '157.72'}], 'type': 'Data'}
                                                                ]
                                                            },
                                                            'Summary': {'ColData': [{'value': 'Total Credit Cards'}, {'value': '157.72'}]},
                                                            'type': 'Section',
                                                            'group': 'CreditCards'
                                                        },
                                                        {
                                                            'Header': {'ColData': [{'value': 'Other Current Liabilities'}, {'value': ''}]},
                                                            'Rows': {
                                                                'Row': [
                                                                    {'ColData': [{'value': 'Arizona Dept. of Revenue Payable', 'id': '89'}, {'value': '0.00'}], 'type': 'Data'},
                                                                    {'ColData': [{'value': 'Board of Equalization Payable', 'id': '90'}, {'value': '370.94'}], 'type': 'Data'},
                                                                    {'ColData': [{'value': 'Loan Payable', 'id': '43'}, {'value': '4000.00'}], 'type': 'Data'}
                                                                ]
                                                            },
                                                            'Summary': {'ColData': [{'value': 'Total Other Current Liabilities'}, {'value': '4370.94'}]},
                                                            'type': 'Section',
                                                            'group': 'OtherCurrentLiabilities'
                                                        }
                                                    ]
                                                },
                                                'Summary': {'ColData': [{'value': 'Total Current Liabilities'}, {'value': '6131.33'}]},
                                                'type': 'Section',
                                                'group': 'CurrentLiabilities'
                                            },
                                            {
                                                'Header': {'ColData': [{'value': 'Long-Term Liabilities'}, {'value': ''}]},
                                                'Rows': {
                                                    'Row': [
                                                        {'ColData': [{'value': 'Notes Payable', 'id': '44'}, {'value': '25000.00'}], 'type': 'Data'}
                                                    ]
                                                },
                                                'Summary': {'ColData': [{'value': 'Total Long-Term Liabilities'}, {'value': '25000.00'}]},
                                                'type': 'Section',
                                                'group': 'LongTermLiabilities'
                                            }
                                        ]
                                    },
                                    'Summary': {'ColData': [{'value': 'Total Liabilities'}, {'value': '31131.33'}]},
                                    'type': 'Section',
                                    'group': 'Liabilities'
                                },
                                {
                                    'Header': {'ColData': [{'value': 'Equity'}, {'value': ''}]},
                                    'Rows': {
                                        'Row': [
                                            {'ColData': [{'value': 'Opening Balance Equity', 'id': '34'}, {'value': '-9337.50'}], 'type': 'Data'},
                                            {'ColData': [{'value': 'Retained Earnings', 'id': '2'}, {'value': ''}], 'type': 'Data'},
                                            {'ColData': [{'value': 'Net Income'}, {'value': '1642.46'}], 'type': 'Data', 'group': 'NetIncome'}
                                        ]
                                    },
                                    'Summary': {'ColData': [{'value': 'Total Equity'}, {'value': '-7695.04'}]},
                                    'type': 'Section',
                                    'group': 'Equity'
                                }
                            ]
                        },
                        'Summary': {'ColData': [{'value': 'TOTAL LIABILITIES AND EQUITY'}, {'value': '23436.29'}]},
                        'type': 'Section',
                        'group': 'TotalLiabilitiesAndEquity'
                    }
                ]
            }
        }
    
    def test_format_balance_sheet_with_valid_data(self):
        """Test formatting balance sheet with valid QBO API response"""
        formatted = QBOBalanceSheetGetter.format_balance_sheet(self.sample_balance_sheet_data)
        
        # Verify the formatted output contains expected sections
        self.assertIn('BalanceSheet', formatted)
        self.assertIn('this calendar year-to-date', formatted)
        self.assertIn('USD', formatted)
        self.assertIn('ASSETS', formatted)
        self.assertIn('LIABILITIES AND EQUITY', formatted)
        
        # Verify specific account data is present
        self.assertIn('Checking: $1,201.00', formatted)
        self.assertIn('Savings: $800.00', formatted)
        self.assertIn('Total Bank Accounts: $2,001.00', formatted)
        self.assertIn('Accounts Receivable (A/R): $5,281.52', formatted)
        self.assertIn('Total Current Assets: $9,941.29', formatted)
        self.assertIn('TOTAL ASSETS: $23,436.29', formatted)
        
        # Verify liabilities and equity
        self.assertIn('Accounts Payable (A/P): $1,602.67', formatted)
        self.assertIn('Total Current Liabilities: $6,131.33', formatted)
        self.assertIn('Opening Balance Equity: $-9,337.50', formatted)
        self.assertIn('Net Income: $1,642.46', formatted)
        self.assertIn('TOTAL LIABILITIES AND EQUITY: $23,436.29', formatted)
        
        # Verify the output is substantial (not truncated)
        self.assertGreater(len(formatted), 1000)
    
    def test_format_balance_sheet_with_empty_data(self):
        """Test formatting balance sheet with empty data"""
        formatted = QBOBalanceSheetGetter.format_balance_sheet({})
        self.assertEqual(formatted, "No balance sheet data available")
        
        formatted = QBOBalanceSheetGetter.format_balance_sheet(None)
        self.assertEqual(formatted, "No balance sheet data available")
    
    def test_format_balance_sheet_with_missing_rows(self):
        """Test formatting balance sheet with missing rows structure"""
        data_without_rows = {
            'Header': {'ReportName': 'BalanceSheet', 'Currency': 'USD'},
            'Columns': {'Column': []}
        }
        formatted = QBOBalanceSheetGetter.format_balance_sheet(data_without_rows)
        self.assertIn('BalanceSheet', formatted)
        self.assertIn('USD', formatted)
    
    def test_format_balance_sheet_with_empty_rows(self):
        """Test formatting balance sheet with empty rows"""
        data_with_empty_rows = {
            'Header': {'ReportName': 'BalanceSheet', 'Currency': 'USD'},
            'Columns': {'Column': []},
            'Rows': {}
        }
        formatted = QBOBalanceSheetGetter.format_balance_sheet(data_with_empty_rows)
        self.assertIn('BalanceSheet', formatted)
        self.assertIn('USD', formatted)
    
    def test_format_balance_sheet_amount_formatting(self):
        """Test that amounts are properly formatted"""
        formatted = QBOBalanceSheetGetter.format_balance_sheet(self.sample_balance_sheet_data)
        
        # Test positive amounts
        self.assertIn('$1,201.00', formatted)
        self.assertIn('$5,281.52', formatted)
        
        # Test negative amounts
        self.assertIn('$-9,337.50', formatted)
        
        # Test zero amounts
        self.assertIn('$0.00', formatted)
    
    def test_format_balance_sheet_structure(self):
        """Test that the formatted output has proper structure"""
        formatted = QBOBalanceSheetGetter.format_balance_sheet(self.sample_balance_sheet_data)
        
        # Check for proper section headers
        self.assertIn('=== ASSETS ===', formatted)
        self.assertIn('=== Current Assets ===', formatted)
        self.assertIn('=== Bank Accounts ===', formatted)
        self.assertIn('=== LIABILITIES AND EQUITY ===', formatted)
        
        # Check for proper totals
        self.assertIn('--- Total Bank Accounts: $2,001.00 ---', formatted)
        self.assertIn('--- Total Current Assets: $9,941.29 ---', formatted)
        self.assertIn('--- TOTAL ASSETS: $23,436.29 ---', formatted)
    
    def test_format_balance_sheet_nested_structure(self):
        """Test that nested structures are properly handled"""
        formatted = QBOBalanceSheetGetter.format_balance_sheet(self.sample_balance_sheet_data)
        
        # Verify nested account structure is preserved
        lines = formatted.split('\n')
        
        # Check that we have proper indentation for nested accounts
        checking_line = None
        savings_line = None
        total_bank_line = None
        
        for line in lines:
            if 'Checking:' in line:
                checking_line = line
            elif 'Savings:' in line:
                savings_line = line
            elif 'Total Bank Accounts:' in line:
                total_bank_line = line
        
        # Verify the structure makes sense
        self.assertIsNotNone(checking_line)
        self.assertIsNotNone(savings_line)
        self.assertIsNotNone(total_bank_line)
        
        # Verify indentation (nested accounts should be indented)
        self.assertIn('  Checking:', checking_line)
        self.assertIn('  Savings:', savings_line)
        self.assertIn('  --- Total Bank Accounts:', total_bank_line)


if __name__ == '__main__':
    unittest.main() 