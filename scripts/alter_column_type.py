#!/usr/bin/env python3
"""
Script to alter schedule_time column from VARCHAR to TIMESTAMP
"""

import os
import sys
from sqlalchemy import text

# Add parent directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import DB

def alter_column_type():
    """Alter schedule_time column from VARCHAR to TIMESTAMP"""
    try:
        db = DB.get_session()
        
        # Get the table name based on environment
        from database import get_table_name
        table_name = get_table_name('qbo_jobs')
        
        print(f"Altering column type for table: {table_name}")
        
        # First, let's see the current column definition
        result = db.execute(text(f"""
            SELECT column_name, data_type, character_maximum_length 
            FROM information_schema.columns 
            WHERE table_name = '{table_name}' AND column_name = 'schedule_time'
        """))
        
        column_info = result.fetchone()
        if column_info:
            print(f"Current column definition: {column_info}")
        
        # Alter the column type
        print("Altering column type...")
        db.execute(text(f"""
            ALTER TABLE {table_name} 
            ALTER COLUMN schedule_time TYPE TIMESTAMP WITH TIME ZONE
        """))
        
        db.commit()
        print("Column type altered successfully!")
        
        # Verify the change
        result = db.execute(text(f"""
            SELECT column_name, data_type, character_maximum_length 
            FROM information_schema.columns 
            WHERE table_name = '{table_name}' AND column_name = 'schedule_time'
        """))
        
        column_info = result.fetchone()
        if column_info:
            print(f"New column definition: {column_info}")
        
    except Exception as e:
        print(f"Error altering column: {e}")
        if db:
            db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    print("Starting column type alteration...")
    alter_column_type() 