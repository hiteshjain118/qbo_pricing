#!/usr/bin/env python3
"""
Migration script to update jobs table schema with new columns:
- daily_schedule_time (String)
- user_timezone (String) 
- last_run_ts (Integer)
- created_at_ts (Integer)
"""

import os
import sys
from sqlalchemy import text

# Add the parent directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import DB

def migrate_jobs_schema():
    """Migrate jobs tables to add new columns"""
    db = None
    try:
        db = DB.get_session()
        
        # Tables to migrate
        tables = ['qbo_jobs_sandbox', 'qbo_jobs_production']
        
        for table_name in tables:
            print(f"🔄 Migrating table: {table_name}")
            
            # Check if table exists
            result = db.execute(text(f"""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = '{table_name}'
                )
            """))
            table_exists = result.fetchone()[0]
            
            if not table_exists:
                print(f"  ⚠️  Table {table_name} does not exist, skipping...")
                continue
            
            # Add new columns if they don't exist
            columns_to_add = [
                ('daily_schedule_time', 'VARCHAR(100)'),
                ('user_timezone', 'VARCHAR(100)'),
                ('last_run_ts', 'INTEGER'),
                ('created_at_ts', 'INTEGER')
            ]
            
            for column_name, column_type in columns_to_add:
                # Check if column exists
                result = db.execute(text(f"""
                    SELECT EXISTS (
                        SELECT FROM information_schema.columns 
                        WHERE table_name = '{table_name}' 
                        AND column_name = '{column_name}'
                    )
                """))
                column_exists = result.fetchone()[0]
                
                if not column_exists:
                    print(f"  ➕ Adding column: {column_name} ({column_type})")
                    db.execute(text(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}"))
                else:
                    print(f"  ✅ Column {column_name} already exists")
            
            # Drop old columns if they exist
            columns_to_drop = ['schedule_time', 'next_run', 'last_run', 'created_at']
            
            for column_name in columns_to_drop:
                # Check if column exists
                result = db.execute(text(f"""
                    SELECT EXISTS (
                        SELECT FROM information_schema.columns 
                        WHERE table_name = '{table_name}' 
                        AND column_name = '{column_name}'
                    )
                """))
                column_exists = result.fetchone()[0]
                
                if column_exists:
                    print(f"  🗑️  Dropping column: {column_name}")
                    db.execute(text(f"ALTER TABLE {table_name} DROP COLUMN {column_name}"))
                else:
                    print(f"  ✅ Column {column_name} already dropped")
            
            # Commit changes for this table
            db.commit()
            print(f"  ✅ Migration completed for {table_name}")
        
        print("\n🎉 All migrations completed successfully!")
        
        # Verify the new schema
        print("\n📊 Verifying new schema:")
        for table_name in tables:
            result = db.execute(text(f"""
                SELECT column_name, data_type, is_nullable 
                FROM information_schema.columns 
                WHERE table_name = '{table_name}'
                ORDER BY ordinal_position
            """))
            columns = result.fetchall()
            
            print(f"\n{table_name}:")
            for column in columns:
                print(f"  - {column[0]}: {column[1]} ({column[2]})")
        
    except Exception as e:
        print(f"❌ Error during migration: {e}")
        if db:
            db.rollback()
        raise
    finally:
        if db:
            db.close()

if __name__ == "__main__":
    print("🔄 Starting jobs schema migration...")
    print("=" * 60)
    migrate_jobs_schema()
    print("\n✅ Migration script completed!") 