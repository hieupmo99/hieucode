#!/usr/bin/env python3
"""
Analyze API fields and create CSV showing:
1. Unique field names
2. Count of APIs using each field
3. List of API URLs containing each field
"""

import json
import pandas as pd
from collections import defaultdict

def analyze_fields_from_json(json_file='tiktok_api_docs.json'):
    """
    Analyze fields from scraped JSON data
    """
    print("="*80)
    print("API Field Analysis")
    print("="*80)
    print(f"\nLoading data from: {json_file}")
    
    # Load JSON data
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"✓ Loaded {len(data)} endpoints\n")
    
    # Only analyze successfully scraped endpoints
    successful_data = [item for item in data if item.get('scrape_status') == 'success']
    print(f"✓ Analyzing {len(successful_data)} successfully scraped endpoints")
    print(f"  (Skipping {len(data) - len(successful_data)} failed endpoints)\n")
    
    # Collect field information
    # Structure: field_name -> {data_type, description, apis: [list of api info]}
    headers_analysis = defaultdict(lambda: {'data_type': '', 'description': '', 'apis': []})
    parameters_analysis = defaultdict(lambda: {'data_type': '', 'description': '', 'apis': []})
    response_analysis = defaultdict(lambda: {'data_type': '', 'description': '', 'apis': []})
    
    for item in successful_data:
        api_info = {
            'endpoint_name': item.get('endpoint_name', ''),
            'api_url': item.get('endpoint', ''),
            'method': item.get('method', ''),
            'doc_url': item.get('doc_url', ''),
            'page_title': item.get('page_title', item.get('endpoint_name', ''))
        }
        
        # Process headers
        for header in item.get('headers', []):
            field = header.get('field', '')
            if field:
                if not headers_analysis[field]['data_type']:
                    headers_analysis[field]['data_type'] = header.get('data_type', '')
                    headers_analysis[field]['description'] = header.get('description', '')
                headers_analysis[field]['apis'].append(api_info)
        
        # Process parameters
        for param in item.get('parameters', []):
            field = param.get('field', '')
            if field:
                if not parameters_analysis[field]['data_type']:
                    parameters_analysis[field]['data_type'] = param.get('data_type', '')
                    parameters_analysis[field]['description'] = param.get('description', '')
                parameters_analysis[field]['apis'].append(api_info)
        
        # Process response fields
        for resp in item.get('response', []):
            field = resp.get('field', '')
            if field:
                if not response_analysis[field]['data_type']:
                    response_analysis[field]['data_type'] = resp.get('data_type', '')
                    response_analysis[field]['description'] = resp.get('description', '')
                response_analysis[field]['apis'].append(api_info)
    
    return headers_analysis, parameters_analysis, response_analysis

def create_field_csv(field_analysis, output_file, field_type):
    """
    Create CSV with unique fields analysis
    """
    print(f"\n{'='*80}")
    print(f"Creating CSV for {field_type}")
    print(f"{'='*80}")
    
    rows = []
    
    # Sort fields alphabetically
    for field_name in sorted(field_analysis.keys()):
        info = field_analysis[field_name]
        api_count = len(info['apis'])
        
        # Create comma-separated list of API URLs
        api_urls = ', '.join([api['api_url'] for api in info['apis']])
        
        # Create comma-separated list of endpoint names
        endpoint_names = ', '.join([api['endpoint_name'] for api in info['apis']])
        
        # Create comma-separated list of methods
        methods = ', '.join([api['method'] for api in info['apis']])
        
        rows.append({
            'Field Name': field_name,
            'Data Type': info['data_type'],
            'Description': info['description'],
            'Usage Count': api_count,
            'API Endpoint URLs': api_urls,
            'Endpoint Names': endpoint_names,
            'Methods': methods
        })
    
    # Create DataFrame
    df = pd.DataFrame(rows)
    
    # Save to CSV
    df.to_csv(output_file, index=False, encoding='utf-8')
    
    print(f"✓ Saved to: {output_file}")
    print(f"  Total unique {field_type}: {len(df)}")
    print(f"  Most common field: {df.nlargest(1, 'Usage Count')['Field Name'].values[0]} (used by {df['Usage Count'].max()} APIs)")
    print(f"  Unique fields (used by only 1 API): {len(df[df['Usage Count'] == 1])}")
    
    return df

