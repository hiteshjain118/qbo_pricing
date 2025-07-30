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
import intent_servers.balance_sheet_server as balance_sheet_server
from intent_servers.pricing_delta_server import PricingDeltaServer
from qbo_balance_sheet_getter import QBOBalanceSheetGetter
from oauth_manager import QBOOAuthManager
from qbo_request_auth_params import QBORequestAuthParams
from intent_servers.balance_sheet_server import BalanceSheetServer
from logging_config import setup_logging
from database import DB

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

class QBOReportScheduler:
    """Manages QBO report generation and job scheduling"""
    
    def __init__(self, auth_params: QBORequestAuthParams):
        self.auth_manager = QBOOAuthManager(auth_params)
    
    def store_job_config(self, realm_id: str, email: str, schedule_time: str):
        """Store job configuration for a company in database"""
        try:
            db = DB.get_session()
            
            # Check if job already exists
            existing_job = db.query(DB.get_job_model()).filter(DB.get_job_model().realm_id == realm_id).first()
            
            next_run = self.calculate_next_run_datetime(schedule_time)
            
            if existing_job:
                # Update existing job
                existing_job.email = email
                existing_job.schedule_time = schedule_time
                existing_job.next_run = next_run
            else:
                # Create new job
                new_job = DB.get_job_model()(
                    realm_id=realm_id,
                    email=email,
                    schedule_time=schedule_time,
                    next_run=next_run
                )
                db.add(new_job)
            
            db.commit()
            logger.info(f"Stored job config for company {realm_id} in database")
            
        except Exception as e:
            logger.error(f"Error storing job config for company {realm_id}: {e}")
            if db:
                db.rollback()
        finally:
            db.close()
    
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
            db = DB.get_session()
            now = datetime.now()
            
            # Get jobs where next_run is in the past
            jobs = db.query(DB.get_job_model()).filter(DB.get_job_model().next_run <= now).all()
            
            jobs_to_run = []
            for job in jobs:
                jobs_to_run.append({
                    'realm_id': job.realm_id,
                    'email': job.email,
                    'schedule_time': job.schedule_time
                })
            
            return jobs_to_run
        except Exception as e:
            logger.error(f"Error getting jobs to run: {e}")
            return []
        finally:
            db.close()
    
    def update_job_run(self, realm_id: str):
        """Update job run information in database"""
        try:
            db = DB.get_session()
            job = db.query(DB.get_job_model()).filter(DB.get_job_model().realm_id == realm_id).first()
            
            if job:
                job.last_run = datetime.now()
                job.next_run = self.calculate_next_run_datetime(job.schedule_time)
                db.commit()
                logger.info(f"Updated job run for company {realm_id}")
            
        except Exception as e:
            logger.error(f"Error updating job run for company {realm_id}: {e}")
            if db:
                db.rollback()
        finally:
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
            self.generate_and_send_report_for_realm(realm_id, email)
            
    
    def generate_and_send_report_for_realm(self, realm_id: str, email: str) -> bool:
        """Generate and send report for immediate execution"""
        print(f"Generating report for company {realm_id}")
        
        # success = BalanceSheetServer(self.auth_manager.params, realm_id).generate_and_send_report(email)
        success = PricingDeltaServer(self.auth_manager.params, realm_id).generate_and_send_report(email)
        if success:
            self.update_job_run(realm_id)
        return success
      
    def get_job_for_realm(self, realm_id: str) -> Optional[Dict[str, Any]]:
        """Get job configuration for a specific realm from database"""
        try:
            db = DB.get_session()
            job = db.query(DB.get_job_model()).filter(DB.get_job_model().realm_id == realm_id).first()
            
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
        finally:
            db.close()
    
    def delete_job(self, realm_id: str) -> bool:
        """Delete a job configuration from database"""
        was_deleted = False
        try:
            db = DB.get_session()
            job = db.query(DB.get_job_model()).filter(DB.get_job_model().realm_id == realm_id).first()

            if job:
                db.delete(job)
                db.commit()
                logger.info(f"Deleted job for company {realm_id}")
                was_deleted = True
            else:
                was_deleted = False
        except Exception as e:
            logger.error(f"Error deleting job for company {realm_id}: {e}")
            if db:
                db.rollback()
        finally:
            db.close()
            return was_deleted 