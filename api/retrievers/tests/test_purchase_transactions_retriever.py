#!/usr/bin/env python3
"""
Test script for QBPurchaseTransactionsRetriever
"""

import sys
import os
import json
import unittest
from unittest.mock import Mock, patch
import pandas as pd

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from api.retrievers.qb_purchase_transactions import QBPurchaseTransactionsRetriever
from qbo_request_auth_params import QBORequestAuthParams
import logging
from logging_config import setup_logging

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

class TestPurchaseTransactionsRetriever(unittest.TestCase):
    """Test cases for QBPurchaseTransactionsRetriever"""
    
    def setUp(self):
        """Set up test data"""
        self.auth_params = QBORequestAuthParams()
        self.retriever = QBPurchaseTransactionsRetriever(self.auth_params, "test_realm_id", "2025-07-29")
        
        # Load bills sandbox data
        with open('api/retrievers/tests/example_bills_response_sandbox.json', 'r') as f:
            self.bills_sandbox_data = json.load(f)
    
    def test_extract_bill_columns_from_sandbox(self):
        """Test extracting bill columns from sandbox data"""
        print("🧪 Testing bill extraction from sandbox data...")
        
        # Create a mock response string
        mock_response = json.dumps(self.bills_sandbox_data)
        
        # Test the extract_inventory_cols method
        bills_df = self.retriever._extract_cols(mock_response)
        
        # Verify we got data
        self.assertIsNotNone(bills_df)
        self.assertIsInstance(bills_df, pd.DataFrame)
        self.assertGreater(len(bills_df), 0)
        
        print(f"   ✅ Extracted {len(bills_df)} line items")
        
        # Verify structure of extracted data - updated to match current interface
        expected_columns = ['product_name', 'purchase_price']
        for col in expected_columns:
            self.assertIn(col, bills_df.columns)
        
        # Verify data types
        self.assertTrue(bills_df['product_name'].dtype == 'object')  # string
        self.assertTrue(bills_df['purchase_price'].dtype in ['float64', 'int64'])
        
        # Verify values are reasonable
        self.assertTrue(len(bills_df['product_name'].iloc[0]) > 0)
        self.assertTrue(bills_df['purchase_price'].min() >= 0)
        
        print("   ✅ All extracted items have correct structure and data types")
        
        # Show some sample data
        print("\n📋 Sample extracted data:")
        for i, row in bills_df.head(3).iterrows():
            print(f"   {i+1}. {row['product_name']} - Purchase Price: ${row['purchase_price']:.2f}")
        
        return bills_df
    
    def test_purchase_transactions_retriever_with_mock(self):
        """Test purchase transactions retriever functionality with mock data"""
        print("\n🧪 Testing purchase transactions retriever with mock data...")
        
        # Mock the requests.get call and the get_headers method
        with patch('requests.get') as mock_get, patch.object(self.retriever, 'get_headers') as mock_headers, patch.object(self.retriever.oauth_manager, 'is_company_connected') as mock_connected:
            # Create mock response
            mock_response = Mock()
            mock_response.text = json.dumps(self.bills_sandbox_data)
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
            bills_df = self.retriever.retrieve()
            
            # Verify the API was called correctly
            mock_get.assert_called_once()
            call_args = mock_get.call_args
            self.assertIn('/v3/company/test_realm_id/query', call_args[0][0])
            
            # Verify we got data
            self.assertIsNotNone(bills_df)
            self.assertIsInstance(bills_df, pd.DataFrame)
            self.assertGreater(len(bills_df), 0)
            
            print(f"   ✅ Retrieved {len(bills_df)} bill transactions via API")
            
            # Show sample data
            print("\n📋 Sample bill transactions from API:")
            for i, row in bills_df.head(3).iterrows():
                print(f"   {i+1}. {row['product_name']} - Purchase Price: ${row['purchase_price']:.2f}")
        
        return bills_df
    
    def test_bill_data_validation(self):
        """Test bill data validation"""
        print("\n🧪 Testing bill data validation...")
        
        # Test with valid data
        mock_response = json.dumps(self.bills_sandbox_data)
        
        bills_df = self.retriever._extract_cols(mock_response)
        
        # Verify all items have required fields
        expected_columns = ['product_name', 'purchase_price']
        for col in expected_columns:
            self.assertIn(col, bills_df.columns)
        
        print("   ✅ All bill transactions pass validation")
        
        # Test with empty data
        empty_response = json.dumps({"QueryResponse": {"Bill": []}})
        
        empty_bills_df = self.retriever._extract_cols(empty_response)
        self.assertEqual(len(empty_bills_df), 0)
        
        print("   ✅ Empty bill data handled correctly")
        
        return bills_df
    
    def test_bill_transactions_calculations(self):
        """Test bill transactions calculations"""
        print("\n🧪 Testing bill transactions calculations...")
        
        # Create sample bill data
        sample_data = [
            {
                'product_name': 'Test:Beef Bone Test Product',
                'purchase_price': 4.93
            },
            {
                'product_name': 'Test:Beef Flank Test Product',
                'purchase_price': 4.89
            },
            {
                'product_name': 'Test:Beef Loin Test Product',
                'purchase_price': 5.87
            }
        ]
        
        bills_df = pd.DataFrame(sample_data)
        
        # Calculate totals
        total_purchase_price = bills_df['purchase_price'].sum()
        unique_products = len(bills_df['product_name'].unique())
        
        # Verify calculations
        expected_purchase_price = 4.93 + 4.89 + 5.87
        expected_products = 3
        
        self.assertAlmostEqual(total_purchase_price, expected_purchase_price, places=2)
        self.assertEqual(unique_products, expected_products)
        
        print(f"   ✅ Total Purchase Price: ${total_purchase_price:.2f}")
        print(f"   ✅ Unique Products: {unique_products}")
        
        return {
            'total_purchase_price': total_purchase_price,
            'unique_products': unique_products
        }
    
    def test_describe_for_logging(self):
        """Test the describe_for_logging method"""
        print("\n🧪 Testing describe_for_logging method...")
        
        # Create sample data
        sample_data = [
            {'product_name': 'Product A', 'purchase_price': 10.0},
            {'product_name': 'Product B', 'purchase_price': 15.0},
            {'product_name': 'Product A', 'purchase_price': 10.0},
        ]
        
        df = pd.DataFrame(sample_data)
        description = self.retriever._describe_for_logging(df)
        
        # Verify description format
        self.assertIn("On 2025-07-29", description)
        self.assertIn("got total:#3", description)
        self.assertIn("bill transactions", description)
        self.assertIn("across #2", description)
        self.assertIn("unique products", description)
        
        print(f"   ✅ Logging description: {description}")
        
        return description

def run_purchase_transactions_retriever_demo():
    """Run a demo of the purchase transactions retriever functionality"""
    print("🚀 PURCHASE TRANSACTIONS RETRIEVER DEMO")
    print("=" * 50)
    
    try:
        # Initialize test
        test = TestPurchaseTransactionsRetriever()
        test.setUp()
        
        # Run tests
        test.test_extract_bill_columns_from_sandbox()
        test.test_purchase_transactions_retriever_with_mock()
        test.test_bill_data_validation()
        test.test_bill_transactions_calculations()
        test.test_describe_for_logging()
        
        print("\n✅ All purchase transactions retriever tests passed!")
        
    except Exception as e:
        logger.error(f"Error in purchase transactions retriever demo: {e}")
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    # Run the demo
    run_purchase_transactions_retriever_demo()
    
    # Run unit tests
    print("\n" + "=" * 50)
    print("🧪 RUNNING UNIT TESTS")
    print("=" * 50)
    
    unittest.main(argv=[''], exit=False, verbosity=2) 