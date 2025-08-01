#!/usr/bin/env python3
"""
Program to load a specific line from a JSONL file and pretty print it to a JSON file.
Usage: python3 load_line_4.py <input_jsonl_file> <line_number> <output_json_file>
Example: python3 load_line_4.py example_inventory_response.jsonl 4 pretty_inventory_response.json
"""

import json
import sys
import argparse

def load_line_and_pretty_print(input_file, line_number, output_file):
    """Load a specific line from JSONL file and pretty print to JSON file"""
    
    try:
        # Read the JSONL file and get the specified line (1-indexed)
        with open(input_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        if len(lines) < line_number:
            print(f"Error: File {input_file} has only {len(lines)} lines, but we need at least {line_number} lines")
            return False
        
        # Get the specified line (convert to 0-indexed)
        line_data = lines[line_number - 1].strip()
        print(f"Loaded line {line_number} from {input_file}")
        print(f"Line length: {len(line_data)} characters")
        
        # Parse the JSON string - it might be a quoted string that needs double parsing
        try:
            # First parse - might be a quoted string
            first_parse = json.loads(line_data)
            
            # If first parse is a string, parse it again
            if isinstance(first_parse, str):
                print("First parse returned a string, parsing again...")
                data = json.loads(first_parse)
            else:
                data = first_parse
                
            print("Successfully parsed JSON from line")
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON from line {line_number}: {e}")
            return False
        
        # Pretty print to output file
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"Successfully wrote pretty-printed JSON to {output_file}")
        
        # Count inventory items if data is a dictionary
        if isinstance(data, dict):
            query_response = data.get('QueryResponse', {})
            items = query_response.get('Item', [])
            print(f"Output file contains {len(items)} inventory items")
        else:
            print(f"Output file contains data of type: {type(data)}")
        
        return True
        
    except FileNotFoundError:
        print(f"Error: File {input_file} not found")
        return False
    except Exception as e:
        print(f"Error: {e}")
        return False

def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description='Load a specific line from a JSONL file and pretty print it to a JSON file',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 load_line_4.py example_inventory_response.jsonl 4 pretty_inventory_response.json
  python3 load_line_4.py data.jsonl 10 output.json
        """
    )
    
    parser.add_argument('input_file', help='Input JSONL file path')
    parser.add_argument('line_number', type=int, help='Line number to extract (1-indexed)')
    parser.add_argument('output_file', help='Output JSON file path')
    
    args = parser.parse_args()
    
    print(f"Loading line {args.line_number} from {args.input_file} and pretty printing to {args.output_file}")
    print("=" * 80)
    
    success = load_line_and_pretty_print(args.input_file, args.line_number, args.output_file)
    
    if success:
        print("\n✅ Success! Check the output file for the formatted JSON.")
    else:
        print("\n❌ Failed to process the file.")
        sys.exit(1)

if __name__ == "__main__":
    main() 