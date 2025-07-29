#!/usr/bin/env python3
"""
QBO Authentication Manager

Handles OAuth token management, token refresh, and company authentication
"""

import os
import json
import base64
from urllib.request import Request
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
import requests
from logging_config import setup_logging

from qbo_request_auth_params import QBORequestAuthParams

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

class QBOAuthManager:
    """Manages QBO OAuth tokens and company authentication"""
    
    def __init__(self, request_auth_params: QBORequestAuthParams):
        self.auth_url = request_auth_params.auth_url
        self.client_id = request_auth_params.client_id
        self.client_secret = request_auth_params.client_secret
        self.redirect_uri = "http://localhost:5001/callback"  # Make sure this matches your Intuit app config
        self.token_url = "https://oauth.platform.intuit.com/oauth2/v1/tokens/bearer"
        self.tokens_file = request_auth_params.tokens_file
        self.tokens = self.load_tokens()
        logger.info(f"Loaded {len(self.tokens)} tokens")

    def load_tokens(self) -> Dict[str, Any]:
        """Load tokens from file"""
        try:
            with open(self.tokens_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}
    
    def save_tokens(self):
        """Save tokens to file"""
        # Ensure data directory exists
        os.makedirs(os.path.dirname(self.tokens_file), exist_ok=True)
        with open(self.tokens_file, 'w') as f:
            json.dump(self.tokens, f, indent=2)
    
    def store_tokens(self, realm_id: str, token_data: Dict[str, Any]):
        """Store tokens for a company"""
        self.tokens[realm_id] = {
            'realm_id': realm_id,
            'access_token': token_data.get('access_token'),
            'refresh_token': token_data.get('refresh_token'),
            'token_type': token_data.get('token_type'),
            'expires_in': token_data.get('expires_in'),
            'refresh_token_expires_in': token_data.get('x_refresh_token_expires_in'),
            'created_at': datetime.now().isoformat(),
            'expires_at': (datetime.now() + timedelta(seconds=token_data.get('expires_in', 3600))).isoformat()
        }
        self.save_tokens()
    
    def get_valid_access_token(self, realm_id: str) -> Optional[str]:
        """Get a valid access token, refreshing if necessary"""
        logger.info(f"Tokens: {self.tokens}")
        if realm_id not in self.tokens:
            return None
        
        company_info = self.tokens[realm_id]
        access_token = company_info.get('access_token')
        expires_at = company_info.get('expires_at')
        
        if not access_token:
            return None
        
        # Check if token is expired
        if expires_at:
            try:
                expires_datetime = datetime.fromisoformat(expires_at)
                if datetime.now() >= expires_datetime:
                    logger.info(f"Token for {realm_id} expired at: {expires_datetime}. Refreshing!")
                    # Refresh the token
                    refreshed_info = self.refresh_access_token(realm_id)
                    if refreshed_info:
                        return refreshed_info.get('access_token')
                    else:
                        return None
            except ValueError:
                pass
        
        return access_token
    
    def refresh_access_token(self, realm_id: str) -> Optional[Dict[str, Any]]:
        """Refresh an expired access token"""
        if realm_id not in self.tokens:
            return None
        
        company_info = self.tokens[realm_id]
        refresh_token = company_info.get('refresh_token')
        
        if not refresh_token:
            return None
        
        data = {
            'grant_type': 'refresh_token',
            'refresh_token': refresh_token
        }
        
        headers = {
            'Authorization': f'Basic {base64.b64encode(f"{self.client_id}:{self.client_secret}".encode()).decode()}',
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        try:
            response = requests.post(self.token_url, data=data, headers=headers)
            response.raise_for_status()
            
            # Log intuit_tid if present in response headers
            intuit_tid = response.headers.get('intuit_tid')
            if intuit_tid:
                logger.info(f"Token Refresh API Response - intuit_tid: {intuit_tid}")
            else:
                logger.info("Token Refresh API Response - no intuit_tid found in headers")
            
            token_data = response.json()
            
            # Update stored tokens
            company_info.update({
                'access_token': token_data.get('access_token'),
                'refresh_token': token_data.get('refresh_token', refresh_token),
                'expires_in': token_data.get('expires_in'),
                'expires_at': (datetime.now() + timedelta(seconds=token_data.get('expires_in', 3600))).isoformat(),
                'last_refreshed': datetime.now().isoformat()
            })
            
            self.save_tokens()
            
            return company_info
            
        except requests.exceptions.RequestException as e:
            print(f"Error refreshing token: {e}")
            if hasattr(e, 'response') and e.response is not None:
                # Log intuit_tid even in error responses
                intuit_tid = e.response.headers.get('intuit_tid')
                if intuit_tid:
                    logger.error(f"Token Refresh API Error Response - intuit_tid: {intuit_tid}")
                else:
                    logger.error("Token Refresh API Error Response - no intuit_tid found in headers")
            return None
    
    def exchange_code_for_tokens(self, authorization_code: str) -> Optional[Dict[str, Any]]:
        """Exchange authorization code for access and refresh tokens"""
        
        data = {
            'grant_type': 'authorization_code',
            'code': authorization_code,
            'redirect_uri': self.redirect_uri
        }
        
        headers = {
            'Authorization': f'Basic {base64.b64encode(f"{self.client_id}:{self.client_secret}".encode()).decode()}',
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        try:
            response = requests.post(self.token_url, data=data, headers=headers)
            response.raise_for_status()
            
            # Log intuit_tid if present in response headers
            intuit_tid = response.headers.get('intuit_tid')
            if intuit_tid:
                logger.info(f"Token Exchange API Response - intuit_tid: {intuit_tid}")
            else:
                logger.info("Token Exchange API Response - no intuit_tid found in headers")
            
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error exchanging code for tokens: {e}")
            if hasattr(e, 'response') and e.response is not None:
                # Log intuit_tid even in error responses
                intuit_tid = e.response.headers.get('intuit_tid')
                if intuit_tid:
                    logger.error(f"Token Exchange API Error Response - intuit_tid: {intuit_tid}")
                else:
                    logger.error("Token Exchange API Error Response - no intuit_tid found in headers")
            return None
    
    def get_companies(self) -> List[Dict[str, Any]]:
        """Get list of connected companies"""
        companies = []
        
        for realm_id, company_info in self.tokens.items():
            expires_at = company_info.get('expires_at')
            status = "Valid"
            
            if expires_at:
                try:
                    expires_datetime = datetime.fromisoformat(expires_at)
                    if datetime.now() >= expires_datetime:
                        status = "Expired"
                except ValueError:
                    status = "Unknown"
            
            company_data = {
                'realm_id': realm_id,
                'status': status,
                'created_at': company_info.get('created_at'),
                'expires_at': expires_at
            }
            
            companies.append(company_data)
        
        return companies
    
    def disconnect_company(self, realm_id: str) -> bool:
        """Disconnect a company by removing its tokens"""
        if realm_id in self.tokens:
            logger.info(f"Disconnecting company {realm_id}")
            del self.tokens[realm_id]
            self.save_tokens()
            return True
        return False
    
    def is_company_connected(self, realm_id: str) -> bool:
        """Check if a company is connected and has valid tokens"""
        return (realm_id in self.tokens and 
                self.get_valid_access_token(realm_id) is not None) 


    def connect_to_quickbooks_uri(self):
        """Initiate QuickBooks OAuth connection"""
        from urllib.parse import urlencode
        from time import time
        
        # Debug logging
        logger.info(f"Generating OAuth URL with client_id: {self.client_id}")
        logger.info(f"Auth URL: {self.auth_url}")
        logger.info(f"Redirect URI: {self.redirect_uri}")
        
        params = {
            'client_id': self.client_id,
            'response_type': 'code',
            'scope': 'com.intuit.quickbooks.accounting',
            'redirect_uri': self.redirect_uri,
            'state': f'auth_{int(time())}'
        }
        
        # The auth_url already contains ?environment=production, so we append with &
        oauth_url = f"{self.auth_url}&{urlencode(params)}"
        logger.info(f"Generated OAuth URL: {oauth_url}")
        
        return oauth_url

    def handle_oauth_callback(self, request: Request):
        """Handle OAuth callback from QuickBooks"""
        code = request.args.get('code')
        state = request.args.get('state')
        realm_id = request.args.get('realmId')

        if not code:
            raise ValueError('No authorization code received')
        # Exchange code for tokens
        token_data = self.exchange_code_for_tokens(code)
        if token_data and realm_id:
            # Store tokens
            self.store_tokens(realm_id, token_data)
        else:
            raise ValueError('Failed to connect to QuickBooks. Please try again.')