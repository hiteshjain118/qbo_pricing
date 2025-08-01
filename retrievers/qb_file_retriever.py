import json
import os
from typing import Any, List, Dict

from retrievers.iretriever import IRetriever
from logging_config import setup_logging
import logging

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)


class QBFileRetriever(IRetriever):
    def __init__(self, file_path: str):
        self.file_path = file_path

    def retrieve(self) -> List[Dict[str, Any]]:
        """
        Read JSONL file and return list of JSON objects (dictionaries)
        """
        if not os.path.exists(self.file_path):
            logger.warning(f"File {self.file_path} does not exist")
            return []
        
        responses = []
        with open(self.file_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line:
                    # Handle both new format (single JSON object) and legacy format (double-escaped)
                    try:
                        # Try to parse as single JSON object first (new format)
                        parsed = json.loads(line)
                        if isinstance(parsed, str):
                            # This is double-escaped (legacy format), parse again
                            responses.append(json.loads(parsed))
                        else:
                            # This is a single JSON object (new format)
                            responses.append(parsed)
                    except json.JSONDecodeError:
                        # If parsing fails, assume it's already a valid JSON string
                        responses.append(json.loads(line))
        
        logger.info(f"Loaded {len(responses)} responses from {self.file_path}")
        return responses
    
    def _describe_for_logging(self, output: Any) -> str:
        return f"Loaded {len(output)} responses from {self.file_path}"
    