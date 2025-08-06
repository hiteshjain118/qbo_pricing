#!/usr/bin/env python3
"""
Migration script to convert schedule_time column in sandbox tables from VARCHAR to TIMESTAMP WITH TIME ZONE.
This script handles the data conversion for both qbo_jobs_sandbox table.
"""

import os
import sys
import pytz
from datetime import datetime, time
from sqlalchemy import text

# Add the parent directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import DB

def get_table_name(base_name):
    """Get the actual table name based on environment"""
    # For sandbox tables, we use the base name directly
    return base_name

def migrate_sandbox_schedule_time():
    """Migrate schedule_time column in sandbox tables from VARCHAR to TIMESTAMP WITH TIME ZONE"""
    db = None
    try:
        db = DB.get_session()
        
        # Migrate qbo_jobs_sandbox table
        table_name = get_table_name('qbo_jobs_sandbox')
        print(f"Migrating schedule_time column for table: {table_name}")
        
        # Step 1: Add a new column with the correct type
        print("Step 1: Adding new schedule_time_new column...")
        db.execute(text(f"ALTER TABLE {table_name} ADD COLUMN schedule_time_new TIMESTAMP WITH TIME ZONE"))
        
        # Step 2: Get all existing records
        print("Step 2: Fetching existing records...")
        result = db.execute(text(f"SELECT id, schedule_time FROM {table_name}"))
        jobs = result.fetchall()
        print(f"Found {len(jobs)} records to migrate")
        
        # Step 3: Convert and update each record
        print("Step 3: Converting and updating records...")
        for job_id, schedule_time_str in jobs:
            if schedule_time_str:
                try:
                    # Parse the time string (e.g., "17:00")
                    hour, minute = map(int, schedule_time_str.split(':'))
                    
                    # Create a datetime object for today with the specified time
                    pacific_tz = pytz.timezone('America/Los_Angeles')
                    today = datetime.now(pacific_tz).date()
                    schedule_datetime = pacific_tz.localize(datetime.combine(today, time(hour, minute)))
                    
                    # Update the new column
                    db.execute(
                        text(f"UPDATE {table_name} SET schedule_time_new = :schedule_datetime WHERE id = :job_id"),
                        {
                            'schedule_datetime': schedule_datetime,
                            'job_id': job_id
                        }
                    )
                    print(f"  Converted job {job_id}: '{schedule_time_str}' -> {schedule_datetime}")
                    
                except Exception as e:
                    print(f"  Error converting job {job_id} with schedule_time '{schedule_time_str}': {e}")
                    continue
            else:
                print(f"  Skipping job {job_id}: schedule_time is NULL")
        
        # Step 4: Drop the old column
        print("Step 4: Dropping old schedule_time column...")
        db.execute(text(f"ALTER TABLE {table_name} DROP COLUMN schedule_time"))
        
        # Step 5: Rename the new column
        print("Step 5: Renaming new column to schedule_time...")
        db.execute(text(f"ALTER TABLE {table_name} RENAME COLUMN schedule_time_new TO schedule_time"))
        
        # Commit the changes
        db.commit()
        print("✅ Migration completed successfully!")
        
        # Step 6: Verify the migration
        print("Step 6: Verifying migration...")
        result = db.execute(text(f"SELECT id, schedule_time FROM {table_name}"))
        migrated_jobs = result.fetchall()
        
        print(f"\n📊 Verification Results:")
        print(f"Total records: {len(migrated_jobs)}")
        for job_id, schedule_time in migrated_jobs:
            if schedule_time:
                print(f"  Job {job_id}: {schedule_time} (type: {type(schedule_time).__name__})")
            else:
                print(f"  Job {job_id}: NULL")
        
        # Check column type
        result = db.execute(text(f"""
            SELECT column_name, data_type, is_nullable 
            FROM information_schema.columns 
            WHERE table_name = '{table_name}' AND column_name = 'schedule_time'
        """))
        column_info = result.fetchone()
        if column_info:
            print(f"\nColumn type: {column_info[1]} (nullable: {column_info[2]})")
        
    except Exception as e:
        print(f"❌ Error during migration: {e}")
        if db:
            db.rollback()
        raise
    finally:
        if db:
            db.close()

if __name__ == "__main__":
    print("🔄 Starting sandbox schedule_time migration...")
    print("=" * 60)
    migrate_sandbox_schedule_time()
    print("\n✅ Migration script completed!") 