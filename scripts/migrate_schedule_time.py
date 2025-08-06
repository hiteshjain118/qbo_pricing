#!/usr/bin/env python3
"""
Migration script to convert schedule_time from string to datetime
"""

import os
import sys
from datetime import datetime, time
import pytz

# Add parent directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import DB

def migrate_schedule_time():
    """Migrate schedule_time from string to datetime"""
    try:
        db = DB.get_session()
        
        # Get all jobs
        jobs = db.query(DB.get_job_model()).all()
        
        print(f"Found {len(jobs)} jobs to migrate")
        
        for job in jobs:
            print(f"Migrating job {job.id} for realm {job.realm_id}")
            print(f"  Current schedule_time: {job.schedule_time} (type: {type(job.schedule_time)})")
            
            if isinstance(job.schedule_time, str):
                # Parse the time string (e.g., "17:00")
                try:
                    hour, minute = map(int, job.schedule_time.split(':'))
                    
                    # Create a datetime object for today with the specified time
                    pacific_tz = pytz.timezone('America/Los_Angeles')
                    today = datetime.now(pacific_tz).date()
                    schedule_datetime = pacific_tz.localize(datetime.combine(today, time(hour, minute)))
                    
                    # Update the job
                    job.schedule_time = schedule_datetime
                    print(f"  Converted to: {schedule_datetime}")
                    
                except Exception as e:
                    print(f"  Error converting {job.schedule_time}: {e}")
                    continue
            else:
                print(f"  Already datetime: {job.schedule_time}")
        
        # Commit the changes
        db.commit()
        print("Migration completed successfully!")
        
    except Exception as e:
        print(f"Error during migration: {e}")
        if db:
            db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    print("Starting schedule_time migration...")
    migrate_schedule_time() 