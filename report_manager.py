#!/usr/bin/env python3
"""
QBO Report Manager

Handles balance sheet queries, job scheduling, and report generation
"""

import os
import json
import smtplib
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import balance_sheet_intent_server
from qbo_api import QuickBooksOnlineAPI
from auth_manager import QBOAuthManager
from qbo_request_auth_params import QBORequestAuthParams
from balance_sheet_intent_server import BalancesheetIntentServer
from logging_config import setup_logging

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

# Data storage file
JOBS_FILE = "data/qbo_jobs.json"

class QBOReportManager:
    """Manages QBO report generation and job scheduling"""
    
    def __init__(self, auth_params: QBORequestAuthParams):
        self.auth_manager = QBOAuthManager(auth_params)
        self.jobs = self.load_jobs()
    
    def load_jobs(self) -> Dict[str, Any]:
        """Load job configurations from file"""
        try:
            with open(JOBS_FILE, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}
    
    def save_jobs(self):
        """Save job configurations to file"""
        # Ensure data directory exists
        os.makedirs(os.path.dirname(JOBS_FILE), exist_ok=True)
        with open(JOBS_FILE, 'w') as f:
            json.dump(self.jobs, f, indent=2)
    
    def store_job_config(self, realm_id: str, email: str, schedule_time: str):
        """Store job configuration for a company"""
        self.jobs[realm_id] = {
            'realm_id': realm_id,
            'email': email,
            'schedule_time': schedule_time,
            'created_at': datetime.now().isoformat(),
            'last_run': None,
            'next_run': self.calculate_next_run(schedule_time)
        }
        self.save_jobs()
    
    def calculate_next_run(self, schedule_time: str) -> str:
        """Calculate next run time based on schedule"""
        now = datetime.now()
        hour, minute = map(int, schedule_time.split(':'))
        next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        
        if next_run <= now:
            next_run += timedelta(days=1)
        
        return next_run.isoformat()
    
    def get_jobs_to_run(self) -> List[Dict[str, Any]]:
        """Get jobs that need to be executed"""
        jobs_to_run = []
        now = datetime.now()
        
        for realm_id, job_config in self.jobs.items():
            next_run = job_config.get('next_run')
            if next_run:
                try:
                    next_run_dt = datetime.fromisoformat(next_run)
                    if now >= next_run_dt:
                        jobs_to_run.append({
                            'realm_id': realm_id,
                            'email': job_config['email'],
                            'schedule_time': job_config['schedule_time']
                        })
                except ValueError:
                    continue
        
        return jobs_to_run
    
    def update_job_run(self, realm_id: str):
        """Update job run information"""
        if realm_id in self.jobs:
            self.jobs[realm_id]['last_run'] = datetime.now().isoformat()
            self.jobs[realm_id]['next_run'] = self.calculate_next_run(
                self.jobs[realm_id]['schedule_time']
            )
            self.save_jobs()
        
    def run_scheduled_jobs(self):
        """Run all scheduled jobs"""
        print("=== Running Scheduled Jobs ===")
        
        jobs_to_run = self.get_jobs_to_run()
        
        if not jobs_to_run:
            print("No jobs to run")
            return
        
        for job in jobs_to_run:
            realm_id = job['realm_id']
            email = job['email']
            
            print(f"Processing job for company {realm_id}")
            
            # Check if company is still connected
            if not self.auth_manager.is_company_connected(realm_id):
                print(f"Company {realm_id} is no longer connected, skipping job")
                continue
            
            # Generate and send report
            resend_api_key = os.getenv('RESEND_API_KEY')
            if not resend_api_key:
                print("❌ RESEND_API_KEY environment variable not set")
                continue
            BalancesheetIntentServer(self.auth_manager, realm_id, resend_api_key).generate_and_send_report(email)
    
    def generate_and_send_report(self, realm_id: str, email: str) -> bool:
        """Generate and send report for immediate execution"""
        print(f"Generating report for company {realm_id}")
        
        # Check if company is still connected
        if not self.auth_manager.is_company_connected(realm_id):
            print(f"Company {realm_id} is no longer connected")
            return False
        
        # Get Resend API key
        resend_api_key = os.getenv('RESEND_API_KEY')
        if not resend_api_key:
            print("❌ RESEND_API_KEY environment variable not set")
            return False
        
        # Generate and send report
        # try:
        success = BalancesheetIntentServer(self.auth_manager, realm_id, resend_api_key).generate_and_send_report(email)
        if success:
            self.update_job_run(realm_id)
        return success
        # except Exception as e:
        #     logger.error(f"❌ Error generating and sending report: {e}")
        #     raise e
        #     return False
      
    def get_job_for_realm(self, realm_id: str) -> Optional[Dict[str, Any]]:
        """Get job configuration for a specific realm"""
        if realm_id in self.jobs:
            job_config = self.jobs[realm_id]
            return {
                'realm_id': realm_id,
                'email': job_config['email'],
                'schedule_time': job_config['schedule_time'],
                'next_run': job_config['next_run'],
                'last_run': job_config['last_run'],
                'is_connected': self.auth_manager.is_company_connected(realm_id)
            }
        return None
    
    def delete_job(self, realm_id: str) -> bool:
        """Delete a job configuration"""
        if realm_id in self.jobs:
            del self.jobs[realm_id]
            self.save_jobs()
            return True
        return False 