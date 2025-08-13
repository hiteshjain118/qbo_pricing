#!/usr/bin/env python3
# pyright: reportGeneralTypeIssues=false, reportAttributeAccessIssue=false, reportArgumentType=false, reportReturnType=false, reportUnusedImport=false
"""
QBO Report Manager

Handles balance sheet queries, job scheduling, and report generation
"""

from datetime import datetime, time, timedelta
from typing import List, Dict, Any, Optional
import pytz
import time


from database import DB
from oauth_manager import QBOOAuthManager
from qbo_request_auth_params import QBORequestAuthParams
from qbo_pricing_delta.pricing_delta_server import PricingDeltaServer
from core.logging_config import setup_logging
import logging



# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

class CompanyReportConfig:
    def __init__(self, realm_id: str, email: str, daily_schedule_time: str, user_timezone: str):
        self.realm_id = realm_id
        self.email = email
        self.daily_schedule_time = daily_schedule_time
        self.user_timezone = user_timezone
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'realm_id': self.realm_id,
            'email': self.email,
            'daily_schedule_time': self.daily_schedule_time,
            'user_timezone': self.user_timezone
        }

class QBOReportScheduler:
    """Manages QBO report generation and job scheduling"""
    
    def __init__(self, auth_params: QBORequestAuthParams):
        self.auth_manager = QBOOAuthManager(auth_params)
    
    def store_job_config(self, realm_id: str, email: str, schedule_time: datetime):
        """Store job configuration for a company in database"""
        try:
            db = DB.get_session()
            
            # Check if job already exists
            existing_job = db.query(DB.get_job_model()).filter(DB.get_job_model().realm_id == realm_id).first()
                        
            if existing_job:
                # Update existing job
                existing_job.email = email 
                # format is hh:mm
                existing_job.daily_schedule_time = f"{schedule_time.hour:02d}:{schedule_time.minute:02d}"
                existing_job.user_timezone = "America/Los_Angeles"
                existing_job.created_at_ts = int(time.time())
            else:
                # Create new job
                new_job = DB.get_job_model()(
                    realm_id=realm_id,
                    email=email,
                    daily_schedule_time=f"{schedule_time.hour:02d}:{schedule_time.minute:02d}",
                    user_timezone="America/Los_Angeles",  # Default to Pacific timezone
                    created_at_ts=int(time.time())
                )
                db.add(new_job)
            
            db.commit()
            logger.info(f"Stored job config for company {realm_id} in database. Schedule time: {schedule_time}")
            
        except Exception as e:
            logger.error(f"Error storing job config for company {realm_id}: {e}")
            if db:
                db.rollback()
        finally:
            db.close()    

    def is_last_run_expired(self, last_run: int, daily_schedule_time: str, user_timezone: str) -> bool:
        """Check if the last run is expired"""
        #convert last run from timestamp to user's timezone and compare with daily_schedule_time
        last_run_user_timezone = datetime.fromtimestamp(last_run).astimezone(pytz.timezone(user_timezone))
        # daily_schedule_time format is hh:mm
        return last_run_user_timezone.strftime("%H:%M") < daily_schedule_time
        
    def get_jobs_to_run(self) -> List[CompanyReportConfig]:
        """Get jobs that need to be executed from database"""
        try:
            db = DB.get_session()
            
            # Get all jobs and filter them in Python
            jobs = db.query(DB.get_job_model()).all()
            
            jobs_to_run = []
            
            for job in jobs:
                # Check if this job needs to run
                if job.last_run_ts is None or self.is_last_run_expired(job.last_run_ts, job.daily_schedule_time, job.user_timezone):
                    jobs_to_run.append(CompanyReportConfig(
                        realm_id=job.realm_id,
                        email=job.email,
                        daily_schedule_time=job.daily_schedule_time,
                        user_timezone=job.user_timezone
                    ))
            
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
                job.last_run_ts = time.time()
                db.commit()
                logger.info(f"Updated job run for company {realm_id}, last run: {job.last_run_ts}, schedule time: {job.daily_schedule_time}")
            
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
            print(f"Processing job for company {job.realm_id}")
            self.generate_and_send_report_for_company_config(job, report_date=None)
            
    
    
    def get_job_for_realm(self, realm_id: str) -> Optional[CompanyReportConfig]:
        """Get job configuration for a specific realm from database"""
        try:
            db = DB.get_session()
            job = db.query(DB.get_job_model()).filter(DB.get_job_model().realm_id == realm_id).first()
            
            if job:
                return CompanyReportConfig(
                    realm_id=realm_id,
                    email=job.email,
                    daily_schedule_time=job.daily_schedule_time,
                    user_timezone=job.user_timezone
                )
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
        
    
    def generate_and_send_report_for_realm(self, realm_id: str, report_date: str) -> bool:
        """Generate and send report for immediate execution"""
        company_report_config = self.get_job_for_realm(realm_id)
        if not company_report_config:
            print(f"No job found for company {realm_id}")
            return False
        
        return self.generate_and_send_report_for_company_config(company_report_config, report_date)
    
    def generate_and_send_report_for_company_config(self, company_report_config: CompanyReportConfig, report_date: str) -> bool:
        
        # Parse report_date if provided, otherwise use current date
        if report_date:
            report_dt = datetime.strptime(report_date, "%Y-%m-%d")
        else:
            report_dt = datetime.now(pytz.timezone(company_report_config.user_timezone))
    
        print(f"Generating report for company {company_report_config.realm_id}, email: {company_report_config.email} report_date: {report_dt}")
        
        success = PricingDeltaServer.init_with_api_retrievers(
            auth_params=self.auth_manager.params, 
            realm_id=company_report_config.realm_id, 
            email=company_report_config.email,
            report_dt=report_dt
        ).serve()
        
        if success:
            self.update_job_run(company_report_config.realm_id)
        return success