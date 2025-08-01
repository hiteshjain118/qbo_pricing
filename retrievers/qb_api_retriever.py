from abc import ABC, abstractmethod
import json
from typing import Any, Dict, List, Tuple

import pandas as pd

from oauth_manager import QBOOAuthManager
from qbo_request_auth_params import QBORequestAuthParams

from retrievers.iretriever import IRetriever
from logging_config import setup_logging
import logging

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

class QBAPIRetriever(IRetriever):
    def __init__(
            self, 
            auth_params: QBORequestAuthParams, 
            realm_id: str, 
            save_file_path: str=None
        ):
        self.auth_params = auth_params
        self.realm_id = realm_id
        self.oauth_manager = QBOOAuthManager(auth_params)
        self.save_file_path = save_file_path
        self.page_size = 100
        self.start_pos = 1

    def retrieve(self) -> Any:
        if not self.oauth_manager.is_company_connected(self.realm_id):
            print(f"Company {self.realm_id} is no longer connected")
            raise Exception(f"Company {self.realm_id} is no longer connected")
        
        responses = self._call_api()
        logger.info(self._describe_for_logging(responses))
        # Responses is now an array of JSON objects, save to file as JSON strings
        if self.save_file_path:
            logger.info(f"Saving {len(responses)} responses to {self.save_file_path}")
            with open(self.save_file_path, 'a') as f:
                for response in responses:
                    # Convert JSON object to string for file storage
                    f.write(json.dumps(response) + '\n')
        
        return responses

    def get_headers(self)-> Dict[str, str]:
        access_token = self.oauth_manager.get_valid_access_token_not_throws(self.realm_id)
        if not access_token:
            raise Exception(f"No valid access token for company {self.realm_id}")
        
        return {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/json",
            "Content-Type": "application/json"
        }

    
    def _call_api(self) -> List[Dict[str, Any]]:
        # handle paginated queries and response 
        responses = []
        while True:
            paginated_response, num_items = self._call_api_once()
            responses.append(paginated_response)
            if num_items < self.page_size:
                break
            self.start_pos += self.page_size    

        return responses

    @abstractmethod
    def _call_api_once(self) -> Tuple[Dict[str, Any], int]: #return response and number of items in the response
        """
        Call the API and return the response as a dictionary
        """
        pass 
