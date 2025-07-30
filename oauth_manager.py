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
from database import DB

from qbo_request_auth_params import QBORequestAuthParams

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

class QBOOAuthManager:
    """Manages QBO OAuth tokens and company authentication"""
    
    def __init__(self, request_auth_params: QBORequestAuthParams):
        self.params = request_auth_params
        self.token_url = "https://oauth.platform.intuit.com/oauth2/v1/tokens/bearer"

    def load_tokens(self) -> Dict[str, Any]:
        """Load tokens from database"""
        try:
            db = DB.get_session()
            companies = db.query(DB.get_company_model()).all()
            tokens = {}
            for company in companies:
                tokens[company.realm_id] = {
                    'realm_id': company.realm_id,
                    'access_token': company.access_token,
                    'refresh_token': company.refresh_token,
                    'token_type': company.token_type,
                    'expires_in': company.expires_in,
                    'refresh_token_expires_in': company.refresh_token_expires_in,
                    'created_at': company.created_at.isoformat(),
                    'expires_at': company.expires_at.isoformat()
                }
            return tokens
        except Exception as e:
            logger.error(f"Error loading tokens from database: {e}")
            return {}
        finally:
            db.close()
    
    
    def store_tokens(self, realm_id: str, token_data: Dict[str, Any]):
        """Store tokens for a company in database"""
        try:
            db = DB.get_session()
            
            # Check if company already exists
            existing_company = db.query(DB.get_company_model()).filter(DB.get_company_model().realm_id == realm_id).first()
            
            expires_at = datetime.utcnow() + timedelta(seconds=token_data.get('expires_in', 3600))
            
            if existing_company:
                # Update existing company
                existing_company.access_token = token_data.get('access_token')
                existing_company.refresh_token = token_data.get('refresh_token')
                existing_company.token_type = token_data.get('token_type')
                existing_company.expires_in = token_data.get('expires_in')
                existing_company.refresh_token_expires_in = token_data.get('x_refresh_token_expires_in')
                existing_company.expires_at = expires_at
                logger.info(f"Updated tokens for existing company {realm_id} in database")
            else:
                # Create new company
                new_company = DB.get_company_model()(
                    realm_id=realm_id,
                    access_token=token_data.get('access_token'),
                    refresh_token=token_data.get('refresh_token'),
                    token_type=token_data.get('token_type'),
                    expires_in=token_data.get('expires_in'),
                    refresh_token_expires_in=token_data.get('x_refresh_token_expires_in'),
                    expires_at=expires_at
                )
                db.add(new_company)
            
            db.commit()
            logger.info(f"Added tokens for new company {realm_id} to database")
            
        except Exception as e:
            logger.error(f"Error storing tokens for company {realm_id}: {e}")
            if db:
                db.rollback()
        finally:
            db.close()
    
    def get_valid_access_token_not_throws(self, realm_id: str) -> Optional[str]:
        """Get a valid access token, refreshing if necessary"""
    
        try:
            db = DB.get_session()
            company = db.query(DB.get_company_model()).filter(DB.get_company_model().realm_id == realm_id).first()
            
            if not company:
                logger.info(f"No company found for realm_id: {realm_id}")
                return None
            
            access_token = company.access_token
            expires_at = company.expires_at
            
            if not access_token:
                return None
            
            # Check if token is expired
            if expires_at and datetime.utcnow() >= expires_at:
                logger.info(f"Token for {realm_id} expired at: {expires_at}. Refreshing!")
                # Refresh the token
                refreshed_info = self.refresh_access_token(realm_id)
                if refreshed_info:
                    return refreshed_info.get('access_token')
                else:
                    return None
            
            return access_token
            
        except Exception as e:
            logger.error(f"Error getting access token for {realm_id}: {e}")
            return None
        finally:
            db.close()
    
    def refresh_access_token(self, realm_id: str) -> Optional[Dict[str, Any]]:
        """Refresh an expired access token"""
        try:
            db = DB.get_session()
            company = db.query(DB.get_company_model()).filter(DB.get_company_model().realm_id == realm_id).first()
            
            if not company:
                return None
            
            refresh_token = company.refresh_token
            
            if not refresh_token:
                return None
            
            data = {
                'grant_type': 'refresh_token',
                'refresh_token': refresh_token
            }
            
            headers = {
                'Authorization': f'Basic {base64.b64encode(f"{self.params.client_id}:{self.params.client_secret}".encode()).decode()}',
                'Content-Type': 'application/x-www-form-urlencoded'
            }
            
            try:
                response = requests.post(self.token_url, data=data, headers=headers)
                response.raise_for_status()
                
                # Log intuit_tid if present in response headers
                intuit_tid = response.headers.get('intuit_tid')
                if intuit_tid:
                    logger.info(f"Token Refresh API Response - intuit_tid: {intuit_tid}, response: {response.json()}")
                else:
                    logger.info("Token Refresh API Response - no intuit_tid found in headers")
                
                token_data = response.json()
                
                # Update stored tokens in database
                company.access_token = token_data.get('access_token')
                company.refresh_token = token_data.get('refresh_token', refresh_token)
                company.expires_in = token_data.get('expires_in')
                company.refresh_token_expires_in = token_data.get('x_refresh_token_expires_in')
                company.expires_at = datetime.utcnow() + timedelta(seconds=token_data.get('expires_in', 3600))
                
                db.commit()
                
                return {
                    'access_token': company.access_token,
                    'refresh_token': company.refresh_token,
                    'expires_in': company.expires_in,
                    'expires_at': company.expires_at.isoformat()
                }
                
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
                
        except Exception as e:
            logger.error(f"Error refreshing token for {realm_id}: {e}")
            return None
        finally:
            db.close()
    
    def exchange_code_for_tokens(self, authorization_code: str) -> Optional[Dict[str, Any]]:
        """Exchange authorization code for access and refresh tokens"""
        
        data = {
            'grant_type': 'authorization_code',
            'code': authorization_code,
            'redirect_uri': self.params.redirect_uri
        }
        
        headers = {
            'Authorization': f'Basic {base64.b64encode(f"{self.params.client_id}:{self.params.client_secret}".encode()).decode()}',
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        response = requests.post(self.token_url, data=data, headers=headers)
        response.raise_for_status()
        
        # Log intuit_tid if present in response headers
        intuit_tid = response.headers.get('intuit_tid')
        if intuit_tid:
            logger.info(f"Token Exchange API Response - intuit_tid: {intuit_tid}, response: {response.json()}")
        else:
            logger.info("Token Exchange API Response - no intuit_tid found in headers")
        
        return response.json()
    
    def get_companies(self) -> List[Dict[str, Any]]:
        """Get list of connected companies from database"""
        try:
            db = DB.get_session()
            companies = db.query(DB.get_company_model()).all()
            company_list = []
            
            for company in companies:
                status = "Valid"
                # Use UTC comparison for proper timezone handling
                if company.expires_at and datetime.utcnow() >= company.expires_at:
                    status = "Expired"
                
                company_data = {
                    'realm_id': company.realm_id,
                    'status': status,
                    'created_at': company.created_at.isoformat(),
                    'expires_at': company.expires_at.isoformat()
                }
                
                company_list.append(company_data)
            
            return company_list
        except Exception as e:
            logger.error(f"Error getting companies: {e}")
            return []
        finally:
            db.close()
    
    def disconnect_company(self, realm_id: str) -> bool:
        """Disconnect a company by removing its tokens from database"""
        try:
            db = DB.get_session()
            company = db.query(DB.get_company_model()).filter(DB.get_company_model().realm_id == realm_id).first()
            
            if company:
                logger.info(f"Disconnecting company {realm_id}")
                db.delete(company)
                db.commit()
                return True
            else:
                logger.info(f"Company {realm_id} not found in database")
                return False
        except Exception as e:
            logger.error(f"Error disconnecting company {realm_id}: {e}")
            if db:
                db.rollback()
            raise Exception(f"Error disconnecting company {realm_id}: {e}")
        finally:
            db.close()
    
    def is_company_connected(self, realm_id: str) -> bool:
        """Check if a company is connected and has valid tokens"""
        return self.get_valid_access_token_not_throws(realm_id) is not None


    def connect_to_quickbooks_uri(self):
        """Initiate QuickBooks OAuth connection"""
        from urllib.parse import urlencode
        from time import time
        
        # Debug logging
        logger.info(f"Generating OAuth URL with client_id: {self.params.client_id}")
        logger.info(f"Auth URL: {self.params.auth_url}")
        logger.info(f"Redirect URI: {self.params.redirect_uri}")
        
        params = {
            'client_id': self.params.client_id,
            'response_type': 'code',
            'scope': 'com.intuit.quickbooks.accounting',
            'redirect_uri': self.params.redirect_uri,
            'state': f'auth_{int(time())}'
        }
        
        # The auth_url already contains ?environment=production, so we append with &
        oauth_url = f"{self.params.auth_url}&{urlencode(params)}"
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