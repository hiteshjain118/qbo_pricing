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
from database import get_db_session, QBOJob, init_database

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

# Data storage file
JOBS_FILE = "data/qbo_jobs.json"

class QBOReportManager:
    """Manages QBO report generation and job scheduling"""
    
    def __init__(self, auth_params: QBORequestAuthParams):
        self.auth_manager = QBOAuthManager(auth_params)
        # Initialize database
        init_database()
        logger.info("Database initialized for report manager")
    
    def load_jobs(self) -> Dict[str, Any]:
        """Load job configurations from database"""
        try:
            db = get_db_session()
            jobs = db.query(QBOJob).all()
            jobs_dict = {}
            for job in jobs:
                jobs_dict[job.realm_id] = {
                    'realm_id': job.realm_id,
                    'email': job.email,
                    'schedule_time': job.schedule_time,
                    'next_run': job.next_run.isoformat() if job.next_run else None,
                    'last_run': job.last_run.isoformat() if job.last_run else None
                }
            db.close()
            return jobs_dict
        except Exception as e:
            logger.error(f"Error loading jobs from database: {e}")
            return {}
    
    def save_jobs(self):
        """Save job configurations to database"""
        # This method is kept for compatibility but jobs are saved directly
        # when store_job_config is called
        pass
    
    def store_job_config(self, realm_id: str, email: str, schedule_time: str):
        """Store job configuration for a company in database"""
        try:
            db = get_db_session()
            
            # Check if job already exists
            existing_job = db.query(QBOJob).filter(QBOJob.realm_id == realm_id).first()
            
            next_run = self.calculate_next_run_datetime(schedule_time)
            
            if existing_job:
                # Update existing job
                existing_job.email = email
                existing_job.schedule_time = schedule_time
                existing_job.next_run = next_run
            else:
                # Create new job
                new_job = QBOJob(
                    realm_id=realm_id,
                    email=email,
                    schedule_time=schedule_time,
                    next_run=next_run
                )
                db.add(new_job)
            
            db.commit()
            db.close()
            logger.info(f"Stored job config for company {realm_id} in database")
            
        except Exception as e:
            logger.error(f"Error storing job config for company {realm_id}: {e}")
            if db:
                db.rollback()
                db.close()
    
    def calculate_next_run(self, schedule_time: str) -> str:
        """Calculate next run time based on schedule"""
        next_run_dt = self.calculate_next_run_datetime(schedule_time)
        return next_run_dt.isoformat()
    
    def calculate_next_run_datetime(self, schedule_time: str) -> datetime:
        """Calculate next run time as datetime object"""
        now = datetime.now()
        hour, minute = map(int, schedule_time.split(':'))
        next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        
        if next_run <= now:
            next_run += timedelta(days=1)
        
        return next_run
    
    def get_jobs_to_run(self) -> List[Dict[str, Any]]:
        """Get jobs that need to be executed from database"""
        try:
            db = get_db_session()
            now = datetime.now()
            
            # Get jobs where next_run is in the past
            jobs = db.query(QBOJob).filter(QBOJob.next_run <= now).all()
            
            jobs_to_run = []
            for job in jobs:
                jobs_to_run.append({
                    'realm_id': job.realm_id,
                    'email': job.email,
                    'schedule_time': job.schedule_time
                })
            
            db.close()
            return jobs_to_run
        except Exception as e:
            logger.error(f"Error getting jobs to run: {e}")
            return []
    
    def update_job_run(self, realm_id: str):
        """Update job run information in database"""
        try:
            db = get_db_session()
            job = db.query(QBOJob).filter(QBOJob.realm_id == realm_id).first()
            
            if job:
                job.last_run = datetime.now()
                job.next_run = self.calculate_next_run_datetime(job.schedule_time)
                db.commit()
                logger.info(f"Updated job run for company {realm_id}")
            
            db.close()
        except Exception as e:
            logger.error(f"Error updating job run for company {realm_id}: {e}")
            if db:
                db.rollback()
                db.close()
        
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
        """Get job configuration for a specific realm from database"""
        try:
            db = get_db_session()
            job = db.query(QBOJob).filter(QBOJob.realm_id == realm_id).first()
            db.close()
            
            if job:
                return {
                    'realm_id': realm_id,
                    'email': job.email,
                    'schedule_time': job.schedule_time,
                    'next_run': job.next_run.isoformat() if job.next_run else None,
                    'last_run': job.last_run.isoformat() if job.last_run else None,
                    'is_connected': self.auth_manager.is_company_connected(realm_id)
                }
            return None
        except Exception as e:
            logger.error(f"Error getting job for realm {realm_id}: {e}")
            return None
    
    def delete_job(self, realm_id: str) -> bool:
        """Delete a job configuration from database"""
        try:
            db = get_db_session()
            job = db.query(QBOJob).filter(QBOJob.realm_id == realm_id).first()
            
            if job:
                db.delete(job)
                db.commit()
                db.close()
                logger.info(f"Deleted job for company {realm_id}")
                return True
            else:
                db.close()
                return False
        except Exception as e:
            logger.error(f"Error deleting job for company {realm_id}: {e}")
            if db:
                db.rollback()
                db.close()
            return False 