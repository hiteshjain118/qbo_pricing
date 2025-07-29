import logging
from dotenv import load_dotenv
import os

def is_prod_environment():
    return os.getenv("VERCEL") is not None

if not is_prod_environment():
    load_dotenv()


class QBORequestAuthParams:    
    def __init__(self):
        self.client_id = os.getenv("QBO_CLIENT_ID")
        self.client_secret = os.getenv("QBO_CLIENT_SECRET")
        self.auth_url = os.getenv("QBO_AUTH_URL")
        self.tokens_file = os.getenv("QBO_TOKENS_FILE")
        self.redirect_uri = os.getenv("QBO_REDIRECT_URI")
        self.qbo_base_url = "https://quickbooks.api.intuit.com" if is_prod_environment() else "https://sandbox-quickbooks.api.intuit.com"
        self.api_version = "v3"
        
        logger = logging.getLogger(__name__)
        logger.info(f"QBORequestAuthParams: {self.client_id}, {self.client_secret}, {self.auth_url}, {self.tokens_file}, {self.redirect_uri}, {self.qbo_base_url}")
