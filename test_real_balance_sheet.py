#!/usr/bin/env python3
"""
Test the balance sheet formatting with real QuickBooks API data
"""

import unittest
from qbo_api import QuickBooksOnlineAPI

class TestRealBalanceSheetFormatting(unittest.TestCase):
    
    def setUp(self):
        """Set up test data with real QuickBooks API response"""
        self.real_balance_sheet_data = {
            'Header': {
                'Time': '2025-07-29T11:27:06-07:00',
                'ReportName': 'BalanceSheet',
                'DateMacro': 'this calendar year-to-date',
                'ReportBasis': 'Accrual',
                'StartPeriod': '2025-01-01',
                'EndPeriod': '2025-07-29',
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
                                            }
                                        ]
                                    },
                                    'Summary': {'ColData': [{'value': 'Total Current Assets'}, {'value': '9941.29'}]},
                                    'type': 'Section',
                                    'group': 'CurrentAssets'
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
                                                        }
                                                    ]
                                                },
                                                'Summary': {'ColData': [{'value': 'Total Current Liabilities'}, {'value': '6131.33'}]},
                                                'type': 'Section',
                                                'group': 'CurrentLiabilities'
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
    
    def test_format_real_balance_sheet(self):
        """Test formatting with real QuickBooks API data"""
        formatted = QuickBooksOnlineAPI.format_balance_sheet(self.real_balance_sheet_data)
        
        # Check that the formatted output contains expected sections
        self.assertIn('=== ASSETS ===', formatted)
        self.assertIn('=== Current Assets ===', formatted)
        self.assertIn('=== Bank Accounts ===', formatted)
        self.assertIn('=== LIABILITIES AND EQUITY ===', formatted)
        self.assertIn('=== Liabilities ===', formatted)
        self.assertIn('=== Current Liabilities ===', formatted)
        self.assertIn('=== Equity ===', formatted)
        
        # Check that account data is properly formatted
        self.assertIn('Checking: $1,201.00', formatted)
        self.assertIn('Savings: $800.00', formatted)
        self.assertIn('Accounts Receivable (A/R): $5,281.52', formatted)
        self.assertIn('Accounts Payable (A/P): $1,602.67', formatted)
        self.assertIn('Opening Balance Equity: $-9,337.50', formatted)
        self.assertIn('Net Income: $1,642.46', formatted)
        
        # Check that totals are properly formatted
        self.assertIn('--- Total Bank Accounts: $2,001.00 ---', formatted)
        self.assertIn('--- Total Accounts Receivable: $5,281.52 ---', formatted)
        self.assertIn('--- Total Current Assets: $9,941.29 ---', formatted)
        self.assertIn('--- Total Accounts Payable: $1,602.67 ---', formatted)
        self.assertIn('--- Total Current Liabilities: $6,131.33 ---', formatted)
        self.assertIn('--- Total Liabilities: $31,131.33 ---', formatted)
        self.assertIn('--- Total Equity: $-7,695.04 ---', formatted)
        self.assertIn('--- TOTAL ASSETS: $23,436.29 ---', formatted)
        self.assertIn('--- TOTAL LIABILITIES AND EQUITY: $23,436.29 ---', formatted)
        
        # Verify the output is substantial (adjusted for test data size)
        self.assertGreater(len(formatted), 800)
        print(f"✅ Formatted report length: {len(formatted)} characters")
        print("✅ All expected sections and amounts found in formatted output")

if __name__ == '__main__':
    unittest.main() 