def create_summary_statistics(headers_df, parameters_df, response_df, output_file='field_statistics.csv'):
    """
    Create summary statistics CSV
    """
    print(f"\n{'='*80}")
    print("Creating Summary Statistics")
    print(f"{'='*80}")
    
    summary_rows = []
    
    # Headers statistics
    summary_rows.append({
        'Category': 'Headers',
        'Total Unique Fields': len(headers_df),
        'Most Common Field': headers_df.nlargest(1, 'Usage Count')['Field Name'].values[0] if len(headers_df) > 0 else 'N/A',
        'Max Usage Count': headers_df['Usage Count'].max() if len(headers_df) > 0 else 0,
        'Unique Fields (1 API only)': len(headers_df[headers_df['Usage Count'] == 1]),
        'Common Fields (10+ APIs)': len(headers_df[headers_df['Usage Count'] >= 10])
    })
    
    # Parameters statistics
    summary_rows.append({
        'Category': 'Parameters',
        'Total Unique Fields': len(parameters_df),
        'Most Common Field': parameters_df.nlargest(1, 'Usage Count')['Field Name'].values[0] if len(parameters_df) > 0 else 'N/A',
        'Max Usage Count': parameters_df['Usage Count'].max() if len(parameters_df) > 0 else 0,
        'Unique Fields (1 API only)': len(parameters_df[parameters_df['Usage Count'] == 1]),
        'Common Fields (10+ APIs)': len(parameters_df[parameters_df['Usage Count'] >= 10])
    })
    
    # Response fields statistics
    summary_rows.append({
        'Category': 'Response Fields',
        'Total Unique Fields': len(response_df),
        'Most Common Field': response_df.nlargest(1, 'Usage Count')['Field Name'].values[0] if len(response_df) > 0 else 'N/A',
        'Max Usage Count': response_df['Usage Count'].max() if len(response_df) > 0 else 0,
        'Unique Fields (1 API only)': len(response_df[response_df['Usage Count'] == 1]),
        'Common Fields (10+ APIs)': len(response_df[response_df['Usage Count'] >= 10])
    })
    
    df = pd.DataFrame(summary_rows)
    df.to_csv(output_file, index=False, encoding='utf-8')
    
    print(f"✓ Saved to: {output_file}\n")
    print(df.to_string(index=False))

def main():
    json_file = 'tiktok_api_docs.json'
    
    # Analyze fields
    headers_analysis, parameters_analysis, response_analysis = analyze_fields_from_json(json_file)
    
    # Create CSV files
    headers_df = create_field_csv(headers_analysis, 'unique_headers_analysis.csv', 'Headers')
    parameters_df = create_field_csv(parameters_analysis, 'unique_parameters_analysis.csv', 'Parameters')
    response_df = create_field_csv(response_analysis, 'unique_response_fields_analysis.csv', 'Response Fields')
    
    # Create summary statistics
    create_summary_statistics(headers_df, parameters_df, response_df)
    
    print("\n" + "="*80)
    print("ANALYSIS COMPLETE")
    print("="*80)
    print("\nOutput Files:")
    print("  1. unique_headers_analysis.csv")
    print("  2. unique_parameters_analysis.csv")
    print("  3. unique_response_fields_analysis.csv")
    print("  4. field_statistics.csv")
    print("\nEach CSV shows:")
    print("  - Unique field names (deduplicated, sorted alphabetically)")
    print("  - Usage count (how many APIs use this field)")
    print("  - List of API URLs that contain this field")
    print("  - Endpoint names and methods")

if __name__ == "__main__":
    main()