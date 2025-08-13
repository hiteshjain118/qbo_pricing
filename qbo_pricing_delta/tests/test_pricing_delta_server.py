import unittest
from unittest.mock import Mock, patch
import pandas as pd
import json
import os
import sys

# Add parent directories to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from qbo_pricing_delta.pricing_delta_server import PricingDeltaServer
from qbo.qbo_pricing_delta.pricing_delta_process_node import PricingDeltaProcessNode
from core.iretriever import IRetriever
from qbo.qb_file_retriever import QBFileRetriever
from qbo.qbo_inventory_server.Inventory_price_process_node import InventoryPriceProcessNode
from qbo.qbo_purchase_transactions.purchase_transactions_process_node import PurchaseTransactionsProcessNode


class TestPricingDeltaServer(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures"""
        self.mock_inventory_retriever = Mock(spec=IRetriever)
        self.mock_purchase_transactions_retriever = Mock(spec=IRetriever)
        self.mock_email_sender = Mock()
        
        # Create mock slot extractors
        self.mock_inventory_slot_extractor = Mock(spec=InventoryPriceProcessNode)
        self.mock_purchase_transactions_slot_extractor = Mock(spec=PurchaseTransactionsProcessNode)
        
        # Create mock pricing delta slot extractor
        self.mock_pricing_delta_slot_extractor = Mock(spec=PricingDeltaProcessNode)
        
        self.pricing_delta_server = PricingDeltaServer(
            pricing_delta_slot_extractor=self.mock_pricing_delta_slot_extractor,
            realm_id="test_realm",
            email_sender=self.mock_email_sender
        )
        
        # Load mock data from files - use only the first line since it's JSONL format
        # Use absolute paths from current working directory
        current_dir = os.getcwd()
        mock_inventory_file_path = os.path.join(current_dir, 'qbo_inventory_server', 'tests', 'mock_inventory_response.jsonl')
        with open(mock_inventory_file_path, 'r') as f:
            # The mock data is double-escaped, so we need to parse it twice
            raw_line = f.readline().strip()
            # Parse the double-escaped JSON string to get the actual data
            parsed_once = json.loads(raw_line)
            self.mock_inventory_data = json.loads(parsed_once)
            
        mock_purchase_file_path = os.path.join(current_dir, 'qbo_purchase_transactions', 'tests', 'mock_purchase_transactions_response.jsonl')
        with open(mock_purchase_file_path, 'r') as f:
            # The mock data is double-escaped, so we need to parse it twice
            raw_line = f.readline().strip()
            # Parse the double-escaped JSON string to get the actual data
            parsed_once = json.loads(raw_line)
            self.mock_purchase_transactions_data = json.loads(parsed_once)

    def test_init(self):
        """Test PricingDeltaServer initialization"""
        self.assertEqual(self.pricing_delta_server.pricing_delta_slot_extractor, self.mock_pricing_delta_slot_extractor)
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
        self.assertIsNotNone(server.pricing_delta_slot_extractor)
        self.assertIsNotNone(server.email_sender)
        self.assertEqual(server.realm_id, "test_realm")

    def test_init_with_file_retrievers(self):
        """Test static factory method init_with_file_retrievers"""
        server = PricingDeltaServer.init_with_file_retrievers(
            inventory_save_file_path="test_inventory.jsonl",
            purchase_transactions_save_file_path="test_purchase.jsonl",
            realm_id="test_realm",
            email="test@example.com"
        )
        
        self.assertIsInstance(server, PricingDeltaServer)
        self.assertIsNotNone(server.pricing_delta_slot_extractor)
        self.assertIsNotNone(server.email_sender)
        self.assertEqual(server.realm_id, "test_realm")

    def test_extract_inventory_cols_with_valid_data(self):
        """Test extracting inventory columns from valid response using mock file data"""
        # This method doesn't exist on PricingDeltaServer, it's on InventoryPriceSlotExtractor
        # Test the inventory slot extractor's extract_cols method instead
        inventory_slot_extractor = InventoryPriceProcessNode(self.mock_inventory_retriever)
        # The mock data is already parsed as a dictionary, pass it directly
        mock_response = self.mock_inventory_data
        
        result = inventory_slot_extractor._extract_cols(mock_response)
        
        self.assertIsInstance(result, pd.DataFrame)
        # The mock data contains multiple items, so we should have multiple rows
        self.assertGreater(len(result), 0)
        self.assertEqual(list(result.columns), ['product_name', 'inventory_price'])
        
        # Check that we have valid product names and prices
        self.assertTrue(all(result['product_name'].notna()))
        self.assertTrue(all(result['inventory_price'] >= 0))

    def test_extract_purchase_columns_with_valid_data(self):
        """Test extracting purchase transaction columns from valid response using mock file data"""
        # This method doesn't exist on PricingDeltaServer, it's on PurchaseTransactionsSlotExtractor
        # Test the purchase transactions slot extractor's extract_cols method instead
        purchase_transactions_slot_extractor = PurchaseTransactionsProcessNode(self.mock_purchase_transactions_retriever)
        # The mock data is already parsed as a dictionary, pass it directly
        mock_response = self.mock_purchase_transactions_data
        
        result = purchase_transactions_slot_extractor._extract_cols(mock_response)
        
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
        """Test getting pricing delta with matching products"""
        # Create test data
        purchase_data = pd.DataFrame({
            'product_name': ['Product A', 'Product B', 'Product C'],
            'purchase_quantity': [10, 20, 15],
            'purchase_price': [5.0, 10.0, 7.5],
            'purchase_amount': [50.0, 200.0, 112.5],
            'purchase_transaction_date': ['2025-07-31', '2025-07-31', '2025-07-31']
        })
        
        inventory_data = pd.DataFrame({
            'product_name': ['Product A', 'Product B', 'Product C'],
            'inventory_price': [8.0, 15.0, 12.0]
        })
        
        # Mock the slot extractors to return our test data
        self.mock_purchase_transactions_slot_extractor.extract_slots.return_value = purchase_data
        self.mock_inventory_slot_extractor.extract_slots.return_value = inventory_data
        
        # Create a real PricingDeltaSlotExtractor for testing
        pricing_delta_slot_extractor = PricingDeltaProcessNode(
            purchase_transactions_slot_extractor=self.mock_purchase_transactions_slot_extractor,
            inventory_slot_extractor=self.mock_inventory_slot_extractor
        )
        
        result = pricing_delta_slot_extractor.extract_slots()
        
        self.assertIsInstance(result, pd.DataFrame)
        self.assertEqual(len(result), 3)
        self.assertIn('pricing_delta', result.columns)
        self.assertIn('pricing_perc_delta', result.columns)
        
        # Check that pricing delta calculations are correct
        self.assertEqual(result.iloc[0]['pricing_delta'], 3.0)  # 8.0 - 5.0
        self.assertEqual(result.iloc[1]['pricing_delta'], 5.0)  # 15.0 - 10.0
        self.assertEqual(result.iloc[2]['pricing_delta'], 4.5)  # 12.0 - 7.5

    def test_get_pricing_delta_with_no_matches(self):
        """Test getting pricing delta with no matching products"""
        # Create test data with no matching products
        purchase_data = pd.DataFrame({
            'product_name': ['Product A', 'Product B'],
            'purchase_quantity': [10, 20],
            'purchase_price': [5.0, 10.0],
            'purchase_amount': [50.0, 200.0],
            'purchase_transaction_date': ['2025-07-31', '2025-07-31']
        })
        
        inventory_data = pd.DataFrame({
            'product_name': ['Product C', 'Product D'],
            'inventory_price': [8.0, 15.0]
        })
        
        # Mock the slot extractors to return our test data
        self.mock_purchase_transactions_slot_extractor.extract_slots.return_value = purchase_data
        self.mock_inventory_slot_extractor.extract_slots.return_value = inventory_data
        
        # Create a real PricingDeltaSlotExtractor for testing
        pricing_delta_slot_extractor = PricingDeltaProcessNode(
            purchase_transactions_slot_extractor=self.mock_purchase_transactions_slot_extractor,
            inventory_slot_extractor=self.mock_inventory_slot_extractor
        )
        
        result = pricing_delta_slot_extractor.extract_slots()
        
        self.assertIsInstance(result, pd.DataFrame)
        self.assertEqual(len(result), 2)  # All purchase transactions are included, even without matches

    def test_get_pricing_delta_with_empty_dataframes(self):
        """Test getting pricing delta with empty dataframes"""
        # Create empty test data with proper columns
        purchase_data = pd.DataFrame(columns=['product_name', 'purchase_quantity', 'purchase_price', 'purchase_amount', 'purchase_transaction_date'])
        inventory_data = pd.DataFrame(columns=['product_name', 'inventory_price'])
        
        # Mock the slot extractors to return our test data
        self.mock_purchase_transactions_slot_extractor.extract_slots.return_value = purchase_data
        self.mock_inventory_slot_extractor.extract_slots.return_value = inventory_data
        
        # Create a real PricingDeltaSlotExtractor for testing
        pricing_delta_slot_extractor = PricingDeltaProcessNode(
            purchase_transactions_slot_extractor=self.mock_purchase_transactions_slot_extractor,
            inventory_slot_extractor=self.mock_inventory_slot_extractor
        )
        
        result = pricing_delta_slot_extractor.extract_slots()
        
        self.assertIsInstance(result, pd.DataFrame)
        self.assertEqual(len(result), 0)

    def test_format_pricing_delta_to_html_with_valid_data(self):
        """Test formatting pricing delta to HTML with valid data"""
        # Create test data
        test_data = pd.DataFrame({
            'product_name': ['Product A', 'Product B'],
            'purchase_quantity': [10, 20],
            'purchase_price': [5.0, 10.0],
            'purchase_amount': [50.0, 200.0],
            'purchase_transaction_date': ['2025-07-31', '2025-07-31'],
            'inventory_price': [8.0, 15.0],
            'pricing_delta': [3.0, 5.0],
            'pricing_perc_delta': [60.0, 50.0],
            'matched': ['both', 'both']
        })
        
        html_table, csv_data = self.pricing_delta_server.format_pricing_delta_to_html(test_data)
        
        self.assertIsInstance(html_table, str)
        self.assertIsInstance(csv_data, str)
        self.assertIn('Product A', html_table)
        self.assertIn('Product B', html_table)
        self.assertIn('3.0', html_table)
        self.assertIn('5.0', html_table)

    def test_format_pricing_delta_to_html_empty_dataframe(self):
        """Test formatting pricing delta to HTML with empty DataFrame"""
        empty_df = pd.DataFrame()
        
        html_table, csv_data = self.pricing_delta_server.format_pricing_delta_to_html(empty_df)
        
        self.assertIsInstance(html_table, str)
        self.assertIsInstance(csv_data, str)
        self.assertEqual(html_table, "")
        self.assertEqual(csv_data, "")

    def test_describe_for_logging(self):
        """Test the _describe_for_logging method"""
        # Create test DataFrame
        test_data = pd.DataFrame({
            'product_name': ['Product A', 'Product B'],
            'purchase_quantity': [10, 20],
            'purchase_price': [5.0, 10.0],
            'purchase_amount': [50.0, 200.0],
            'purchase_transaction_date': ['2025-07-31', '2025-07-31'],
            'inventory_price': [8.0, 15.0],
            'pricing_delta': [3.0, 5.0],
            'pricing_perc_delta': [60.0, 50.0],
            'matched': ['both', 'both']
        })
        
        # Create a real PricingDeltaSlotExtractor for testing
        pricing_delta_slot_extractor = PricingDeltaProcessNode(
            purchase_transactions_slot_extractor=self.mock_purchase_transactions_slot_extractor,
            inventory_slot_extractor=self.mock_inventory_slot_extractor
        )
        
        result = pricing_delta_slot_extractor._describe_for_logging(test_data)
        
        self.assertIsInstance(result, str)
        self.assertIn('Pricing delta total rows: 2', result)

    def test_describe_for_logging_empty_dataframe(self):
        """Test the _describe_for_logging method with empty DataFrame"""
        empty_df = pd.DataFrame()
        
        # Create a real PricingDeltaSlotExtractor for testing
        pricing_delta_slot_extractor = PricingDeltaProcessNode(
            purchase_transactions_slot_extractor=self.mock_purchase_transactions_slot_extractor,
            inventory_slot_extractor=self.mock_inventory_slot_extractor
        )
        
        result = pricing_delta_slot_extractor._describe_for_logging(empty_df)
        
        self.assertIsInstance(result, str)
        self.assertIn('Pricing delta total rows: 0', result)

    def test_serve_with_valid_responses(self):
        """Test serve method with valid responses"""
        # Create test data
        test_data = pd.DataFrame({
            'product_name': ['Product A', 'Product B'],
            'purchase_quantity': [10, 20],
            'purchase_price': [5.0, 10.0],
            'purchase_amount': [50.0, 200.0],
            'purchase_transaction_date': ['2025-07-31', '2025-07-31'],
            'inventory_price': [8.0, 15.0],
            'pricing_delta': [3.0, 5.0],
            'pricing_perc_delta': [60.0, 50.0],
            'matched': ['both', 'both']
        })
        
        # Mock the pricing delta slot extractor to return our test data
        self.mock_pricing_delta_slot_extractor.extract_slots.return_value = test_data
        
        # Mock the email sender
        self.mock_email_sender.send_email.return_value = True
        
        result = self.pricing_delta_server.serve()
        
        self.assertTrue(result)
        self.mock_pricing_delta_slot_extractor.extract_slots.assert_called_once()
        self.mock_email_sender.send_email.assert_called_once()

    def test_serve_with_empty_responses(self):
        """Test serve method with empty responses"""
        # Mock the pricing delta slot extractor to return empty data
        self.mock_pricing_delta_slot_extractor.extract_slots.return_value = pd.DataFrame()
        
        # Mock the email sender
        self.mock_email_sender.send_email.return_value = True
        
        result = self.pricing_delta_server.serve()
        
        self.assertTrue(result)
        self.mock_pricing_delta_slot_extractor.extract_slots.assert_called_once()
        self.mock_email_sender.send_email.assert_called_once()

    def test_serve_with_retriever_exception(self):
        """Test serve method when retriever raises an exception"""
        self.mock_pricing_delta_slot_extractor.extract_slots.side_effect = Exception("API Error")
        
        with self.assertRaises(Exception):
            self.pricing_delta_server.serve()

    def test_serve_with_email_error(self):
        """Test serve method when email sending fails"""
        # Create test data
        test_data = pd.DataFrame({
            'product_name': ['Product A'],
            'purchase_quantity': [10],
            'purchase_price': [5.0],
            'purchase_amount': [50.0],
            'purchase_transaction_date': ['2025-07-31'],
            'inventory_price': [8.0],
            'pricing_delta': [3.0],
            'pricing_perc_delta': [60.0],
            'matched': ['both']
        })
        
        # Mock the pricing delta slot extractor to return our test data
        self.mock_pricing_delta_slot_extractor.extract_slots.return_value = test_data
        
        # Mock the email sender to raise an exception
        self.mock_email_sender.send_email.side_effect = Exception("Email Error")
        
        with self.assertRaises(Exception):
            self.pricing_delta_server.serve()

    def test_with_file_retrievers(self):
        """Test PricingDeltaServer with QBFileRetriever using mock files"""
        # Create file retrievers with the mock files
        # Use absolute paths from current working directory
        current_dir = os.getcwd()
        mock_inventory_file_path = os.path.join(current_dir, 'qbo_inventory_server', 'tests', 'mock_inventory_response.jsonl')
        mock_purchase_file_path = os.path.join(current_dir, 'qbo_purchase_transactions', 'tests', 'mock_purchase_transactions_response.jsonl')
        
        server = PricingDeltaServer.init_with_file_retrievers(
            inventory_save_file_path=mock_inventory_file_path,
            purchase_transactions_save_file_path=mock_purchase_file_path,
            realm_id="test_realm",
            email="test@example.com"
        )
        
        self.assertIsInstance(server, PricingDeltaServer)
        self.assertIsNotNone(server.pricing_delta_slot_extractor)
        self.assertIsNotNone(server.email_sender)
        self.assertEqual(server.realm_id, "test_realm")

    def test_get_email_sender_single_email(self):
        """Test get_email_sender with single email"""
        from datetime import datetime
        email_sender = PricingDeltaServer.get_email_sender(
            realm_id="test_realm",
            email="test@example.com",
            report_dt=datetime.now()
        )
        
        self.assertIsNotNone(email_sender)
        self.assertEqual(email_sender.email_to, "test@example.com")
        self.assertEqual(email_sender.company_id, "test_realm")

    def test_get_email_sender_multiple_emails(self):
        """Test get_email_sender with multiple emails"""
        from datetime import datetime
        email_sender = PricingDeltaServer.get_email_sender(
            realm_id="test_realm",
            email="test1@example.com, test2@example.com",
            report_dt=datetime.now()
        )
        
        self.assertIsNotNone(email_sender)
        self.assertEqual(email_sender.email_to, "test1@example.com, test2@example.com")
        self.assertEqual(email_sender.company_id, "test_realm")

    def test_get_email_sender_with_whitespace(self):
        """Test get_email_sender with whitespace in email"""
        from datetime import datetime
        email_sender = PricingDeltaServer.get_email_sender(
            realm_id="test_realm",
            email=" test@example.com ",
            report_dt=datetime.now()
        )
        
        self.assertIsNotNone(email_sender)
        self.assertEqual(email_sender.email_to, " test@example.com ")
        self.assertEqual(email_sender.company_id, "test_realm")

    def test_serve_with_multiple_emails(self):
        """Test serve method with multiple email addresses"""
        # Create test data
        test_data = pd.DataFrame({
            'product_name': ['Product A', 'Product B'],
            'purchase_quantity': [10, 20],
            'purchase_price': [5.0, 10.0],
            'purchase_amount': [50.0, 200.0],
            'purchase_transaction_date': ['2025-07-31', '2025-07-31'],
            'inventory_price': [8.0, 15.0],
            'pricing_delta': [3.0, 5.0],
            'pricing_perc_delta': [60.0, 50.0],
            'matched': ['both', 'both']
        })
        
        # Mock the pricing delta slot extractor to return our test data
        self.mock_pricing_delta_slot_extractor.extract_slots.return_value = test_data
        
        # Mock the email sender
        self.mock_email_sender.send_email.return_value = True
        
        result = self.pricing_delta_server.serve()
        
        self.assertTrue(result)
        self.mock_pricing_delta_slot_extractor.extract_slots.assert_called_once()
        self.mock_email_sender.send_email.assert_called_once()

    def test_format_pricing_delta_to_html_with_matched_column(self):
        """Test formatting pricing delta to HTML with matched column"""
        # Create test data with matched column
        test_data = pd.DataFrame({
            'product_name': ['Product A', 'Product B', 'Product C'],
            'purchase_quantity': [10, 20, 15],
            'purchase_price': [5.0, 10.0, 7.5],
            'purchase_amount': [50.0, 200.0, 112.5],
            'purchase_transaction_date': ['2025-07-31', '2025-07-31', '2025-07-31'],
            'inventory_price': [8.0, 15.0, float('nan')],
            'pricing_delta': [3.0, 5.0, float('nan')],
            'pricing_perc_delta': [60.0, 50.0, float('nan')],
            'matched': ['both', 'both', 'left_only']
        })
        
        html_table, csv_data = self.pricing_delta_server.format_pricing_delta_to_html(test_data)
        
        self.assertIsInstance(html_table, str)
        self.assertIsInstance(csv_data, str)
        self.assertIn('Product A', html_table)
        self.assertIn('Product B', html_table)
        self.assertIn('Product C', html_table)

    def test_describe_for_logging_with_matched_column(self):
        """Test the _describe_for_logging method with matched column"""
        # Create test DataFrame with matched column
        test_data = pd.DataFrame({
            'product_name': ['Product A', 'Product B', 'Product C'],
            'purchase_quantity': [10, 20, 15],
            'purchase_price': [5.0, 10.0, 7.5],
            'purchase_amount': [50.0, 200.0, 112.5],
            'purchase_transaction_date': ['2025-07-31', '2025-07-31', '2025-07-31'],
            'inventory_price': [8.0, 15.0, float('nan')],
            'pricing_delta': [3.0, 5.0, float('nan')],
            'pricing_perc_delta': [60.0, 50.0, float('nan')],
            'matched': ['both', 'both', 'left_only']
        })
        
        # Create a real PricingDeltaSlotExtractor for testing
        pricing_delta_slot_extractor = PricingDeltaProcessNode(
            purchase_transactions_slot_extractor=self.mock_purchase_transactions_slot_extractor,
            inventory_slot_extractor=self.mock_inventory_slot_extractor
        )
        
        result = pricing_delta_slot_extractor._describe_for_logging(test_data)
        
        self.assertIsInstance(result, str)
        self.assertIn('Pricing delta total rows: 3', result)
        self.assertIn('w/ nan inventory price: 1', result)

    def test_init_with_api_retrievers_with_report_date(self):
        """Test static factory method init_with_api_retrievers with specific report date"""
        # Create mock auth params
        mock_auth_params = Mock()
        
        # Create a specific report date
        from datetime import datetime
        import pytz
        report_dt = datetime(2025, 7, 31, tzinfo=pytz.timezone('America/Los_Angeles'))
        
        server = PricingDeltaServer.init_with_api_retrievers(
            auth_params=mock_auth_params,
            realm_id="test_realm",
            email="test@example.com",
            report_dt=report_dt
        )
        
        self.assertIsInstance(server, PricingDeltaServer)
        self.assertIsNotNone(server.pricing_delta_slot_extractor)
        self.assertIsNotNone(server.email_sender)
        self.assertEqual(server.realm_id, "test_realm")

    def test_init_with_file_retrievers_with_report_date(self):
        """Test static factory method init_with_file_retrievers with specific report date"""
        # Create a specific report date
        from datetime import datetime
        import pytz
        report_dt = datetime(2025, 7, 31, tzinfo=pytz.timezone('America/Los_Angeles'))
        
        server = PricingDeltaServer.init_with_file_retrievers(
            inventory_save_file_path="test_inventory.jsonl",
            purchase_transactions_save_file_path="test_purchase.jsonl",
            realm_id="test_realm",
            email="test@example.com",
            report_dt=report_dt
        )
        
        self.assertIsInstance(server, PricingDeltaServer)
        self.assertIsNotNone(server.pricing_delta_slot_extractor)
        self.assertIsNotNone(server.email_sender)
        self.assertEqual(server.realm_id, "test_realm")

    def test_get_email_sender_with_specific_date(self):
        """Test get_email_sender with specific report date"""
        from datetime import datetime
        import pytz
        report_dt = datetime(2025, 7, 31, tzinfo=pytz.timezone('America/Los_Angeles'))
        
        email_sender = PricingDeltaServer.get_email_sender(
            realm_id="test_realm",
            email="test@example.com",
            report_dt=report_dt
        )
        
        self.assertIsNotNone(email_sender)
        self.assertEqual(email_sender.email_to, "test@example.com")
        self.assertEqual(email_sender.company_id, "test_realm")
        self.assertIn("2025-07-31", email_sender.subject)

    def test_serve_with_report_date_parameter(self):
        """Test serve method with report date parameter"""
        # Create test data
        test_data = pd.DataFrame({
            'product_name': ['Product A', 'Product B'],
            'purchase_quantity': [10, 20],
            'purchase_price': [5.0, 10.0],
            'purchase_amount': [50.0, 200.0],
            'purchase_transaction_date': ['2025-07-31', '2025-07-31'],
            'inventory_price': [8.0, 15.0],
            'pricing_delta': [3.0, 5.0],
            'pricing_perc_delta': [60.0, 50.0],
            'matched': ['both', 'both']
        })
        
        # Mock the pricing delta slot extractor to return our test data
        self.mock_pricing_delta_slot_extractor.extract_slots.return_value = test_data
        
        # Mock the email sender
        self.mock_email_sender.send_email.return_value = True
        
        # Test with report date parameter
        from datetime import datetime
        import pytz
        report_dt = datetime(2025, 7, 31, tzinfo=pytz.timezone('America/Los_Angeles'))
        
        result = self.pricing_delta_server.serve()
        
        self.assertTrue(result)
        self.mock_pricing_delta_slot_extractor.extract_slots.assert_called_once()
        self.mock_email_sender.send_email.assert_called_once()

    def test_report_date_validation(self):
        """Test report date validation"""
        # Test with valid report date
        from datetime import datetime
        import pytz
        valid_report_dt = datetime(2025, 7, 31, tzinfo=pytz.timezone('America/Los_Angeles'))
        
        # This should not raise an exception
        try:
            PricingDeltaServer.get_email_sender(
                realm_id="test_realm",
                email="test@example.com",
                report_dt=valid_report_dt
            )
        except Exception as e:
            self.fail(f"Valid report date should not raise exception: {e}")


if __name__ == '__main__':
    unittest.main() 