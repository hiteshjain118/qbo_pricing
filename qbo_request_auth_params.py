import logging
from dotenv import load_dotenv
import os

if os.getenv("VERCEL") is None:
    load_dotenv()

class QBORequestAuthParams:    
    def __init__(self):
        self.client_id = os.getenv("QBO_CLIENT_ID")
        self.client_secret = os.getenv("QBO_CLIENT_SECRET")
        self.auth_url = os.getenv("QBO_AUTH_URL")
        self.tokens_file = os.getenv("QBO_TOKENS_FILE")
        # Use logger instead of direct logging
        logger = logging.getLogger(__name__)
        logger.info(f"QBORequestAuthParams: {self.client_id}, {self.client_secret}, {self.auth_url}, {self.tokens_file}")
