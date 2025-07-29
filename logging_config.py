#!/usr/bin/env python3
"""
Centralized logging configuration for QBO application
"""

import logging
import os

def setup_logging():
    """Setup logging configuration for the entire application"""
    # Only configure logging once
    if not logging.getLogger().handlers:
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s:%(lineno)d - %(levelname)s - %(message)s'
        )
    
    # Set the root logger level
    logging.getLogger().setLevel(logging.INFO)
    
    # Prevent duplicate log messages
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('requests').setLevel(logging.WARNING) 