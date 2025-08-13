#!/usr/bin/env python3
"""
Script to show all production data from QBO app
"""

import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import DB, QBOCompany, QBOJob, is_prod_environment, get_table_name
from datetime import datetime
import json

def format_timestamp(timestamp):
    """Convert Unix timestamp to readable datetime"""
    if timestamp:
        return datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")
    return "N/A"

def show_production_data():
    """Display all production data from QBO database"""
    
    # Initialize database
    DB.initialize()
    session = DB.get_session()
    
    try:
        print("=" * 80)
        print("QBO APP PRODUCTION DATA")
        print("=" * 80)
        print(f"Environment: {'Production' if is_prod_environment() else 'Sandbox/Development'}")
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # Show QBO Companies data
        print("-" * 50)
        print("QBO COMPANIES TABLE")
        print("-" * 50)
        print(f"Table Name: {get_table_name('qbo_companies')}")
        
        companies = session.query(QBOCompany).all()
        
        if companies:
            print(f"Total Companies: {len(companies)}")
            print()
            
            for i, company in enumerate(companies, 1):
                print(f"Company #{i}:")
                print(f"  ID: {company.id}")
                print(f"  Realm ID: {company.realm_id}")
                print(f"  Token Type: {company.token_type}")
                print(f"  Expires In: {company.expires_in} seconds")
                print(f"  Refresh Token Expires In: {company.refresh_token_expires_in} seconds")
                print(f"  Created At: {company.created_at}")
                print(f"  Expires At: {company.expires_at}")
                print(f"  Access Token: {company.access_token[:20]}..." if company.access_token else "N/A")
                print(f"  Refresh Token: {company.refresh_token[:20]}..." if company.refresh_token else "N/A")
                print()
        else:
            print("No companies found in database.")
            print()
        
        # Show QBO Jobs data
        print("-" * 50)
        print("QBO JOBS TABLE")
        print("-" * 50)
        print(f"Table Name: {get_table_name('qbo_jobs')}")
        
        jobs = session.query(QBOJob).all()
        
        if jobs:
            print(f"Total Jobs: {len(jobs)}")
            print()
            
            for i, job in enumerate(jobs, 1):
                print(f"Job #{i}:")
                print(f"  ID: {job.id}")
                print(f"  Realm ID: {job.realm_id}")
                print(f"  Email: {job.email}")
                print(f"  Daily Schedule Time: {job.daily_schedule_time}")
                print(f"  User Timezone: {job.user_timezone}")
                print(f"  Last Run: {format_timestamp(job.last_run_ts)}")
                print(f"  Created At: {format_timestamp(job.created_at_ts)}")
                print()
        else:
            print("No jobs found in database.")
            print()
        
        # Summary
        print("-" * 50)
        print("SUMMARY")
        print("-" * 50)
        print(f"Total Companies: {len(companies)}")
        print(f"Total Jobs: {len(jobs)}")
        print(f"Environment: {'Production' if is_prod_environment() else 'Sandbox/Development'}")
        
        # Active/Expired token analysis
        if companies:
            now = datetime.utcnow()
            active_companies = [c for c in companies if c.expires_at > now]
            expired_companies = [c for c in companies if c.expires_at <= now]
            
            print(f"Active Companies (valid tokens): {len(active_companies)}")
            print(f"Expired Companies: {len(expired_companies)}")
            
            if active_companies:
                print("\nActive Company Realm IDs:")
                for company in active_companies:
                    print(f"  - {company.realm_id}")
            
            if expired_companies:
                print("\nExpired Company Realm IDs:")
                for company in expired_companies:
                    print(f"  - {company.realm_id} (expired: {company.expires_at})")
        
        print("=" * 80)
        
    except Exception as e:
        print(f"Error retrieving data: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()

if __name__ == "__main__":
    show_production_data() 