import unittest
from unittest.mock import Mock, patch
import pandas as pd
import json
import os
import sys

# Add parent directories to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from intent_servers.pricing_delta_server import PricingDeltaServer
from retrievers.iretriever import IRetriever
from retrievers.qb_file_retriever import QBFileRetriever
from intent_servers.inventory_server import InventoryServer
from intent_servers.purchase_transactions_server import PurchaseTransactionsServer


class TestPricingDeltaServer(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures"""
        self.mock_inventory_retriever = Mock(spec=IRetriever)
        self.mock_purchase_transactions_retriever = Mock(spec=IRetriever)
        self.mock_email_sender = Mock()
        
        # Create mock servers
        self.mock_inventory_server = Mock(spec=InventoryServer)
        self.mock_purchase_transactions_server = Mock(spec=PurchaseTransactionsServer)
        
        self.pricing_delta_server = PricingDeltaServer(
            purchase_transactions_server=self.mock_purchase_transactions_server,
            inventory_server=self.mock_inventory_server,
            realm_id="test_realm",
            email_sender=self.mock_email_sender
        )
        
        # Load mock data from files - use only the first line since it's JSONL format
        # Use absolute paths from current working directory
        current_dir = os.getcwd()
        mock_inventory_file_path = os.path.join(current_dir, 'retrievers', 'tests', 'mock_inventory_response.jsonl')
        with open(mock_inventory_file_path, 'r') as f:
            # The mock data is double-escaped, so we need to parse it twice
            raw_line = f.readline().strip()
            # Parse the double-escaped JSON string to get the actual data
            parsed_once = json.loads(raw_line)
            self.mock_inventory_data = json.loads(parsed_once)
            
        mock_purchase_file_path = os.path.join(current_dir, 'retrievers', 'tests', 'mock_purchase_transactions_response.jsonl')
        with open(mock_purchase_file_path, 'r') as f:
            # The mock data is double-escaped, so we need to parse it twice
            raw_line = f.readline().strip()
            # Parse the double-escaped JSON string to get the actual data
            parsed_once = json.loads(raw_line)
            self.mock_purchase_transactions_data = json.loads(parsed_once)

    def test_init(self):
        """Test PricingDeltaServer initialization"""
        self.assertEqual(self.pricing_delta_server.purchase_transactions_server, self.mock_purchase_transactions_server)
        self.assertEqual(self.pricing_delta_server.inventory_server, self.mock_inventory_server)
        self.assertEqual(self.pricing_delta_server.realm_id, "test_realm")
        self.assertEqual(self.pricing_delta_server.email_sender, self.mock_email_sender)

    def test_init_with_api_retrievers(self):
        """Test static factory method init_with_api_retrievers"""
        # Create mock auth params
        mock_auth_params = Mock()
        
        server = PricingDeltaServer.init_with_api_retrievers(
            auth_params=mock_auth_params,
            realm_id="test_realm",
            email="test@example.com"
        )
        
        self.assertIsInstance(server, PricingDeltaServer)
        self.assertIsNotNone(server.inventory_server)
        self.assertIsNotNone(server.purchase_transactions_server)
        self.assertIsNotNone(server.email_sender)
        self.assertEqual(server.realm_id, "test_realm")

    def test_init_with_file_retrievers(self):
        """Test static factory method init_with_file_retrievers"""
        server = PricingDeltaServer.init_with_file_retrievers(
            inventory_file_path="test_inventory.jsonl",
            purchase_transactions_file_path="test_purchase.jsonl",
            realm_id="test_realm",
            email="test@example.com"
        )
        
        self.assertIsInstance(server, PricingDeltaServer)
        self.assertIsInstance(server.inventory_server.qb_inventory_retriever, QBFileRetriever)
        self.assertIsInstance(server.purchase_transactions_server.qb_purchase_transactions_retriever, QBFileRetriever)
        self.assertIsNotNone(server.email_sender)
        self.assertEqual(server.realm_id, "test_realm")

    def test_extract_inventory_cols_with_valid_data(self):
        """Test extracting inventory columns from valid response using mock file data"""
        # This method doesn't exist on PricingDeltaServer, it's on InventoryServer
        # Test the inventory server's extract_cols method instead
        inventory_server = InventoryServer(self.mock_inventory_retriever)
        # The mock data is already parsed as a dictionary, pass it directly
        mock_response = self.mock_inventory_data
    
        result = inventory_server._extract_cols(mock_response)
    
        self.assertIsInstance(result, pd.DataFrame)
        # The mock data contains multiple items, so we should have multiple rows
        self.assertGreater(len(result), 0)
        self.assertEqual(list(result.columns), ['product_name', 'inventory_price'])
        
        # Check that we have valid product names and prices
        self.assertTrue(all(result['product_name'].notna()))
        self.assertTrue(all(result['inventory_price'] >= 0))

    def test_extract_purchase_columns_with_valid_data(self):
        """Test extracting purchase columns from valid response using mock file data"""
        # This method doesn't exist on PricingDeltaServer, it's on PurchaseTransactionsServer
        # Test the purchase transactions server's extract_cols method instead
        purchase_transactions_server = PurchaseTransactionsServer(self.mock_purchase_transactions_retriever)
        # The mock data is already parsed as a dictionary, pass it directly
        mock_response = self.mock_purchase_transactions_data
    
        result = purchase_transactions_server._extract_cols(mock_response)
    
        self.assertIsInstance(result, pd.DataFrame)
        # The mock data contains multiple transactions, so we should have multiple rows
        self.assertGreater(len(result), 0)
        self.assertEqual(list(result.columns), ['product_name', 'purchase_quantity', 'purchase_price', 'purchase_amount', 'purchase_transaction_date'])
        
        # Check that we have valid data
        self.assertTrue(all(result['product_name'].notna()))
        self.assertTrue(all(result['purchase_quantity'] > 0))
        self.assertTrue(all(result['purchase_amount'] >= 0))
        self.assertTrue(all(result['purchase_price'] >= 0))

    def test_get_pricing_delta_with_matching_products(self):
        """Test get_pricing_delta with products that match between inventory and purchase data"""
        # Create test data with matching product names
        inventory_df = pd.DataFrame({
            'product_name': ['Product A', 'Product B', 'Product C'],
            'inventory_price': [10.0, 20.0, 30.0]
        })

        purchase_df = pd.DataFrame({
            'product_name': ['Product A', 'Product B', 'Product D'],
            'purchase_quantity': [5, 10, 15],
            'purchase_amount': [45.0, 180.0, 300.0],
            'purchase_price': [9.0, 18.0, 20.0]
        })
        
        # Mock the servers to return our test data
        self.mock_inventory_server.serve.return_value = inventory_df
        self.mock_purchase_transactions_server.serve.return_value = purchase_df
        
        result = self.pricing_delta_server.get_pricing_delta()
        
        self.assertIsInstance(result, pd.DataFrame)
        # Left join should include all purchase transactions (3 total)
        # Product A and B have matching inventory, Product D doesn't
        self.assertEqual(len(result), 3)
        self.assertIn('Product A', result['product_name'].values)
        self.assertIn('Product B', result['product_name'].values)
        self.assertIn('Product D', result['product_name'].values)

    def test_get_pricing_delta_with_no_matches(self):
        """Test get_pricing_delta with no matching products"""
        inventory_df = pd.DataFrame({
            'product_name': ['Product A', 'Product B'],
            'inventory_price': [10.0, 20.0]
        })

        purchase_df = pd.DataFrame({
            'product_name': ['Product C', 'Product D'],
            'purchase_quantity': [5, 10],
            'purchase_amount': [45.0, 180.0],
            'purchase_price': [9.0, 18.0]
        })
        
        # Mock the servers to return our test data
        self.mock_inventory_server.serve.return_value = inventory_df
        self.mock_purchase_transactions_server.serve.return_value = purchase_df
        
        result = self.pricing_delta_server.get_pricing_delta()
        
        self.assertIsInstance(result, pd.DataFrame)
        # Left join should include all purchase transactions (2 total)
        # Even though no products match, the left join includes all purchase transactions
        self.assertEqual(len(result), 2)
        self.assertIn('Product C', result['product_name'].values)
        self.assertIn('Product D', result['product_name'].values)

    def test_get_pricing_delta_with_empty_dataframes(self):
        """Test get_pricing_delta with empty DataFrames"""
        # Mock the servers to return empty DataFrames
        self.mock_inventory_server.serve.return_value = pd.DataFrame()
        self.mock_purchase_transactions_server.serve.return_value = pd.DataFrame()
        
        result = self.pricing_delta_server.get_pricing_delta()
        
        self.assertIsInstance(result, pd.DataFrame)
        self.assertTrue(result.empty)

    def test_format_pricing_delta_to_html_with_valid_data(self):
        """Test format_pricing_delta_to_html with valid data"""
        test_df = pd.DataFrame({
            'product_name': ['Product A', 'Product B'],
            'inventory_price': [10.0, 20.0],
            'purchase_quantity': [5, 10],
            'purchase_amount': [45.0, 180.0],
            'purchase_price': [9.0, 18.0],
            'purchase_transaction_date': ['2025-01-01', '2025-01-02'],  # Add missing column
            'pricing_delta': [1.0, 2.0],
            'pricing_perc_delta': [11.11, 11.11]
        })
    
        html_table, excel_data = self.pricing_delta_server.format_pricing_delta_to_html(test_df)
        
        # Check that HTML table is generated
        self.assertIsInstance(html_table, str)
        self.assertGreater(len(html_table), 0)
        
        # Check that Excel data is generated
        self.assertIsInstance(excel_data, str)
        self.assertGreater(len(excel_data), 0)

    def test_format_pricing_delta_to_html_empty_dataframe(self):
        """Test format_pricing_delta_to_html with empty DataFrame"""
        empty_df = pd.DataFrame()
        
        html_table, excel_data = self.pricing_delta_server.format_pricing_delta_to_html(empty_df)
        
        self.assertEqual(html_table, '')
        self.assertEqual(excel_data, '')

    def test_describe_for_logging(self):
        """Test the _describe_for_logging method"""
        test_df = pd.DataFrame({
            'product_name': ['Product A', 'Product B'],
            'inventory_price': [10.0, None],  # One NaN value
            'purchase_quantity': [5, 10],
            'purchase_amount': [45.0, 180.0],
            'purchase_price': [9.0, 18.0],
            'pricing_perc_delta': [11.11, 11.11],
            'matched': ['both', 'left_only']  # Add the matched column
        })
    
        result = self.pricing_delta_server._describe_for_logging(test_df)
        self.assertIn("Pricing delta total rows: 2", result)
        self.assertIn("w/ nan inventory price: 1", result)
        self.assertIn("products with nan inventory price: ['Product B']", result)

    def test_describe_for_logging_empty_dataframe(self):
        """Test the _describe_for_logging method with empty DataFrame"""
        empty_df = pd.DataFrame()
    
        result = self.pricing_delta_server._describe_for_logging(empty_df)
    
        self.assertIsInstance(result, str)
        self.assertIn('Pricing delta total rows: 0', result)

    def test_serve_with_valid_responses(self):
        """Test serve method with valid responses using mock file data"""
        # Mock the servers to return our mock data
        self.mock_inventory_server.serve.return_value = pd.DataFrame({
            'product_name': ['Product A', 'Product B'],
            'inventory_price': [10.0, 20.0]
        })
        self.mock_purchase_transactions_server.serve.return_value = pd.DataFrame({
            'product_name': ['Product A', 'Product B'],
            'purchase_quantity': [5, 10],
            'purchase_amount': [45.0, 180.0],
            'purchase_price': [9.0, 18.0],
            'purchase_transaction_date': ['2025-07-31', '2025-07-31']
        })
    
        # Mock the email sender
        self.mock_email_sender.send_email.return_value = True
    
        result = self.pricing_delta_server.serve()
    
        # Should return True if email was sent successfully
        self.assertIsInstance(result, bool)
    
        # Verify servers were called
        self.mock_inventory_server.serve.assert_called_once()
        self.mock_purchase_transactions_server.serve.assert_called_once()

    def test_serve_with_empty_responses(self):
        """Test serve method with empty responses"""
        self.mock_inventory_retriever.retrieve.return_value = []
        self.mock_purchase_transactions_retriever.retrieve.return_value = []
        
        result = self.pricing_delta_server.serve()
        
        self.assertIsInstance(result, bool)

    def test_serve_with_retriever_exception(self):
        """Test serve method when retriever raises an exception"""
        self.mock_inventory_server.serve.side_effect = Exception("API Error")
    
        with self.assertRaises(Exception):
            self.pricing_delta_server.serve()

    def test_serve_with_email_error(self):
        """Test serve method when email sending fails"""
        # Mock the servers to return valid data
        self.mock_inventory_server.serve.return_value = pd.DataFrame({
            'product_name': ['Product A'],
            'inventory_price': [10.0]
        })
        self.mock_purchase_transactions_server.serve.return_value = pd.DataFrame({
            'product_name': ['Product A'],
            'purchase_quantity': [5],
            'purchase_amount': [45.0],
            'purchase_price': [9.0],
            'purchase_transaction_date': ['2025-07-31']
        })
    
        # Mock the email sender to raise an exception
        self.mock_email_sender.send_email.side_effect = Exception("Email Error")
    
        # The serve method should raise the exception
        with self.assertRaises(Exception):
            self.pricing_delta_server.serve()

    def test_with_file_retrievers(self):
        """Test PricingDeltaServer with QBFileRetrievers using mock files"""
        # Create file retrievers with the mock files
        # Use absolute paths from current working directory
        current_dir = os.getcwd()
        mock_inventory_file_path = os.path.join(current_dir, 'retrievers', 'tests', 'mock_inventory_response.jsonl')
        mock_purchase_file_path = os.path.join(current_dir, 'retrievers', 'tests', 'mock_purchase_transactions_response.jsonl')
    
        inventory_retriever = QBFileRetriever(mock_inventory_file_path)
        purchase_retriever = QBFileRetriever(mock_purchase_file_path)
        
        inventory_server = InventoryServer(inventory_retriever)
        purchase_transactions_server = PurchaseTransactionsServer(purchase_retriever)
    
        pricing_delta_server = PricingDeltaServer(
            purchase_transactions_server=purchase_transactions_server,
            inventory_server=inventory_server,
            realm_id="test_realm",
            email_sender=self.mock_email_sender
        )
        
        # Mock the email sender
        self.mock_email_sender.send_email.return_value = True
        
        result = pricing_delta_server.serve()
        
        self.assertIsInstance(result, bool)
        self.mock_email_sender.send_email.assert_called_once()


if __name__ == '__main__':
    unittest.main() 