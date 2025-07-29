#!/usr/bin/env python3
"""
Script to call QuickBooks Company Info API for all companies in the database
"""

import requests
import json
from database import DB
from sqlalchemy import text

def get_company_info(realm_id, access_token, is_production=False):
    """Call QuickBooks Company Info API"""
    base_url = "https://quickbooks.api.intuit.com" if is_production else "https://sandbox-quickbooks.api.intuit.com"
    url = f"{base_url}/v3/company/{realm_id}/companyinfo/{realm_id}?minorversion=65"
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json"
    }
    
    try:
        response = requests.get(url, headers=headers)
        print(f"\n🔍 Company Info for Realm ID: {realm_id}")
        print(f"Environment: {'Production' if is_production else 'Sandbox'}")
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            company_info = data.get('CompanyInfo', {})
            print(f"✅ Company Name: {company_info.get('CompanyName', 'N/A')}")
            print(f"📧 Email: {company_info.get('Email', {}).get('Address', 'N/A')}")
            print(f"🌐 Website: {company_info.get('WebAddr', {}).get('URI', 'N/A')}")
            print(f"📞 Phone: {company_info.get('PrimaryPhone', {}).get('FreeFormNumber', 'N/A')}")
            print(f"🏢 Legal Name: {company_info.get('LegalName', 'N/A')}")
            print(f"📅 Fiscal Year Start: {company_info.get('FiscalYearStartMonth', 'N/A')}")
            print(f"💰 Currency: {company_info.get('Currency', {}).get('value', 'N/A')}")
        else:
            print(f"❌ Error: {response.text}")
            
    except Exception as e:
        print(f"❌ Exception for {realm_id}: {e}")

def main():
    """Main function to call company info for all companies"""
    print("🚀 Calling QuickBooks Company Info API for all companies...")
    
    db = DB.get_session()
    
    try:
        # Get production companies
        print("\n=== PRODUCTION COMPANIES ===")
        prod_companies = db.execute(text("SELECT realm_id, access_token FROM qbo_companies_production")).fetchall()
        for row in prod_companies:
            realm_id, access_token = row
            get_company_info(realm_id, access_token, is_production=True)
        
        # Get sandbox companies
        print("\n=== SANDBOX COMPANIES ===")
        sandbox_companies = db.execute(text("SELECT realm_id, access_token FROM qbo_companies_sandbox")).fetchall()
        for row in sandbox_companies:
            realm_id, access_token = row
            get_company_info(realm_id, access_token, is_production=False)
            
    except Exception as e:
        print(f"❌ Database error: {e}")
    finally:
        db.close()
    
    print("\n✅ Company info API calls completed!")

if __name__ == "__main__":
    main() 