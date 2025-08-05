import unittest
from unittest.mock import Mock, patch
import pandas as pd
import json
import os
import sys

# Add parent directories to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from intent_servers.purchase_transactions_server import PurchaseTransactionsServer
from retrievers.iretriever import IRetriever
from retrievers.qb_file_retriever import QBFileRetriever


class TestPurchaseTransactionsServer(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures"""
        self.mock_retriever = Mock(spec=IRetriever)
        self.purchase_transactions_server = PurchaseTransactionsServer(self.mock_retriever)
        
        # Load mock data from file - use only the first line since it's JSONL format
        # Use absolute path from current working directory
        current_dir = os.getcwd()
        mock_file_path = os.path.join(current_dir, 'retrievers', 'tests', 'mock_purchase_transactions_response.jsonl')
        with open(mock_file_path, 'r') as f:
            # The mock data is double-escaped, so we need to parse it twice
            raw_line = f.readline().strip()
            # Parse the double-escaped JSON string to get the actual data
            parsed_once = json.loads(raw_line)
            self.mock_purchase_transactions_data = json.loads(parsed_once)

    def test_init(self):
        """Test PurchaseTransactionsServer initialization"""
        self.assertEqual(self.purchase_transactions_server.qb_purchase_transactions_retriever, self.mock_retriever)

    def test_extract_cols_with_valid_data(self):
        """Test extracting columns from valid purchase transactions response using mock file data"""
        # The mock data is already parsed as a dictionary, pass it directly
        mock_response = self.mock_purchase_transactions_data
        
        result = self.purchase_transactions_server._extract_cols(mock_response)
        
        self.assertIsInstance(result, pd.DataFrame)
        # The mock data contains multiple transactions, so we should have multiple rows
        self.assertGreater(len(result), 0)
        self.assertEqual(list(result.columns), ['product_name', 'purchase_quantity', 'purchase_price', 'purchase_amount', 'purchase_transaction_date'])
        
        # Check that we have valid data
        self.assertTrue(all(result['product_name'].notna()))
        self.assertTrue(all(result['purchase_quantity'] > 0))
        self.assertTrue(all(result['purchase_amount'] >= 0))
        self.assertTrue(all(result['purchase_price'] >= 0))

    def test_extract_cols_with_missing_fields(self):
        """Test extracting columns when some fields are missing"""
        mock_response = {
            "QueryResponse": {
                "Bill": [
                    {
                        "Line": [
                            {
                                "ItemBasedExpenseLineDetail": {
                                    "ItemRef": {"name": "Test Product"},
                                    "Qty": 10,
                                    "UnitPrice": 5.0
                                },
                                "Amount": 50.0
                            },
                            {
                                "ItemBasedExpenseLineDetail": {
                                    "ItemRef": {"name": "Unknown Item"},  # This should be skipped
                                    "Qty": 0,  # This should be skipped
                                    "UnitPrice": 0.0  # This should be skipped
                                },
                                "Amount": 0.0  # This should be skipped
                            },
                            {
                                "ItemBasedExpenseLineDetail": {
                                    "ItemRef": {"name": "Valid Product"},
                                    "Qty": 5,
                                    "UnitPrice": 10.0
                                },
                                "Amount": 50.0
                            }
                        ],
                        "TxnDate": "2025-07-31"
                    }
                ]
            }
        }
        
        result = self.purchase_transactions_server._extract_cols(mock_response)
        
        self.assertIsInstance(result, pd.DataFrame)
        # Only valid products should be included
        self.assertEqual(len(result), 2)
        product_names = result['product_name'].tolist()
        self.assertIn('Test Product', product_names)
        self.assertIn('Valid Product', product_names)

    def test_extract_cols_with_missing_item_detail(self):
        """Test extracting columns when ItemBasedExpenseLineDetail is missing"""
        mock_response = {
            "QueryResponse": {
                "Bill": [
                    {
                        "Line": [
                            {
                                "DetailType": "ItemBasedExpenseLineDetail",
                                # Missing ItemBasedExpenseLineDetail
                                "Amount": 50.0
                            }
                        ],
                        "TxnDate": "2025-07-31"
                    }
                ]
            }
        }
        
        result = self.purchase_transactions_server._extract_cols(mock_response)
        
        self.assertIsInstance(result, pd.DataFrame)
        # Should be empty since no valid line items
        self.assertEqual(len(result), 0)

    def test_extract_cols_with_empty_response(self):
        """Test extracting columns from empty response"""
        mock_response = {
            "QueryResponse": {
                "Bill": []
            }
        }
        
        result = self.purchase_transactions_server._extract_cols(mock_response)
        
        self.assertIsInstance(result, pd.DataFrame)
        self.assertEqual(len(result), 0)
        # When DataFrame is empty, it may not have columns set
        if len(result.columns) > 0:
            self.assertEqual(list(result.columns), ['product_name', 'purchase_quantity', 'purchase_price', 'purchase_amount', 'purchase_transaction_date'])

    def test_extract_cols_with_invalid_json(self):
        """Test extracting columns with invalid JSON"""
        with self.assertRaises(TypeError):
            self.purchase_transactions_server._extract_cols("invalid json")

    def test_describe_for_logging(self):
        """Test the _describe_for_logging method"""
        # Create test DataFrame
        test_data = {
            'product_name': ['Product A', 'Product B', 'Product C'],
            'quantity': [10, 20, 15],
            'rate': [5.0, 10.0, 7.5],
            'amount': [50.0, 200.0, 112.5],
            'transaction_date': ['2025-07-31', '2025-07-31', '2025-07-31']
        }
        test_df = pd.DataFrame(test_data)
        
        result = self.purchase_transactions_server._describe_for_logging(test_df)
        
        self.assertIsInstance(result, str)
        self.assertIn('Got total:#3 purchase transactions', result)

    def test_describe_for_logging_empty_dataframe(self):
        """Test the _describe_for_logging method with empty DataFrame"""
        empty_df = pd.DataFrame()
        
        result = self.purchase_transactions_server._describe_for_logging(empty_df)
        
        self.assertIsInstance(result, str)
        self.assertIn('Got total:#0 purchase transactions', result)

    def test_serve_with_valid_responses(self):
        """Test serve method with valid responses"""
        # Mock the retriever to return our mock data as dictionaries
        self.mock_retriever.retrieve.return_value = [self.mock_purchase_transactions_data]
        
        result = self.purchase_transactions_server.serve()
        
        self.assertIsInstance(result, pd.DataFrame)
        self.assertGreater(len(result), 0)
        self.assertEqual(list(result.columns), ['product_name', 'purchase_quantity', 'purchase_price', 'purchase_amount', 'purchase_transaction_date'])
        
        # Verify retriever was called
        self.mock_retriever.retrieve.assert_called_once()

    def test_serve_with_empty_responses(self):
        """Test serve method with empty responses"""
        self.mock_retriever.retrieve.return_value = []
        
        result = self.purchase_transactions_server.serve()
        
        self.assertIsInstance(result, pd.DataFrame)
        self.assertEqual(len(result), 0)
        # When DataFrame is empty, it may not have columns set
        if len(result.columns) > 0:
            self.assertEqual(list(result.columns), ['product_name', 'purchase_quantity', 'purchase_price', 'purchase_amount', 'purchase_transaction_date'])

    def test_serve_with_retriever_exception(self):
        """Test serve method when retriever raises an exception"""
        self.mock_retriever.retrieve.side_effect = Exception("API Error")
        
        with self.assertRaises(Exception):
            self.purchase_transactions_server.serve()

    def test_serve_with_invalid_response_format(self):
        """Test serve method with invalid response format"""
        self.mock_retriever.retrieve.return_value = ["invalid json"]
        
        with self.assertRaises(TypeError):
            self.purchase_transactions_server.serve()

    def test_extract_cols_with_valid_data_but_zero_values(self):
        """Test extracting columns with valid data but zero values that should be filtered out"""
        mock_response = {
            "QueryResponse": {
                "Bill": [
                    {
                        "Line": [
                            {
                                "ItemBasedExpenseLineDetail": {
                                    "ItemRef": {"name": "Product with Zero Values"},
                                    "Qty": 0,  # Should be filtered out
                                    "UnitPrice": 0.0  # Should be filtered out
                                },
                                "Amount": 0.0  # Should be filtered out
                            }
                        ],
                        "TxnDate": "2025-07-31"
                    }
                ]
            }
        }
        
        result = self.purchase_transactions_server._extract_cols(mock_response)
        
        self.assertIsInstance(result, pd.DataFrame)
        # Should be empty since all values are zero
        self.assertEqual(len(result), 0)

    def test_with_file_retriever(self):
        """Test PurchaseTransactionsServer with QBFileRetriever using mock file"""
        # Create a file retriever with the mock file
        # Use absolute path from current working directory
        current_dir = os.getcwd()
        mock_file_path = os.path.join(current_dir, 'retrievers', 'tests', 'mock_purchase_transactions_response.jsonl')
        file_retriever = QBFileRetriever(mock_file_path)
        purchase_transactions_server = PurchaseTransactionsServer(file_retriever)
        
        result = purchase_transactions_server.serve()
        
        self.assertIsInstance(result, pd.DataFrame)
        self.assertGreater(len(result), 0)
        self.assertEqual(list(result.columns), ['product_name', 'purchase_quantity', 'purchase_price', 'purchase_amount', 'purchase_transaction_date'])


if __name__ == '__main__':
    unittest.main() 