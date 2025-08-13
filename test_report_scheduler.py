#!/usr/bin/env python3
# pyright: reportGeneralTypeIssues=false, reportAttributeAccessIssue=false, reportArgumentType=false, reportReturnType=false, reportUnusedImport=false, reportMissingParameterType=false
"""
Test script for QBOReportScheduler
"""

import unittest
from unittest.mock import Mock, patch
from datetime import datetime
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from report_scheduler import QBOReportScheduler
from qbo_request_auth_params import QBORequestAuthParams

class TestQBOReportScheduler(unittest.TestCase):
    """Test cases for QBOReportScheduler"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.auth_params = QBORequestAuthParams()
        self.scheduler = QBOReportScheduler(self.auth_params)

    def test_generate_and_send_report_with_date(self):
        """Test generate_and_send_report_for_realm with specific report date"""
        realm_id = "test_realm"
        email = "test@example.com"
        report_date = "2025-01-15"
        
        # Mock the PricingDeltaServer to avoid actual API calls
        with patch('report_scheduler.PricingDeltaServer') as mock_pricing_delta:
            mock_server = Mock()
            mock_server.serve.return_value = True
            mock_pricing_delta.init_with_api_retrievers.return_value = mock_server
            
            # Mock the update_job_run method
            with patch.object(self.scheduler, 'update_job_run'):
                result = self.scheduler.generate_and_send_report_for_realm(realm_id, email, report_date)
                
                # Verify the result
                self.assertTrue(result)
                
                # Verify that PricingDeltaServer was called with correct parameters
                mock_pricing_delta.init_with_api_retrievers.assert_called_once()
                call_args = mock_pricing_delta.init_with_api_retrievers.call_args
                self.assertEqual(call_args[1]['realm_id'], realm_id)
                self.assertEqual(call_args[1]['email'], email)
                
                # Verify that the report_dt parameter was passed with the correct date
                report_dt_arg = call_args[1]['report_dt']
                self.assertEqual(report_dt_arg.strftime('%Y-%m-%d'), report_date)

    def test_generate_and_send_report_without_date(self):
        """Test generate_and_send_report_for_realm without report date (uses current date)"""
        realm_id = "test_realm"
        email = "test@example.com"
        
        # Mock the PricingDeltaServer to avoid actual API calls
        with patch('report_scheduler.PricingDeltaServer') as mock_pricing_delta:
            mock_server = Mock()
            mock_server.serve.return_value = True
            mock_pricing_delta.init_with_api_retrievers.return_value = mock_server
            
            # Mock the update_job_run method
            with patch.object(self.scheduler, 'update_job_run'):
                result = self.scheduler.generate_and_send_report_for_realm(realm_id, email)
                
                # Verify the result
                self.assertTrue(result)
                
                # Verify that PricingDeltaServer was called with correct parameters
                mock_pricing_delta.init_with_api_retrievers.assert_called_once()
                call_args = mock_pricing_delta.init_with_api_retrievers.call_args
                self.assertEqual(call_args[1]['realm_id'], realm_id)
                self.assertEqual(call_args[1]['email'], email)
                
                # Verify that the report_dt parameter was passed with current date
                report_dt_arg = call_args[1]['report_dt']
                current_date = datetime.now().strftime('%Y-%m-%d')
                self.assertEqual(report_dt_arg.strftime('%Y-%m-%d'), current_date)

    def test_generate_and_send_report_with_invalid_date(self):
        """Test generate_and_send_report_for_realm with invalid date format"""
        realm_id = "test_realm"
        email = "test@example.com"
        invalid_date = "invalid-date"
        
        # Test that the method raises ValueError for invalid date format
        with self.assertRaises(ValueError):
            self.scheduler.generate_and_send_report_for_realm(realm_id, email, invalid_date)

    def test_generate_and_send_report_with_malformed_date(self):
        """Test generate_and_send_report_for_realm with malformed date format"""
        realm_id = "test_realm"
        email = "test@example.com"
        malformed_date = "2025/01/15"  # Wrong format
        
        # Test that the method raises ValueError for malformed date format
        with self.assertRaises(ValueError):
            self.scheduler.generate_and_send_report_for_realm(realm_id, email, malformed_date)

    def test_generate_and_send_report_with_empty_date(self):
        """Test generate_and_send_report_for_realm with empty date string"""
        realm_id = "test_realm"
        email = "test@example.com"
        empty_date = ""
        
        # Mock the PricingDeltaServer to avoid actual API calls
        with patch('report_scheduler.PricingDeltaServer') as mock_pricing_delta:
            mock_server = Mock()
            mock_server.serve.return_value = True
            mock_pricing_delta.init_with_api_retrievers.return_value = mock_server
            
            # Mock the update_job_run method
            with patch.object(self.scheduler, 'update_job_run'):
                # Test that the method handles empty date gracefully
                result = self.scheduler.generate_and_send_report_for_realm(realm_id, email, empty_date)
                
                # Verify the result
                self.assertTrue(result)
                
                # Verify that PricingDeltaServer was called with correct parameters
                mock_pricing_delta.init_with_api_retrievers.assert_called_once()
                call_args = mock_pricing_delta.init_with_api_retrievers.call_args
                self.assertEqual(call_args[1]['realm_id'], realm_id)
                self.assertEqual(call_args[1]['email'], email)
                
                # Verify that the report_dt parameter was passed with current date (fallback)
                report_dt_arg = call_args[1]['report_dt']
                current_date = datetime.now().strftime('%Y-%m-%d')
                self.assertEqual(report_dt_arg.strftime('%Y-%m-%d'), current_date)

if __name__ == '__main__':
    unittest.main() 