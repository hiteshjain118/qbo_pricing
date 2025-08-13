import unittest
from unittest.mock import Mock, patch
import pandas as pd
import json
import os
import sys

# Add parent directories to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from qbo.qbo_inventory_server.Inventory_price_process_node import InventoryPriceProcessNode
from core.iretriever import IRetriever
from qbo.qb_file_retriever import QBFileRetriever


class TestInventoryPriceSlotExtractor(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures"""
        self.mock_retriever = Mock(spec=IRetriever)
        self.inventory_slot_extractor = InventoryPriceProcessNode(self.mock_retriever)
        
        # Load mock data from file - use only the first line since it's JSONL format
        # Use absolute path from current working directory
        current_dir = os.getcwd()
        mock_file_path = os.path.join(current_dir, 'qbo_inventory_server', 'tests', 'mock_inventory_response.jsonl')
        with open(mock_file_path, 'r') as f:
            # The mock data is double-escaped, so we need to parse it twice
            raw_line = f.readline().strip()
            # Parse the double-escaped JSON string to get the actual data
            parsed_once = json.loads(raw_line)
            self.mock_inventory_data = json.loads(parsed_once)

    def test_init(self):
        """Test InventoryPriceSlotExtractor initialization"""
        self.assertEqual(self.inventory_slot_extractor.qb_inventory_retriever, self.mock_retriever)

    def test_extract_cols_with_valid_data(self):
        """Test extracting columns from valid inventory response using mock file data"""
        # The mock data is already parsed as a dictionary, pass it directly
        mock_response = self.mock_inventory_data
        
        result = self.inventory_slot_extractor._extract_cols(mock_response)
        
        self.assertIsInstance(result, pd.DataFrame)
        # The mock data contains multiple items, so we should have multiple rows
        self.assertGreater(len(result), 0)
        self.assertEqual(list(result.columns), ['product_name', 'inventory_price'])
        
        # Check that we have valid product names and prices
        self.assertTrue(all(result['product_name'].notna()))
        self.assertTrue(all(result['inventory_price'] >= 0))

    def test_extract_cols_with_empty_response(self):
        """Test extracting columns from empty response"""
        mock_response = {
            "QueryResponse": {
                "Item": []
            }
        }
    
        result = self.inventory_slot_extractor._extract_cols(mock_response)
        
        self.assertIsInstance(result, pd.DataFrame)
        self.assertEqual(len(result), 0)
        # When DataFrame is empty, it may not have columns set
        if len(result.columns) > 0:
            self.assertEqual(list(result.columns), ['product_name', 'inventory_price'])

    def test_extract_cols_with_missing_fields(self):
        """Test extracting columns when some fields are missing"""
        mock_response = {
            "QueryResponse": {
                "Item": [
                    {
                        "FullyQualifiedName": "Test Product",
                        # UnitPrice missing - will default to 0.0
                    },
                    {
                        # FullyQualifiedName missing - will be skipped
                        "UnitPrice": 15.0
                    },
                    {
                        "FullyQualifiedName": "Valid Product",
                        "UnitPrice": 20.0
                    }
                ]
            }
        }
        
        result = self.inventory_slot_extractor._extract_cols(mock_response)
        
        self.assertIsInstance(result, pd.DataFrame)
        # Items with missing FullyQualifiedName are skipped, but items with missing UnitPrice are included
        self.assertEqual(len(result), 2)
        product_names = result['product_name'].tolist()
        self.assertIn('Test Product', product_names)
        self.assertIn('Valid Product', product_names)
        
        # Check that missing UnitPrice defaults to 0.0
        test_product_row = result[result['product_name'] == 'Test Product'].iloc[0]
        self.assertEqual(test_product_row['inventory_price'], 0.0)

    def test_extract_cols_with_invalid_json(self):
        """Test extracting columns with invalid JSON"""
        with self.assertRaises(KeyError):
            self.inventory_slot_extractor._extract_cols({"invalid": "json"})

    def test_describe_for_logging(self):
        """Test the _describe_for_logging method"""
        # Create test DataFrame
        test_data = {
            'product_name': ['Product A', 'Product B', 'Product C'],
            'inventory_price': [10.50, 25.75, 15.00]
        }
        test_df = pd.DataFrame(test_data)
        
        result = self.inventory_slot_extractor._describe_for_logging(test_df)
        
        self.assertIsInstance(result, str)
        self.assertIn('Got total:#3 inventory items', result)
        self.assertIn('across #3 unique products', result)

    def test_describe_for_logging_empty_dataframe(self):
        """Test the _describe_for_logging method with empty DataFrame"""
        empty_df = pd.DataFrame()
        
        result = self.inventory_slot_extractor._describe_for_logging(empty_df)
        
        self.assertIsInstance(result, str)
        self.assertIn('Got total:#0 inventory items', result)

    def test_extract_slots_with_valid_responses(self):
        """Test extract_slots method with valid responses"""
        # Mock the retriever to return our mock data as dictionaries
        self.mock_retriever.retrieve.return_value = [self.mock_inventory_data]
        
        result = self.inventory_slot_extractor.extract_slots()
        
        self.assertIsInstance(result, pd.DataFrame)
        self.assertGreater(len(result), 0)
        self.assertEqual(list(result.columns), ['product_name', 'inventory_price'])

    def test_extract_slots_with_empty_responses(self):
        """Test extract_slots method with empty responses"""
        self.mock_retriever.retrieve.return_value = []
        
        result = self.inventory_slot_extractor.extract_slots()
        
        self.assertIsInstance(result, pd.DataFrame)
        self.assertEqual(len(result), 0)
        # When DataFrame is empty, it may not have columns set
        if len(result.columns) > 0:
            self.assertEqual(list(result.columns), ['product_name', 'inventory_price'])

    def test_extract_slots_with_retriever_exception(self):
        """Test extract_slots method when retriever raises an exception"""
        self.mock_retriever.retrieve.side_effect = Exception("API Error")
        
        with self.assertRaises(Exception):
            self.inventory_slot_extractor.extract_slots()

    def test_extract_slots_with_invalid_response_format(self):
        """Test extract_slots method with invalid response format"""
        self.mock_retriever.retrieve.return_value = ["invalid json"]
        
        with self.assertRaises(TypeError):
            self.inventory_slot_extractor.extract_slots()

    def test_with_file_retriever(self):
        """Test InventoryPriceSlotExtractor with QBFileRetriever using mock file"""
        # Create a file retriever with the mock file
        # Use absolute path from current working directory
        current_dir = os.getcwd()
        mock_file_path = os.path.join(current_dir, 'qbo_inventory_server', 'tests', 'mock_inventory_response.jsonl')
        file_retriever = QBFileRetriever(mock_file_path)
        inventory_slot_extractor = InventoryPriceProcessNode(file_retriever)
        
        result = inventory_slot_extractor.extract_slots()
        
        self.assertIsInstance(result, pd.DataFrame)
        self.assertGreater(len(result), 0)
        self.assertEqual(list(result.columns), ['product_name', 'inventory_price'])


if __name__ == '__main__':
    unittest.main() 