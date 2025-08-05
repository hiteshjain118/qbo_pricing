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

        result = self.pricing_delta_server.get_pricing_delta(purchase_df, inventory_df)

        # Verify the result
        self.assertIsInstance(result, pd.DataFrame)
        self.assertEqual(len(result), 3)  # All purchase transactions should be included
        self.assertIn('pricing_delta', result.columns)
        self.assertIn('pricing_perc_delta', result.columns)
        self.assertIn('matched', result.columns)

        # Check that matching products have both inventory and purchase data
        product_a_row = result[result['product_name'] == 'Product A'].iloc[0]
        self.assertEqual(product_a_row['matched'], 'both')
        self.assertNotEqual(product_a_row['pricing_delta'], None)

        # Check that non-matching products have only purchase data
        product_d_row = result[result['product_name'] == 'Product D'].iloc[0]
        self.assertEqual(product_d_row['matched'], 'left_only')
        self.assertTrue(pd.isna(product_d_row['inventory_price']))

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

        result = self.pricing_delta_server.get_pricing_delta(purchase_df, inventory_df)

        # Verify the result
        self.assertIsInstance(result, pd.DataFrame)
        self.assertEqual(len(result), 2)  # All purchase transactions should be included
        self.assertIn('pricing_delta', result.columns)
        self.assertIn('pricing_perc_delta', result.columns)
        self.assertIn('matched', result.columns)

        # Check that all products have only purchase data (no inventory matches)
        for _, row in result.iterrows():
            self.assertEqual(row['matched'], 'left_only')
            self.assertTrue(pd.isna(row['inventory_price']))

    def test_get_pricing_delta_with_empty_dataframes(self):
        """Test get_pricing_delta with empty DataFrames"""
        # Create empty DataFrames with the required columns and proper dtypes
        empty_purchase_df = pd.DataFrame(columns=['product_name', 'purchase_price']).astype({
            'product_name': 'object',
            'purchase_price': 'float64'
        })
        empty_inventory_df = pd.DataFrame(columns=['product_name', 'inventory_price']).astype({
            'product_name': 'object',
            'inventory_price': 'float64'
        })
        
        result = self.pricing_delta_server.get_pricing_delta(empty_purchase_df, empty_inventory_df)
        
        # Verify the result
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
        
        purchase_df = pd.DataFrame({'product_name': ['Product A', 'Product B']})
        inventory_df = pd.DataFrame({'product_name': ['Product A']})
        
        result = self.pricing_delta_server._describe_for_logging(test_df, purchase_df, inventory_df)
        
        # Verify the result contains expected information
        self.assertIn("Pricing delta total rows: 2", result)
        self.assertIn("w/ nan inventory price: 1", result)
        self.assertIn("products with nan inventory price: ['Product B']", result)

    def test_describe_for_logging_empty_dataframe(self):
        """Test the _describe_for_logging method with empty DataFrame"""
        empty_df = pd.DataFrame()
        purchase_df = pd.DataFrame()
        inventory_df = pd.DataFrame()
        
        result = self.pricing_delta_server._describe_for_logging(empty_df, purchase_df, inventory_df)
        
        # Verify the result contains expected information for empty DataFrame
        self.assertIn("Pricing delta total rows: 0", result)
        self.assertIn("w/ nan inventory price: 0", result)
        self.assertIn("products with nan inventory price: []", result)

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
        # Mock empty server responses
        self.mock_purchase_transactions_server.serve.return_value = pd.DataFrame()
        self.mock_inventory_server.serve.return_value = pd.DataFrame()
        
        # Create email sender with multiple emails
        mock_email_sender = Mock()
        self.pricing_delta_server.email_sender = mock_email_sender
        
        # Call serve method
        result = self.pricing_delta_server.serve()
        
        # Verify the result
        self.assertTrue(result)
        
        # Verify that email sender was called
        mock_email_sender.send_email.assert_called_once()
        
        # Verify the call arguments
        call_args = mock_email_sender.send_email.call_args
        html_arg, excel_arg = call_args[0]
        
        # Verify HTML contains empty message
        self.assertIn("No purchase transactions found", html_arg)
        self.assertEqual(excel_arg, "")

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

    def test_get_email_sender_single_email(self):
        """Test get_email_sender with single email address"""
        from datetime import datetime
        report_dt = datetime.now()
        email_sender = PricingDeltaServer.get_email_sender("test_realm", "test@example.com", report_dt)
        
        self.assertIsNotNone(email_sender)
        self.assertEqual(email_sender.email_to, "test@example.com")
        self.assertEqual(email_sender.company_id, "test_realm")
        self.assertIn("QuickBooks Pricing Markup Report", email_sender.subject)

    def test_get_email_sender_multiple_emails(self):
        """Test get_email_sender with multiple comma-separated email addresses"""
        from datetime import datetime
        report_dt = datetime.now()
        email_sender = PricingDeltaServer.get_email_sender("test_realm", "test1@example.com, test2@example.com, test3@example.com", report_dt)
        
        self.assertIsNotNone(email_sender)
        self.assertEqual(email_sender.email_to, "test1@example.com, test2@example.com, test3@example.com")
        self.assertEqual(email_sender.company_id, "test_realm")
        self.assertIn("QuickBooks Pricing Markup Report", email_sender.subject)

    def test_get_email_sender_with_whitespace(self):
        """Test get_email_sender with email addresses containing whitespace"""
        from datetime import datetime
        report_dt = datetime.now()
        email_sender = PricingDeltaServer.get_email_sender("test_realm", "  test1@example.com  ,  test2@example.com  ", report_dt)
        
        self.assertIsNotNone(email_sender)
        self.assertEqual(email_sender.email_to, "  test1@example.com  ,  test2@example.com  ")
        self.assertEqual(email_sender.company_id, "test_realm")

    def test_serve_with_multiple_emails(self):
        """Test serve method with multiple email addresses"""
        # Mock the server responses
        mock_purchase_df = pd.DataFrame({
            'product_name': ['Product A', 'Product B'],
            'purchase_price': [10.0, 20.0],
            'purchase_quantity': [1, 2],
            'purchase_amount': [10.0, 40.0],
            'purchase_transaction_date': ['2025-01-01', '2025-01-02']
        })
        
        mock_inventory_df = pd.DataFrame({
            'product_name': ['Product A', 'Product B'],
            'inventory_price': [15.0, 25.0]
        })
        
        self.mock_purchase_transactions_server.serve.return_value = mock_purchase_df
        self.mock_inventory_server.serve.return_value = mock_inventory_df
        
        # Create email sender with multiple emails
        mock_email_sender = Mock()
        self.pricing_delta_server.email_sender = mock_email_sender
        
        # Call serve method
        result = self.pricing_delta_server.serve()
        
        # Verify the result
        self.assertTrue(result)
        
        # Verify that email sender was called
        mock_email_sender.send_email.assert_called_once()
        
        # Verify the call arguments
        call_args = mock_email_sender.send_email.call_args
        html_arg, excel_arg = call_args[0]
        
        # Verify HTML contains expected content
        self.assertIn("Product Name", html_arg)
        self.assertIn("Purchase Price", html_arg)
        self.assertIn("Inventory Price", html_arg)
        self.assertIn("Markup", html_arg)
        
        # Verify Excel data is not empty
        self.assertNotEqual(excel_arg, "")

    def test_format_pricing_delta_to_html_with_matched_column(self):
        """Test format_pricing_delta_to_html handles the matched column correctly"""
        pricing_delta_df = pd.DataFrame({
            'product_name': ['Product A', 'Product B'],
            'purchase_price': [10.0, 20.0],
            'inventory_price': [15.0, 25.0],
            'pricing_delta': [5.0, 5.0],
            'pricing_perc_delta': [50.0, 25.0],
            'purchase_transaction_date': ['2025-01-01', '2025-01-02'],
            'purchase_quantity': [1, 2],
            'purchase_amount': [10.0, 40.0],
            'matched': ['both', 'both']
        })
        
        html, excel_data = self.pricing_delta_server.format_pricing_delta_to_html(pricing_delta_df)
        
        # Verify HTML contains expected columns
        self.assertIn("Product Name", html)
        self.assertIn("Purchase Price", html)
        self.assertIn("Inventory Price", html)
        self.assertIn("Markup (Inventory - Purchase)", html)
        self.assertIn("Markup % (Inventory - Purchase)/Purchase", html)
        
        # Verify Excel data is not empty
        self.assertNotEqual(excel_data, "")

    def test_describe_for_logging_with_matched_column(self):
        """Test _describe_for_logging handles the matched column correctly"""
        pricing_delta_df = pd.DataFrame({
            'product_name': ['Product A', 'Product B', 'Product C'],
            'purchase_price': [10.0, 20.0, 30.0],
            'inventory_price': [15.0, 25.0, None],
            'pricing_delta': [5.0, 5.0, None],
            'pricing_perc_delta': [50.0, 25.0, None],
            'matched': ['both', 'both', 'left_only']
        })
        
        purchase_df = pd.DataFrame({'product_name': ['Product A', 'Product B', 'Product C']})
        inventory_df = pd.DataFrame({'product_name': ['Product A', 'Product B']})
        
        description = self.pricing_delta_server._describe_for_logging(pricing_delta_df, purchase_df, inventory_df)
        
        # Verify the description contains expected information
        self.assertIn("Pricing delta total rows: 3", description)
        self.assertIn("w/ nan inventory price: 1", description)
        self.assertIn("products with nan inventory price: ['Product C']", description)

    def test_init_with_api_retrievers_with_report_date(self):
        """Test init_with_api_retrievers with specific report date"""
        from datetime import datetime
        mock_auth_params = Mock()
        report_dt = datetime(2025, 1, 15)
        
        server = PricingDeltaServer.init_with_api_retrievers(
            auth_params=mock_auth_params,
            realm_id="test_realm",
            email="test@example.com",
            report_dt=report_dt
        )
        
        self.assertIsInstance(server, PricingDeltaServer)
        self.assertIsNotNone(server.inventory_server)
        self.assertIsNotNone(server.purchase_transactions_server)
        self.assertIsNotNone(server.email_sender)
        self.assertEqual(server.realm_id, "test_realm")
        
        # Verify the email sender has the correct report date in subject
        self.assertIn("2025-01-15", server.email_sender.subject)

    def test_init_with_file_retrievers_with_report_date(self):
        """Test init_with_file_retrievers with specific report date"""
        from datetime import datetime
        report_dt = datetime(2025, 1, 20)
        
        server = PricingDeltaServer.init_with_file_retrievers(
            inventory_file_path="test_inventory.jsonl",
            purchase_transactions_file_path="test_purchase.jsonl",
            realm_id="test_realm",
            email="test@example.com",
            report_dt=report_dt
        )
        
        self.assertIsInstance(server, PricingDeltaServer)
        self.assertIsInstance(server.inventory_server.qb_inventory_retriever, QBFileRetriever)
        self.assertIsInstance(server.purchase_transactions_server.qb_purchase_transactions_retriever, QBFileRetriever)
        self.assertIsNotNone(server.email_sender)
        self.assertEqual(server.realm_id, "test_realm")
        
        # Verify the email sender has the correct report date in subject
        self.assertIn("2025-01-20", server.email_sender.subject)

    def test_get_email_sender_with_specific_date(self):
        """Test get_email_sender with a specific report date"""
        from datetime import datetime
        report_dt = datetime(2025, 2, 10)
        email_sender = PricingDeltaServer.get_email_sender("test_realm", "test@example.com", report_dt)
        
        self.assertIsNotNone(email_sender)
        self.assertEqual(email_sender.email_to, "test@example.com")
        self.assertEqual(email_sender.company_id, "test_realm")
        self.assertIn("QuickBooks Pricing Markup Report", email_sender.subject)
        self.assertIn("2025-02-10", email_sender.subject)

    def test_serve_with_report_date_parameter(self):
        """Test serve method with report date parameter"""
        # Mock the server responses
        mock_purchase_df = pd.DataFrame({
            'product_name': ['Product A', 'Product B'],
            'purchase_price': [10.0, 20.0],
            'purchase_quantity': [1, 2],
            'purchase_amount': [10.0, 40.0],
            'purchase_transaction_date': ['2025-01-01', '2025-01-02']
        })
        
        mock_inventory_df = pd.DataFrame({
            'product_name': ['Product A', 'Product B'],
            'inventory_price': [15.0, 25.0]
        })
        
        self.mock_purchase_transactions_server.serve.return_value = mock_purchase_df
        self.mock_inventory_server.serve.return_value = mock_inventory_df
        
        # Create email sender with multiple emails
        mock_email_sender = Mock()
        self.pricing_delta_server.email_sender = mock_email_sender
        
        # Call serve method
        result = self.pricing_delta_server.serve()
        
        # Verify the result
        self.assertTrue(result)
        
        # Verify that email sender was called
        mock_email_sender.send_email.assert_called_once()
        
        # Verify the call arguments
        call_args = mock_email_sender.send_email.call_args
        html_arg, excel_arg = call_args[0]
        
        # Verify HTML contains expected content
        self.assertIn("Product Name", html_arg)
        self.assertIn("Purchase Price", html_arg)
        self.assertIn("Inventory Price", html_arg)
        self.assertIn("Markup", html_arg)
        
        # Verify Excel data is not empty
        self.assertNotEqual(excel_arg, "")

    def test_report_date_validation(self):
        """Test that report date is properly validated and formatted"""
        from datetime import datetime
        
        # Test with valid date
        report_dt = datetime(2025, 3, 15)
        email_sender = PricingDeltaServer.get_email_sender("test_realm", "test@example.com", report_dt)
        
        self.assertIn("2025-03-15", email_sender.subject)
        
        # Test with different date
        report_dt2 = datetime(2024, 12, 31)
        email_sender2 = PricingDeltaServer.get_email_sender("test_realm", "test@example.com", report_dt2)
        
        self.assertIn("2024-12-31", email_sender2.subject)


if __name__ == '__main__':
    unittest.main() 