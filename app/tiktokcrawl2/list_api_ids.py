#!/usr/bin/env python3
"""
List all API IDs from config JSON
Useful for finding API IDs to use in api_config.yaml
"""

import json
import sys
from pathlib import Path

def list_api_ids(config_file='tiktok_api_config.json'):
    """List all APIs with their IDs"""
    if not Path(config_file).exists():
        print(f"✗ Config file not found: {config_file}")
        print("  Run the scraper first to generate tiktok_api_config.json")
        return
    
    with open(config_file, 'r', encoding='utf-8') as f:
        config_data = json.load(f)
    
    print("\n" + "="*80)
    print(f"API IDs from {config_file}")
    print("="*80 + "\n")
    
    for i, api in enumerate(config_data, 1):
        api_id = api.get('api_id', 'NO_ID')
        api_name = api.get('api_name', 'Unknown')
        method = api.get('method', 'GET')
        endpoint = api.get('endpoint_url', 'NOT FOUND')
        
        print(f"{i:3d}. ID: {api_id:40s} | {method:4s} | {api_name[:50]}")
        if endpoint != 'NOT FOUND':
            print(f"     URL: {endpoint}")
        print()
    
    print("="*80)
    print(f"Total: {len(config_data)} APIs")
    print("\nTo use in api_config.yaml:")
    print("  api_ids: \"business_get\"  # Single API")
    print("  api_ids: [\"business_get\", \"comment_create\"]  # Multiple APIs")


if __name__ == "__main__":
    config_file = sys.argv[1] if len(sys.argv) > 1 else 'tiktok_api_config.json'
    list_api_ids(config_file)

