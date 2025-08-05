#!/usr/bin/env python3
"""
Test script for QBPurchaseTransactionsAPIRetriever
"""

import sys
import os
import json
import unittest
from unittest.mock import Mock, patch
import pandas as pd
from datetime import datetime

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from retrievers.qb_purchase_transactions_api_retriever import QBPurchaseTransactionsAPIRetriever
from qbo_request_auth_params import QBORequestAuthParams
import logging
from logging_config import setup_logging

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

class TestQBPurchaseTransactionsAPIRetriever(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures"""
        self.auth_params = QBORequestAuthParams()
        self.realm_id = "test_realm_id"
        self.report_dt = datetime.now()
        self.retriever = QBPurchaseTransactionsAPIRetriever(
            auth_params=self.auth_params,
            realm_id=self.realm_id,
            report_dt=self.report_dt
        )

    def test_call_api_once(self):
        """Test the _call_api_once method"""
        mock_response = Mock()
        mock_response.text = '{"QueryResponse": {"Bill": [{"Id": "123", "VendorRef": {"name": "Test Vendor"}, "Line": [{"ItemBasedExpenseLineDetail": {"ItemRef": {"name": "Test Product"}, "Qty": 5, "UnitPrice": 10.0}, "Amount": 50.0}], "TxnDate": "2025-07-29"}]}}'
        mock_response.json.return_value = {"QueryResponse": {"Bill": [{"Id": "123", "VendorRef": {"name": "Test Vendor"}, "Line": [{"ItemBasedExpenseLineDetail": {"ItemRef": {"name": "Test Product"}, "Qty": 5, "UnitPrice": 10.0}, "Amount": 50.0}], "TxnDate": "2025-07-29"}]}}
        mock_response.raise_for_status.return_value = None
    
        with patch('requests.get', return_value=mock_response):
            with patch.object(self.retriever, 'get_headers', return_value={'Authorization': 'Bearer test_token'}):
                response_dict, num_items = self.retriever._call_api_once()
    
                self.assertIsInstance(response_dict, dict)
                self.assertEqual(num_items, 1)
                self.assertIn('QueryResponse', response_dict)
                self.assertIn('Bill', response_dict['QueryResponse'])

    def test_describe_for_logging(self):
        """Test the _describe_for_logging method"""
        responses = ['response1', 'response2']
        description = self.retriever._describe_for_logging(responses)
        
        self.assertIn("got total:#2", description)
        self.assertIn("purchase transaction responses", description)
        self.assertIn(self.retriever.report_date, description)

    def test_retrieve_with_mock(self):
        """Test the retrieve method with mock data"""
        mock_response = Mock()
        mock_response.text = '{"QueryResponse": {"Bill": [{"Id": "123", "VendorRef": {"name": "Test Vendor"}, "Line": [{"ItemBasedExpenseLineDetail": {"ItemRef": {"name": "Test Product"}, "Qty": 5, "UnitPrice": 10.0}, "Amount": 50.0}], "TxnDate": "2025-07-29"}]}}'
        mock_response.json.return_value = {"QueryResponse": {"Bill": [{"Id": "123", "VendorRef": {"name": "Test Vendor"}, "Line": [{"ItemBasedExpenseLineDetail": {"ItemRef": {"name": "Test Product"}, "Qty": 5, "UnitPrice": 10.0}, "Amount": 50.0}], "TxnDate": "2025-07-29"}]}}
        mock_response.raise_for_status.return_value = None
    
        with patch('requests.get', return_value=mock_response):
            with patch.object(self.retriever, 'get_headers', return_value={'Authorization': 'Bearer test_token'}):
                with patch.object(self.retriever.oauth_manager, 'is_company_connected', return_value=True):
                    responses = self.retriever.retrieve()
    
                    self.assertIsInstance(responses, list)
                    self.assertEqual(len(responses), 1)
                    self.assertIsInstance(responses[0], dict)
                    self.assertIn('QueryResponse', responses[0])

    def test_retrieve_company_not_connected(self):
        """Test retrieve method when company is not connected"""
        with patch.object(self.retriever.oauth_manager, 'is_company_connected', return_value=False):
            with self.assertRaises(Exception) as context:
                self.retriever.retrieve()
            
            self.assertIn("Company test_realm_id is no longer connected", str(context.exception))

    def test_get_headers(self):
        """Test the get_headers method"""
        with patch.object(self.retriever.oauth_manager, 'get_valid_access_token_not_throws', return_value='test_token'):
            headers = self.retriever.get_headers()
            
            self.assertIn('Authorization', headers)
            self.assertIn('Accept', headers)
            self.assertIn('Content-Type', headers)
            self.assertEqual(headers['Authorization'], 'Bearer test_token')

    def test_get_headers_no_token(self):
        """Test get_headers when no valid token is available"""
        with patch.object(self.retriever.oauth_manager, 'get_valid_access_token_not_throws', return_value=None):
            with self.assertRaises(Exception) as context:
                self.retriever.get_headers()
            
            self.assertIn("No valid access token for company test_realm_id", str(context.exception))

    def test_call_api_once_missing_query_response(self):
        """Test _call_api_once when QueryResponse key is missing"""
        mock_response = Mock()
        mock_response.json.return_value = {"SomeOtherKey": {"Bill": []}}
        mock_response.raise_for_status.return_value = None
    
        with patch('requests.get', return_value=mock_response):
            with patch.object(self.retriever, 'get_headers', return_value={'Authorization': 'Bearer test_token'}):
                with self.assertRaises(KeyError):
                    self.retriever._call_api_once()

    def test_call_api_once_missing_bill_key(self):
        """Test _call_api_once when Bill key is missing from QueryResponse"""
        mock_response = Mock()
        mock_response.json.return_value = {"QueryResponse": {"SomeOtherKey": []}}
        mock_response.raise_for_status.return_value = None
    
        with patch('requests.get', return_value=mock_response):
            with patch.object(self.retriever, 'get_headers', return_value={'Authorization': 'Bearer test_token'}):
                response_dict, num_items = self.retriever._call_api_once()
    
                self.assertIsInstance(response_dict, dict)
                self.assertEqual(num_items, 0)  # Should return 0 when Bill key is missing
                self.assertIn('QueryResponse', response_dict)

    def test_call_api_once_empty_bill_list(self):
        """Test _call_api_once when Bill list is empty"""
        mock_response = Mock()
        mock_response.json.return_value = {"QueryResponse": {"Bill": []}}
        mock_response.raise_for_status.return_value = None
    
        with patch('requests.get', return_value=mock_response):
            with patch.object(self.retriever, 'get_headers', return_value={'Authorization': 'Bearer test_token'}):
                response_dict, num_items = self.retriever._call_api_once()
    
                self.assertIsInstance(response_dict, dict)
                self.assertEqual(num_items, 0)
                self.assertIn('QueryResponse', response_dict)
                self.assertIn('Bill', response_dict['QueryResponse'])
                self.assertEqual(len(response_dict['QueryResponse']['Bill']), 0)

    def test_call_api_once_bill_key_is_none(self):
        """Test _call_api_once when Bill key is None"""
        mock_response = Mock()
        mock_response.json.return_value = {"QueryResponse": {"Bill": None}}
        mock_response.raise_for_status.return_value = None
    
        with patch('requests.get', return_value=mock_response):
            with patch.object(self.retriever, 'get_headers', return_value={'Authorization': 'Bearer test_token'}):
                with self.assertRaises(TypeError):
                    self.retriever._call_api_once()

    def test_call_api_once_malformed_response(self):
        """Test _call_api_once with malformed response"""
        mock_response = Mock()
        mock_response.json.return_value = {"QueryResponse": None}
        mock_response.raise_for_status.return_value = None
    
        with patch('requests.get', return_value=mock_response):
            with patch.object(self.retriever, 'get_headers', return_value={'Authorization': 'Bearer test_token'}):
                with self.assertRaises(AttributeError):
                    self.retriever._call_api_once()

    def test_call_api_once_bill_key_not_present(self):
        """Test _call_api_once when Bill key is not present in QueryResponse"""
        mock_response = Mock()
        mock_response.json.return_value = {"QueryResponse": {}}  # Empty QueryResponse
        mock_response.raise_for_status.return_value = None
    
        with patch('requests.get', return_value=mock_response):
            with patch.object(self.retriever, 'get_headers', return_value={'Authorization': 'Bearer test_token'}):
                response_dict, num_items = self.retriever._call_api_once()
    
                self.assertIsInstance(response_dict, dict)
                self.assertEqual(num_items, 0)  # Should return 0 when Bill key is not present
                self.assertIn('QueryResponse', response_dict)


if __name__ == '__main__':
    unittest.main() 