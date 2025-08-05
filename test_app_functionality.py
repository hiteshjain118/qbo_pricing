#!/usr/bin/env python3
"""
Test script for app.py functionality
"""

import unittest
from unittest.mock import Mock, patch
from datetime import datetime
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class TestAppFunctionality(unittest.TestCase):
    """Test cases for app.py functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        pass

    def test_run_job_now_with_valid_report_date(self):
        """Test run_job_now endpoint with valid report date"""
        from app import app
        
        with app.test_client() as client:
            with patch('app.report_manager') as mock_report_manager:
                with patch('app.auth_manager') as mock_auth_manager:
                    # Mock the auth manager to return connected companies
                    mock_auth_manager.get_companies.return_value = [{'realm_id': 'test_realm'}]
                    mock_auth_manager.is_company_connected.return_value = True
                    
                    # Mock the report manager
                    mock_report_manager.generate_and_send_report_for_realm.return_value = True
                    
                    # Test the endpoint
                    response = client.post('/run_job_now', data={
                        'email': 'test@example.com',
                        'schedule_time': '09:00',
                        'report_date': '2025-01-15'
                    })
                    
                    # Verify the response
                    self.assertEqual(response.status_code, 302)  # Redirect
                    
                    # Verify that the report manager was called with correct parameters
                    mock_report_manager.generate_and_send_report_for_realm.assert_called_once_with(
                        'test_realm', 'test@example.com', '2025-01-15'
                    )

    def test_run_job_now_without_report_date(self):
        """Test run_job_now endpoint without report date"""
        from app import app
        
        with app.test_client() as client:
            with patch('app.report_manager') as mock_report_manager:
                with patch('app.auth_manager') as mock_auth_manager:
                    # Mock the auth manager to return connected companies
                    mock_auth_manager.get_companies.return_value = [{'realm_id': 'test_realm'}]
                    mock_auth_manager.is_company_connected.return_value = True
                    
                    # Mock the report manager
                    mock_report_manager.generate_and_send_report_for_realm.return_value = True
                    
                    # Test the endpoint
                    response = client.post('/run_job_now', data={
                        'email': 'test@example.com',
                        'schedule_time': '09:00'
                        # No report_date
                    })
                    
                    # Verify the response
                    self.assertEqual(response.status_code, 302)  # Redirect
                    
                    # Verify that the report manager was called with None for report_date
                    mock_report_manager.generate_and_send_report_for_realm.assert_called_once_with(
                        'test_realm', 'test@example.com', None
                    )

    def test_run_job_now_with_invalid_report_date(self):
        """Test run_job_now endpoint with invalid report date"""
        from app import app
        
        with app.test_client() as client:
            with patch('app.report_manager') as mock_report_manager:
                with patch('app.auth_manager') as mock_auth_manager:
                    # Mock the auth manager to return connected companies
                    mock_auth_manager.get_companies.return_value = [{'realm_id': 'test_realm'}]
                    mock_auth_manager.is_company_connected.return_value = True
                    
                    # Mock the report manager to raise ValueError for invalid date
                    mock_report_manager.generate_and_send_report_for_realm.side_effect = ValueError("Invalid date format")
                    
                    # Test the endpoint
                    response = client.post('/run_job_now', data={
                        'email': 'test@example.com',
                        'schedule_time': '09:00',
                        'report_date': 'invalid-date'
                    })
                    
                    # Verify the response
                    self.assertEqual(response.status_code, 302)  # Redirect
                    
                    # Verify that the report manager was called with the invalid date
                    mock_report_manager.generate_and_send_report_for_realm.assert_called_once_with(
                        'test_realm', 'test@example.com', 'invalid-date'
                    )

    def test_run_job_now_with_malformed_report_date(self):
        """Test run_job_now endpoint with malformed report date"""
        from app import app
        
        with app.test_client() as client:
            with patch('app.report_manager') as mock_report_manager:
                with patch('app.auth_manager') as mock_auth_manager:
                    # Mock the auth manager to return connected companies
                    mock_auth_manager.get_companies.return_value = [{'realm_id': 'test_realm'}]
                    mock_auth_manager.is_company_connected.return_value = True
                    
                    # Mock the report manager to raise ValueError for malformed date
                    mock_report_manager.generate_and_send_report_for_realm.side_effect = ValueError("Invalid date format")
                    
                    # Test the endpoint
                    response = client.post('/run_job_now', data={
                        'email': 'test@example.com',
                        'schedule_time': '09:00',
                        'report_date': '2025/01/15'
                    })
                    
                    # Verify the response
                    self.assertEqual(response.status_code, 302)  # Redirect
                    
                    # Verify that the report manager was called with the malformed date
                    mock_report_manager.generate_and_send_report_for_realm.assert_called_once_with(
                        'test_realm', 'test@example.com', '2025/01/15'
                    )

    def test_index_route_with_today_date(self):
        """Test index route provides today_date to template"""
        from app import app
        
        with app.test_client() as client:
            with patch('app.auth_manager') as mock_auth_manager:
                with patch('app.report_manager') as mock_report_manager:
                    # Mock the auth manager to return connected companies
                    mock_auth_manager.get_companies.return_value = [{'realm_id': 'test_realm'}]
                    mock_auth_manager.is_company_connected.return_value = True
                    
                    # Mock the report manager to return an existing job
                    mock_report_manager.get_job_for_realm.return_value = {
                        'realm_id': 'test_realm',
                        'email': 'test@example.com',
                        'schedule_time': '09:00',
                        'next_run': '2025-01-15T09:00:00',
                        'last_run': '2025-01-14T09:00:00',
                        'is_connected': True
                    }
                    
                    # Test the endpoint
                    response = client.get('/')
                    
                    # Verify the response
                    self.assertEqual(response.status_code, 200)
                    
                    # Verify that today_date is in the response
                    response_text = response.get_data(as_text=True)
                    today_date = datetime.now().strftime('%Y-%m-%d')
                    self.assertIn(today_date, response_text)

    def test_configure_job_with_valid_report_date(self):
        """Test configure_job endpoint with valid report date"""
        from app import app
        
        with app.test_client() as client:
            with patch('app.auth_manager') as mock_auth_manager:
                with patch('app.report_manager') as mock_report_manager:
                    # Mock the auth manager to return connected companies
                    mock_auth_manager.get_companies.return_value = [{'realm_id': 'test_realm'}]
                    mock_auth_manager.is_company_connected.return_value = True
                    
                    # Mock the report manager
                    mock_report_manager.store_job_config.return_value = None
                    
                    # Test the endpoint
                    response = client.post('/configure', data={
                        'email': 'test@example.com',
                        'schedule_time': '09:00',
                        'user_timezone': 'UTC'
                    })
                    
                    # Verify the response
                    self.assertEqual(response.status_code, 302)  # Redirect
                    
                    # Verify that the job config was stored
                    mock_report_manager.store_job_config.assert_called_once()

if __name__ == '__main__':
    unittest.main() 