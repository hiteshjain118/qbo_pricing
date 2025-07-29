#!/usr/bin/env python3
"""
Simple script to list all rows in every database table
"""

import os
from datetime import datetime
from database import (
    get_db_session_with_options, 
    QBOCompany, 
    QBOJob,
    is_prod_environment,
    SANDBOX_TABLE_SUFFIX,
    PROD_TABLE_SUFFIX
)

def format_datetime(dt):
    """Format datetime for display"""
    if dt:
        return dt.strftime('%Y-%m-%d %H:%M:%S')
    return 'None'

def create_model_for_environment(base_model, table_suffix):
    """Create a model instance with a specific table name"""
    class EnvironmentModel(base_model):
        __tablename__ = f"{base_model.__tablename__.replace('_sandbox', '').replace('_production', '')}{table_suffix}"
    
    return EnvironmentModel

def list_table_data_for_environment(base_model, table_name, env_suffix):
    """List all data from a specific table for a given environment"""
    try:
        # Create a model instance for this specific environment
        ModelClass = create_model_for_environment(base_model, env_suffix)
        
        db = get_db_session_with_options()
        records = db.query(ModelClass).all()
        db.close()
        
        print(f"\n📊 {ModelClass.__tablename__} ({len(records)} records):")
        print("-" * 60)
        
        if not records:
            print("  No records found")
            return
        
        for i, record in enumerate(records, 1):
            print(f"\n  Record {i}:")
            if hasattr(record, 'realm_id'):
                print(f"    Realm ID: {record.realm_id}")
            if hasattr(record, 'email'):
                print(f"    Email: {record.email}")
            if hasattr(record, 'schedule_time'):
                print(f"    Schedule Time: {record.schedule_time}")
            if hasattr(record, 'access_token'):
                print(f"    Access Token: {record.access_token[:20]}...")
            if hasattr(record, 'refresh_token'):
                print(f"    Refresh Token: {record.refresh_token[:20]}...")
            if hasattr(record, 'token_type'):
                print(f"    Token Type: {record.token_type}")
            if hasattr(record, 'expires_in'):
                print(f"    Expires In: {record.expires_in} seconds")
            if hasattr(record, 'refresh_token_expires_in'):
                print(f"    Refresh Token Expires In: {record.refresh_token_expires_in} seconds")
            if hasattr(record, 'created_at'):
                print(f"    Created At: {format_datetime(record.created_at)}")
            if hasattr(record, 'expires_at'):
                print(f"    Expires At: {format_datetime(record.expires_at)}")
            if hasattr(record, 'next_run'):
                print(f"    Next Run: {format_datetime(record.next_run)}")
            if hasattr(record, 'last_run'):
                print(f"    Last Run: {format_datetime(record.last_run)}")
            
            # Show token status
            if hasattr(record, 'expires_at') and record.expires_at:
                if datetime.now() < record.expires_at:
                    print(f"    Status: ✅ Valid")
                else:
                    print(f"    Status: ❌ Expired")
        
    except Exception as e:
        print(f"❌ Error reading {table_name}{env_suffix}: {e}")

def count_records_for_environment(base_model, table_name, env_suffix):
    """Count records in a specific table for a given environment"""
    try:
        # Create a model instance for this specific environment
        ModelClass = create_model_for_environment(base_model, env_suffix)
        
        db = get_db_session_with_options()
        count = db.query(ModelClass).count()
        db.close()
        
        return count
    except Exception as e:
        print(f"❌ Error counting {table_name}{env_suffix}: {e}")
        return 0

def main():
    """List all data from all tables"""
    print("🗄️  Database Contents Report")
    print("=" * 60)
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # List sandbox tables
    print("\n🌱 SANDBOX ENVIRONMENT")
    print("=" * 30)
    list_table_data_for_environment(QBOCompany, "qbo_companies", SANDBOX_TABLE_SUFFIX)
    list_table_data_for_environment(QBOJob, "qbo_jobs", SANDBOX_TABLE_SUFFIX)
    
    # List production tables
    print("\n🚀 PRODUCTION ENVIRONMENT")
    print("=" * 30)
    list_table_data_for_environment(QBOCompany, "qbo_companies", PROD_TABLE_SUFFIX)
    list_table_data_for_environment(QBOJob, "qbo_jobs", PROD_TABLE_SUFFIX)
    
    # Summary
    print("\n📈 SUMMARY")
    print("=" * 30)
    
    # Count sandbox records
    sandbox_companies = count_records_for_environment(QBOCompany, "qbo_companies", SANDBOX_TABLE_SUFFIX)
    sandbox_jobs = count_records_for_environment(QBOJob, "qbo_jobs", SANDBOX_TABLE_SUFFIX)
    
    # Count production records
    production_companies = count_records_for_environment(QBOCompany, "qbo_companies", PROD_TABLE_SUFFIX)
    production_jobs = count_records_for_environment(QBOJob, "qbo_jobs", PROD_TABLE_SUFFIX)
    
    print(f"🌱 Sandbox Companies: {sandbox_companies}")
    print(f"🌱 Sandbox Jobs: {sandbox_jobs}")
    print(f"🚀 Production Companies: {production_companies}")
    print(f"🚀 Production Jobs: {production_jobs}")
    print(f"📊 Total Records: {sandbox_companies + sandbox_jobs + production_companies + production_jobs}")

if __name__ == "__main__":
    main() 