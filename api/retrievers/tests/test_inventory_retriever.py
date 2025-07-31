#!/usr/bin/env python3
"""
Test script for QBInventoryRetriever
"""

import sys
import os
import json
import unittest
from unittest.mock import Mock, patch
import pandas as pd

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from api.retrievers.qb_inventory_retriever import QBInventoryRetriever
from qbo_request_auth_params import QBORequestAuthParams
import logging
from logging_config import setup_logging

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

class TestInventoryRetriever(unittest.TestCase):
    """Test cases for QBInventoryRetriever"""
    
    def setUp(self):
        """Set up test data"""
        self.auth_params = QBORequestAuthParams()
        self.retriever = QBInventoryRetriever(self.auth_params, "test_realm_id")
        
        # Load inventory sandbox data
        with open('api/retrievers/tests/example_inventory_response_sandbox.json', 'r') as f:
            self.inventory_sandbox_data = json.load(f)
    
    def test_extract_inventory_cols(self):
        """Test extracting inventory columns from sandbox data"""
        print("🧪 Testing inventory extraction from sandbox data...")
        
        # Create a mock response string
        mock_response = json.dumps(self.inventory_sandbox_data)
        
        # Test the extract_inventory_cols method
        inventory_df = self.retriever._extract_cols(mock_response)
        
        # Verify we got data
        self.assertIsNotNone(inventory_df)
        self.assertIsInstance(inventory_df, pd.DataFrame)
        self.assertGreater(len(inventory_df), 0)
        
        print(f"   ✅ Extracted {len(inventory_df)} inventory items")
        
        # Verify structure of extracted data - updated to match current interface
        expected_columns = ['product_name', 'inventory_price']
        for col in expected_columns:
            self.assertIn(col, inventory_df.columns)
        
        # Verify data types
        self.assertTrue(inventory_df['product_name'].dtype == 'object')  # string
        self.assertTrue(inventory_df['inventory_price'].dtype in ['float64', 'int64'])
        
        # Verify values are reasonable
        self.assertTrue(len(inventory_df['product_name'].iloc[0]) > 0)
        self.assertTrue(inventory_df['inventory_price'].min() >= 0)
        
        print("   ✅ All inventory items have correct structure and data types")
        
        # Show some sample data
        print("\n📦 Sample inventory data:")
        for i, row in inventory_df.head(3).iterrows():
            print(f"   {i+1}. {row['product_name']}")
            print(f"      Inventory Price: ${row['inventory_price']:.2f}")
        
        return inventory_df
    
    def test_inventory_retriever_with_mock(self):
        """Test inventory retriever functionality with mock data"""
        print("\n🧪 Testing inventory retriever with mock data...")
        
        # Mock the requests.get call and the get_headers method
        with patch('requests.get') as mock_get, patch.object(self.retriever, 'get_headers') as mock_headers, patch.object(self.retriever.oauth_manager, 'is_company_connected') as mock_connected:
            # Create mock response
            mock_response = Mock()
            mock_response.text = json.dumps(self.inventory_sandbox_data)
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response
            
            # Mock the headers to avoid authentication issues
            mock_headers.return_value = {
                'Authorization': 'Bearer mock_token',
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            }
            
            # Mock the company connection check
            mock_connected.return_value = True
            
            # Test the retrieve method
            inventory_df = self.retriever.retrieve()
            
            # Verify the API was called correctly
            mock_get.assert_called_once()
            call_args = mock_get.call_args
            self.assertIn('/v3/company/test_realm_id/query', call_args[0][0])
            
            # Verify we got data
            self.assertIsNotNone(inventory_df)
            self.assertIsInstance(inventory_df, pd.DataFrame)
            self.assertGreater(len(inventory_df), 0)
            
            print(f"   ✅ Retrieved {len(inventory_df)} inventory items via API")
            
            # Show sample data
            print("\n📦 Sample inventory data from API:")
            for i, row in inventory_df.head(3).iterrows():
                print(f"   {i+1}. {row['product_name']}")
                print(f"      Inventory Price: ${row['inventory_price']:.2f}")
        
        return inventory_df
    
    def test_inventory_data_validation(self):
        """Test inventory data validation"""
        print("\n🧪 Testing inventory data validation...")
        
        # Test with valid data
        mock_response = json.dumps(self.inventory_sandbox_data)
        
        inventory_df = self.retriever._extract_cols(mock_response)
        
        # Verify all items have required fields
        expected_columns = ['product_name', 'inventory_price']
        for col in expected_columns:
            self.assertIn(col, inventory_df.columns)
        
        print("   ✅ All inventory items pass validation")
        
        # Test with empty data
        empty_response = json.dumps({"QueryResponse": {"Item": []}})
        
        empty_inventory_df = self.retriever._extract_cols(empty_response)
        self.assertEqual(len(empty_inventory_df), 0)
        
        print("   ✅ Empty inventory data handled correctly")
        
        return inventory_df
    
    def test_inventory_pricing_calculations(self):
        """Test inventory pricing calculations"""
        print("\n🧪 Testing inventory pricing calculations...")
        
        # Create sample inventory data
        sample_data = [
            {
                'product_name': 'Test:Beef Bone Test Product',
                'inventory_price': 5.50
            },
            {
                'product_name': 'Test:Beef Flank Test Product',
                'inventory_price': 6.25
            },
            {
                'product_name': 'Test:Beef Loin Test Product',
                'inventory_price': 7.25
            }
        ]
        
        inventory_df = pd.DataFrame(sample_data)
        
        # Calculate totals
        total_inventory_price = inventory_df['inventory_price'].sum()
        unique_products = len(inventory_df['product_name'].unique())
        
        # Verify calculations
        expected_inventory_price = 5.50 + 6.25 + 7.25
        expected_products = 3
        
        self.assertAlmostEqual(total_inventory_price, expected_inventory_price, places=2)
        self.assertEqual(unique_products, expected_products)
        
        print(f"   ✅ Total Inventory Price: ${total_inventory_price:.2f}")
        print(f"   ✅ Unique Products: {unique_products}")
        
        return {
            'total_inventory_price': total_inventory_price,
            'unique_products': unique_products
        }
    
    def test_describe_for_logging(self):
        """Test the describe_for_logging method"""
        print("\n🧪 Testing describe_for_logging method...")
        
        # Create sample data
        sample_data = [
            {'product_name': 'Product A', 'inventory_price': 10.0},
            {'product_name': 'Product B', 'inventory_price': 15.0},
            {'product_name': 'Product A', 'inventory_price': 10.0},  # Duplicate
        ]
        
        df = pd.DataFrame(sample_data)
        description = self.retriever._describe_for_logging(df)
        
        # Verify description format
        self.assertIn("Got total:#3", description)
        self.assertIn("inventory items", description)
        self.assertIn("across #2", description)
        self.assertIn("unique products", description)
        
        print(f"   ✅ Logging description: {description}")
        
        return description

def run_inventory_retriever_demo():
    """Run a demo of the inventory retriever functionality"""
    print("🚀 INVENTORY RETRIEVER DEMO")
    print("=" * 50)
    
    try:
        # Initialize test
        test = TestInventoryRetriever()
        test.setUp()
        
        # Run tests
        test.test_extract_inventory_cols()
        test.test_inventory_retriever_with_mock()
        test.test_inventory_data_validation()
        test.test_inventory_pricing_calculations()
        test.test_describe_for_logging()
        
        print("\n✅ All inventory retriever tests passed!")
        
    except Exception as e:
        logger.error(f"Error in inventory retriever demo: {e}")
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    # Run the demo
    run_inventory_retriever_demo()
    
    # Run unit tests
    print("\n" + "=" * 50)
    print("🧪 RUNNING UNIT TESTS")
    print("=" * 50)
    
    unittest.main(argv=[''], exit=False, verbosity=2) 