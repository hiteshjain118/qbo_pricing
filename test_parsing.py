import json
import os
from retrievers.qb_file_retriever import QBFileRetriever

current_dir = os.getcwd()
mock_file_path = os.path.join(current_dir, 'retrievers', 'tests', 'mock_inventory_response.jsonl')
retriever = QBFileRetriever(mock_file_path)
responses = retriever.retrieve()
first_response = responses[0]

print('First response type:', type(first_response))
print('First response length:', len(first_response))
print('First 100 chars:', first_response[:100])

parsed_once = json.loads(first_response)
print('Parsed once type:', type(parsed_once))

if isinstance(parsed_once, str):
    parsed_twice = json.loads(parsed_once)
    print('Parsed twice type:', type(parsed_twice))
    print('Parsed twice keys:', list(parsed_twice.keys()) if isinstance(parsed_twice, dict) else 'Not a dict')
else:
    print('First parse was not a string') 