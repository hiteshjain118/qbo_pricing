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
from datetime import datetime

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from retrievers.qb_inventory_api_retriever import QBInventoryAPIRetriever
from qbo_request_auth_params import QBORequestAuthParams
import logging
from logging_config import setup_logging

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

class TestInventoryRetriever(unittest.TestCase):
    """Test cases for QBInventoryRetriever"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.auth_params = QBORequestAuthParams()
        self.realm_id = "test_realm_id"
        self.retriever = QBInventoryAPIRetriever(
            auth_params=self.auth_params,
            realm_id=self.realm_id
        )

    def test_call_api_once(self):
        """Test the _call_api_once method"""
        mock_response = Mock()
        mock_response.text = '{"QueryResponse": {"Item": [{"Id": "1", "FullyQualifiedName": "Test Product", "UnitPrice": 10.0}]}}'
        mock_response.json.return_value = {"QueryResponse": {"Item": [{"Id": "1", "FullyQualifiedName": "Test Product", "UnitPrice": 10.0}]}}
        mock_response.raise_for_status.return_value = None
    
        with patch('requests.get', return_value=mock_response):
            with patch.object(self.retriever, 'get_headers', return_value={'Authorization': 'Bearer test_token'}):
                response_dict, num_items = self.retriever._call_api_once()
    
                self.assertIsInstance(response_dict, dict)
                self.assertEqual(num_items, 1)
                self.assertIn('QueryResponse', response_dict)
                self.assertIn('Item', response_dict['QueryResponse'])

    def test_describe_for_logging(self):
        """Test the _describe_for_logging method"""
        responses = ['response1', 'response2', 'response3']
        description = self.retriever._describe_for_logging(responses)
        
        self.assertIn("got total:#3", description)
        self.assertIn("inventory responses", description)

    def test_retrieve_with_mock(self):
        """Test the retrieve method with mock data"""
        mock_response = Mock()
        mock_response.text = '{"QueryResponse": {"Item": [{"Id": "1", "FullyQualifiedName": "Test Product", "UnitPrice": 10.0}]}}'
        mock_response.json.return_value = {"QueryResponse": {"Item": [{"Id": "1", "FullyQualifiedName": "Test Product", "UnitPrice": 10.0}]}}
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
        mock_response.json.return_value = {"SomeOtherKey": {"Item": []}}
        mock_response.raise_for_status.return_value = None
    
        with patch('requests.get', return_value=mock_response):
            with patch.object(self.retriever, 'get_headers', return_value={'Authorization': 'Bearer test_token'}):
                with self.assertRaises(KeyError):
                    self.retriever._call_api_once()

    def test_call_api_once_missing_item_key(self):
        """Test _call_api_once when Item key is missing from QueryResponse"""
        mock_response = Mock()
        mock_response.json.return_value = {"QueryResponse": {"SomeOtherKey": []}}
        mock_response.raise_for_status.return_value = None
    
        with patch('requests.get', return_value=mock_response):
            with patch.object(self.retriever, 'get_headers', return_value={'Authorization': 'Bearer test_token'}):
                with self.assertRaises(KeyError):
                    self.retriever._call_api_once()

    def test_call_api_once_empty_item_list(self):
        """Test _call_api_once when Item list is empty"""
        mock_response = Mock()
        mock_response.json.return_value = {"QueryResponse": {"Item": []}}
        mock_response.raise_for_status.return_value = None
    
        with patch('requests.get', return_value=mock_response):
            with patch.object(self.retriever, 'get_headers', return_value={'Authorization': 'Bearer test_token'}):
                response_dict, num_items = self.retriever._call_api_once()
    
                self.assertIsInstance(response_dict, dict)
                self.assertEqual(num_items, 0)
                self.assertIn('QueryResponse', response_dict)
                self.assertIn('Item', response_dict['QueryResponse'])
                self.assertEqual(len(response_dict['QueryResponse']['Item']), 0)

    def test_call_api_once_item_key_is_none(self):
        """Test _call_api_once when Item key is None"""
        mock_response = Mock()
        mock_response.json.return_value = {"QueryResponse": {"Item": None}}
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
                with self.assertRaises(TypeError):
                    self.retriever._call_api_once()


if __name__ == '__main__':
    unittest.main() 