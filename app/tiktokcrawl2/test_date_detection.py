#!/usr/bin/env python3
"""
Test script to verify date parameter detection
Shows which APIs have date parameters and which don't
"""

import json
from pathlib import Path

def test_date_detection():
    """Test date parameter detection for all APIs"""
    config_file = 'tiktok_api_config.json'
    
    if not Path(config_file).exists():
        print(f"✗ Config file not found: {config_file}")
        return
    
    with open(config_file, 'r', encoding='utf-8') as f:
        config_data = json.load(f)
    
    print("\n" + "="*80)
    print("Date Parameter Detection Test")
    print("="*80 + "\n")
    
    apis_with_dates = []
    apis_without_dates = []
    
    for api in config_data:
        api_id = api.get('api_id', 'NO_ID')
        api_name = api.get('api_name', 'Unknown')
        parameters = api.get('parameters', {})
        parameter_types = api.get('parameter_types', {})
        
        # Check for date parameters
        date_params = []
        date_keywords = ['date', 'time', 'start', 'end', 'from', 'to', 'since', 'until']
        
        for param_name in parameters.keys():
            param_lower = param_name.lower()
            if any(keyword in param_lower for keyword in date_keywords):
                date_params.append(param_name)
        
        for param_name, param_type in parameter_types.items():
            if param_type == 'date' and param_name not in date_params:
                date_params.append(param_name)
        
        if date_params:
            apis_with_dates.append({
                'api_id': api_id,
                'api_name': api_name,
                'date_params': date_params
            })
        else:
            apis_without_dates.append({
                'api_id': api_id,
                'api_name': api_name
            })
    
    print(f"APIs WITH date parameters: {len(apis_with_dates)}")
    print("-" * 80)
    for api in apis_with_dates[:10]:  # Show first 10
        print(f"  {api['api_id']:40s} | {', '.join(api['date_params'])}")
        print(f"    {api['api_name'][:60]}")
    if len(apis_with_dates) > 10:
        print(f"  ... and {len(apis_with_dates) - 10} more")
    
    print(f"\nAPIs WITHOUT date parameters: {len(apis_without_dates)}")
    print("-" * 80)
    for api in apis_without_dates[:10]:  # Show first 10
        print(f"  {api['api_id']:40s} | {api['api_name'][:60]}")
    if len(apis_without_dates) > 10:
        print(f"  ... and {len(apis_without_dates) - 10} more")
    
    print("\n" + "="*80)
    print(f"Summary:")
    print(f"  Total APIs: {len(config_data)}")
    print(f"  With date params: {len(apis_with_dates)}")
    print(f"  Without date params: {len(apis_without_dates)}")
    print("="*80)


if __name__ == "__main__":
    test_date_detection()

