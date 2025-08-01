#!/usr/bin/env python3
"""
QBO Report Scheduler - Cron Job Entry Point

This file is designed to be invoked by Vercel cron jobs to run scheduled reports.
"""

import os
import sys
from dotenv import load_dotenv

# Add parent directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.cron import run_scheduled_reports

# Load environment variables
if os.getenv("VERCEL") is None:
    load_dotenv()

def main():
    """Main entry point for Vercel cron jobs"""
    run_scheduled_reports()

if __name__ == "__main__":
    main() 