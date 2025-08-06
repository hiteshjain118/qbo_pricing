#!/usr/bin/env python3
"""
Simple script to list all rows in every database table
"""

import os
import sys
from datetime import datetime
from sqlalchemy import text
import pytz

# Add parent directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import DB

def format_datetime(dt):
    """Format datetime for display in PST timezone"""
    if dt:
        # Convert to PST timezone
        pst = pytz.timezone('America/Los_Angeles')
        if dt.tzinfo is None:
            # For naive datetime, assume it's already in Pacific time
            # (This is how next_run is stored in the database)
            dt = pst.localize(dt)
        else:
            # For aware datetime, convert to Pacific time
            dt = dt.astimezone(pst)
        return dt.strftime('%Y-%m-%d %H:%M:%S PST')
    return 'None'

def is_token_expired(expires_at):
    """Check if token is expired using UTC comparison"""
    if not expires_at:
        return True
    
    # Get current time in UTC
    utc_now = datetime.now(pytz.UTC)
    
    # Convert expires_at to UTC if it doesn't have timezone info
    if expires_at.tzinfo is None:
        expires_at = pytz.utc.localize(expires_at)
    
    return utc_now >= expires_at

def list_all_data():
    """List all data from both sandbox and production tables"""
    print("🗄️  Complete Database Contents Report")
    print("=" * 60)
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        db = DB.get_session()
        
        # Sandbox Companies
        print("\n🌱 SANDBOX COMPANIES")
        print("=" * 30)
        sandbox_companies = db.execute(text("SELECT * FROM qbo_companies_sandbox")).fetchall()
        print(f"\n📊 qbo_companies_sandbox ({len(sandbox_companies)} records):")
        print("-" * 60)
        
        if not sandbox_companies:
            print("  No sandbox companies found")
        else:
            for i, company in enumerate(sandbox_companies, 1):
                print(f"\n  Record {i}:")
                print(f"    ID: {company[0]}")
                print(f"    Realm ID: {company[1]}")
                print(f"    Access Token: {company[2][:20]}..." if company[2] else "    Access Token: None")
                print(f"    Refresh Token: {company[3][:20]}..." if company[3] else "    Refresh Token: None")
                print(f"    Token Type: {company[4]}")
                print(f"    Expires In: {company[5]} seconds")
                print(f"    Refresh Token Expires In: {company[6]} seconds")
                print(f"    Created At: {format_datetime(company[7])} raw: {company[7]}")
                print(f"    Expires At: {format_datetime(company[8])} raw: {company[8]}")
                
                # Show token status
                if company[8]:
                    if is_token_expired(company[8]):
                        print(f"    Status: ❌ Expired")
                    else:
                        print(f"    Status: ✅ Valid")
        
        # Sandbox Jobs
        print("\n🌱 SANDBOX JOBS")
        print("=" * 30)
        sandbox_jobs = db.execute(text("SELECT * FROM qbo_jobs_sandbox")).fetchall()
        print(f"\n📊 qbo_jobs_sandbox ({len(sandbox_jobs)} records):")
        print("-" * 60)
        
        if not sandbox_jobs:
            print("  No sandbox jobs found")
        else:
            for i, job in enumerate(sandbox_jobs, 1):
                print(f"\n  Record {i}:")
                print(f"    ID: {job[0]}")
                print(f"    Realm ID: {job[1]}")
                print(f"    Email: {job[2]}")
                print(f"    Daily Schedule Time: {job[3]}")
                print(f"    User Timezone: {job[4]}")
                print(f"    Last Run TS: {job[5]} PST: {datetime.fromtimestamp(job[5]).strftime('%Y-%m-%d %H:%M:%S') if job[5] else 'None'}")
                print(f"    Created At TS: {job[6]} PST: {datetime.fromtimestamp(job[6]).strftime('%Y-%m-%d %H:%M:%S') if job[6] else 'None'}")
        
        # Production Companies
        print("\n🚀 PRODUCTION COMPANIES")
        print("=" * 30)
        production_companies = db.execute(text("SELECT * FROM qbo_companies_production")).fetchall()
        print(f"\n📊 qbo_companies_production ({len(production_companies)} records):")
        print("-" * 60)
        
        if not production_companies:
            print("  No production companies found")
        else:
            for i, company in enumerate(production_companies, 1):
                print(f"\n  Record {i}:")
                print(f"    ID: {company[0]}")
                print(f"    Realm ID: {company[1]}")
                print(f"    Access Token: {company[2][:20]}..." if company[2] else "    Access Token: None")
                print(f"    Refresh Token: {company[3][:20]}..." if company[3] else "    Refresh Token: None")
                print(f"    Token Type: {company[4]}")
                print(f"    Expires In: {company[5]} seconds")
                print(f"    Refresh Token Expires In: {company[6]} seconds")
                print(f"    Created At: {format_datetime(company[7])} raw: {company[7]}")
                print(f"    Expires At: {format_datetime(company[8])} raw: {company[8]}")
                
                # Show token status
                if company[8]:
                    if is_token_expired(company[8]):
                        print(f"    Status: ❌ Expired")
                    else:
                        print(f"    Status: ✅ Valid")
        
        # Production Jobs
        print("\n🚀 PRODUCTION JOBS")
        print("=" * 30)
        production_jobs = db.execute(text("SELECT * FROM qbo_jobs_production")).fetchall()
        print(f"\n📊 qbo_jobs_production ({len(production_jobs)} records):")
        print("-" * 60)
        
        if not production_jobs:
            print("  No production jobs found")
        else:
            for i, job in enumerate(production_jobs, 1):
                print(f"\n  Record {i}:")
                print(f"    ID: {job[0]}")
                print(f"    Realm ID: {job[1]}")
                print(f"    Email: {job[2]}")
                print(f"    Daily Schedule Time: {job[3]}")
                print(f"    User Timezone: {job[4]}")
                print(f"    Last Run TS: {job[5]} PST: {datetime.fromtimestamp(job[5]).strftime('%Y-%m-%d %H:%M:%S') if job[5] else 'None'}")
                print(f"    Created At TS: {job[6]} PST: {datetime.fromtimestamp(job[6]).strftime('%Y-%m-%d %H:%M:%S') if job[6] else 'None'}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    list_all_data() 