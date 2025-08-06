#!/usr/bin/env python3
"""
Debug script to check raw timezone values in the database
"""

import os
import sys
import pytz
from datetime import datetime

# Add the parent directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import DB
from sqlalchemy import text

def debug_timezone():
    """Debug timezone values in the database"""
    try:
        db = DB.get_session()
        
        # Check production jobs
        print("🔍 DEBUGGING TIMEZONE VALUES")
        print("=" * 50)
        
        result = db.execute(text("SELECT id, schedule_time, next_run, last_run FROM qbo_jobs_production"))
        jobs = result.fetchall()
        
        for job in jobs:
            job_id, schedule_time, next_run, last_run = job
            print(f"\n📊 Job ID: {job_id}")
            print(f"Schedule Time (raw): {schedule_time} (type: {type(schedule_time).__name__})")
            print(f"Next Run (raw): {next_run} (type: {type(next_run).__name__})")
            print(f"Last Run (raw): {last_run} (type: {type(last_run).__name__})")
            
            if schedule_time:
                print(f"Schedule Time tzinfo: {schedule_time.tzinfo}")
                print(f"Schedule Time UTC: {schedule_time.utctimetuple() if hasattr(schedule_time, 'utctimetuple') else 'N/A'}")
            
            if next_run:
                print(f"Next Run tzinfo: {next_run.tzinfo}")
                print(f"Next Run UTC: {next_run.utctimetuple() if hasattr(next_run, 'utctimetuple') else 'N/A'}")
                
                # Convert to different timezones for comparison
                pacific_tz = pytz.timezone('America/Los_Angeles')
                if next_run.tzinfo is None:
                    print(f"Next Run (naive) - assuming UTC: {pytz.utc.localize(next_run).astimezone(pacific_tz)}")
                else:
                    print(f"Next Run (aware) - Pacific: {next_run.astimezone(pacific_tz)}")
                    print(f"Next Run (aware) - UTC: {next_run.astimezone(pytz.UTC)}")
        
        # Check current time in different timezones
        print(f"\n⏰ CURRENT TIME COMPARISON:")
        print(f"UTC now: {datetime.now(pytz.UTC)}")
        print(f"PST now: {datetime.now(pytz.timezone('America/Los_Angeles'))}")
        print(f"Pacific now: {datetime.now(pytz.timezone('US/Pacific'))}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    debug_timezone() 