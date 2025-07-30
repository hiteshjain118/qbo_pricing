#!/usr/bin/env python3
"""
QBO Report Scheduler - Flask Web Application

Simple Flask web app for scheduling QuickBooks reports
"""

import os
import time
import logging
from qbo_request_auth_params import QBORequestAuthParams
from flask import Flask, request, jsonify, render_template, redirect, url_for, flash
from oauth_manager import QBOOAuthManager
from report_scheduler import QBOReportScheduler
from logging_config import setup_logging

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)


app = Flask(__name__)
app.secret_key = os.urandom(24)

# Initialize managers
auth_params = QBORequestAuthParams()
auth_manager = QBOOAuthManager(auth_params)
report_manager = QBOReportScheduler(auth_params)

@app.route('/')
def index():
    """Main page - show connection status and next steps"""
    connected_companies = auth_manager.get_companies()
    existing_job = None
    
    if connected_companies:
        # Check if there's an existing job for the first company
        realm_id = connected_companies[0]['realm_id']
        existing_job = report_manager.get_job_for_realm(realm_id)
    
    return render_template('index.html', 
                         connected_companies=connected_companies,
                         existing_job=existing_job)

@app.route('/connect', methods=['POST'])
def connect_quickbooks():
    print(f"Connecting QuickBooks")
    print(f"Auth manager client_id: {auth_manager.params.client_id}")
    auth_url = auth_manager.connect_to_quickbooks_uri()
    print(f"Redirecting to: {auth_url}")
    return redirect(auth_url)

@app.route('/callback')
def oauth_callback():
    """Handle OAuth callback from QuickBooks"""
    print("Received OAuth callback")
    try:
        auth_manager.handle_oauth_callback(request)
        flash('QuickBooks connected successfully!', 'success')
    except ValueError as e:
        flash(str(e), 'error')
    return redirect(url_for('index'))

# API Routes

@app.route('/configure', methods=['POST'])
def configure_job():
    """Configure job for a company"""
    realm_id = request.form.get('realm_id')
    email = request.form.get('email')
    schedule_time = request.form.get('schedule_time')
    user_timezone = request.form.get('user_timezone', 'UTC')
    
    if not all([email, schedule_time]):
        flash('Please fill in all fields.', 'error')
        return redirect(url_for('index'))
    
    # Get the first connected company if realm_id not provided
    if not realm_id:
        connected_companies = auth_manager.get_companies()
        if not connected_companies:
            flash('No QuickBooks company connected. Please connect first.', 'error')
            return redirect(url_for('index'))
        realm_id = connected_companies[0]['realm_id']
    
    # Validate that we have tokens for this company
    if not auth_manager.is_company_connected(realm_id):
        flash('Company not connected. Please connect QuickBooks first.', 'error')
        return redirect(url_for('index'))
    
    # Convert user's local time to UTC for storage
    try:
        import pytz
        from datetime import datetime, time
        
        # Parse the time input (HH:MM format)
        hour, minute = map(int, schedule_time.split(':'))
        user_time = time(hour, minute)
        
        # Create a datetime object for today in user's timezone
        user_tz = pytz.timezone(user_timezone)
        today = datetime.now(user_tz).date()
        user_datetime = user_tz.localize(datetime.combine(today, user_time))
        
        # Convert to UTC
        utc_datetime = user_datetime.astimezone(pytz.UTC)
        
        # Store the UTC time as HH:MM format
        utc_schedule_time = utc_datetime.strftime('%H:%M')
        
        logger.info(f"Converting schedule time from {user_timezone}: {schedule_time} -> UTC: {utc_schedule_time}")
        
        report_manager.store_job_config(realm_id, email, utc_schedule_time)
        flash('Job scheduled successfully!', 'success')
        
    except Exception as e:
        logger.error(f"Error converting timezone: {e}")
        flash('Error processing time. Please try again.', 'error')
    
    return redirect(url_for('index'))

@app.route('/disconnect', methods=['POST'])
def disconnect_quickbooks():
    """Disconnect QuickBooks and remove all jobs"""
    connected_companies = auth_manager.get_companies()
    
    if connected_companies:
        realm_id = connected_companies[0]['realm_id']
        # Disconnect the company
        auth_manager.disconnect_company(realm_id)
        # Remove any scheduled jobs
        report_manager.delete_job(realm_id)
        flash('QuickBooks disconnected successfully.', 'success')
    else:
        flash('No QuickBooks connection to disconnect.', 'error')
    
    return redirect(url_for('index'))

@app.route('/run_job_now', methods=['POST'])
def run_job_now():
    """Run a job immediately"""
    email = request.form.get('email')
    schedule_time = request.form.get('schedule_time')
    
    if not email:
        flash('Email is required for running job.', 'error')
        return redirect(url_for('index'))
    
    # Get the first connected company
    connected_companies = auth_manager.get_companies()
    if not connected_companies:
        flash('No QuickBooks company connected. Please connect first.', 'error')
        return redirect(url_for('index'))
    
    realm_id = connected_companies[0]['realm_id']
    
    # Validate that we have tokens for this company
    if not auth_manager.is_company_connected(realm_id):
        flash('Company not connected. Please connect QuickBooks first.', 'error')
        return redirect(url_for('index'))
    
    try:
        # Generate and send report immediately
        success = report_manager.generate_and_send_report_for_realm(realm_id, email)
        
        if success:
            flash('✅ Report generated and sent successfully!', 'success')
        else:
            flash('❌ Failed to generate or send report. Check logs for details.', 'error')
            
    except Exception as e:
        flash(f'❌ Error running job: {str(e)}', 'error')
    
    return redirect(url_for('index'))


def main():
    """Main entry point - Flask web server"""
    print("Starting QBO Report Scheduler...")
    print("Application available at http://localhost:5001")
    app.run(debug=True, port=5001)

if __name__ == "__main__":
    main() 