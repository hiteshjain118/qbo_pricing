#!/usr/bin/env python3
"""
Comprehensive migration script to convert schedule_time from VARCHAR to TIMESTAMP
"""

import os
import sys
from datetime import datetime, time
import pytz
from sqlalchemy import text

# Add parent directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import DB

def migrate_column_with_data():
    """Migrate schedule_time column with data conversion"""
    try:
        db = DB.get_session()
        
        # Get the table name based on environment
        from database import get_table_name
        table_name = get_table_name('qbo_jobs')
        
        print(f"Migrating column for table: {table_name}")
        
        # Step 1: Add a new column with the correct type
        print("Step 1: Adding new column...")
        db.execute(text(f"""
            ALTER TABLE {table_name} 
            ADD COLUMN schedule_time_new TIMESTAMP WITH TIME ZONE
        """))
        
        # Step 2: Convert existing data
        print("Step 2: Converting existing data...")
        result = db.execute(text(f"SELECT id, schedule_time FROM {table_name}"))
        jobs = result.fetchall()
        
        for job_id, schedule_time_str in jobs:
            print(f"Converting job {job_id}: {schedule_time_str}")
            
            if schedule_time_str:
                try:
                    # Parse the time string (e.g., "17:00")
                    hour, minute = map(int, schedule_time_str.split(':'))
                    
                    # Create a datetime object for today with the specified time
                    pacific_tz = pytz.timezone('America/Los_Angeles')
                    today = datetime.now(pacific_tz).date()
                    schedule_datetime = pacific_tz.localize(datetime.combine(today, time(hour, minute)))
                    
                    # Update the new column
                    db.execute(text(f"""
                        UPDATE {table_name} 
                        SET schedule_time_new = :schedule_datetime 
                        WHERE id = :job_id
                    """), {
                        'schedule_datetime': schedule_datetime,
                        'job_id': job_id
                    })
                    
                    print(f"  Converted to: {schedule_datetime}")
                    
                except Exception as e:
                    print(f"  Error converting {schedule_time_str}: {e}")
                    continue
        
        # Step 3: Drop the old column and rename the new one
        print("Step 3: Dropping old column and renaming new column...")
        db.execute(text(f"ALTER TABLE {table_name} DROP COLUMN schedule_time"))
        db.execute(text(f"ALTER TABLE {table_name} RENAME COLUMN schedule_time_new TO schedule_time"))
        
        db.commit()
        print("Migration completed successfully!")
        
        # Step 4: Verify the change
        print("Step 4: Verifying the change...")
        result = db.execute(text(f"""
            SELECT column_name, data_type, character_maximum_length 
            FROM information_schema.columns 
            WHERE table_name = '{table_name}' AND column_name = 'schedule_time'
        """))
        
        column_info = result.fetchone()
        if column_info:
            print(f"New column definition: {column_info}")
        
        # Step 5: Test reading the data
        print("Step 5: Testing data reading...")
        result = db.execute(text(f"SELECT id, schedule_time FROM {table_name}"))
        jobs = result.fetchall()
        
        for job_id, schedule_time in jobs:
            print(f"Job {job_id}: {schedule_time} (type: {type(schedule_time)})")
        
    except Exception as e:
        print(f"Error during migration: {e}")
        if db:
            db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    print("Starting comprehensive column migration...")
    migrate_column_with_data() 