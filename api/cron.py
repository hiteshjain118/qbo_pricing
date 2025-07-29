from http.server import BaseHTTPRequestHandler
import sys
import os
from dotenv import load_dotenv

from qbo_request_auth_params import QBORequestAuthParams
from report_manager import QBOReportManager

# Add the parent directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables
if os.getenv("VERCEL") is None:
    load_dotenv()

def run_scheduled_reports():
    """Run all scheduled reports - Entry point for Vercel cron jobs"""
    try:
        # Initialize managers
        auth_params = QBORequestAuthParams()        
        report_manager = QBOReportManager(auth_params)        
        report_manager.run_scheduled_jobs()
    except Exception as e:
        print(f"❌ Critical error in scheduled reports job: {e}")
        return {
            "status": "error",
            "error": str(e)
        }    


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        """Handle GET requests for cron job invocation"""
        try:
            # Run the scheduled reports
            result = run_scheduled_reports()
            
            # Set response headers
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            # Return the result as JSON
            import json
            response = json.dumps(result, indent=2)
            self.wfile.write(response.encode())
            
        except Exception as e:
            # Handle errors
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            import json
            error_response = {
                "status": "error",
                "error": str(e)
            }
            self.wfile.write(json.dumps(error_response, indent=2).encode()) 