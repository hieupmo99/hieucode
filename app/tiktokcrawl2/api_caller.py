#!/usr/bin/env python3
"""
TikTok API Caller Script
Loads API config JSON and makes API calls with access tokens
Saves responses to JSON and Excel
"""

import json
import requests
import pandas as pd
from datetime import datetime
from pathlib import Path
import sys
from typing import List, Dict, Any
import time
import threading
from queue import Queue
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging
import re
import urllib.parse


class TikTokAPICaller:
    def __init__(self, config_file='tiktok_api_config.json', max_workers=5):
        """
        Initialize API caller with config file
        
        Args:
            config_file: Path to API config JSON file
            max_workers: Maximum number of concurrent API call threads
        """
        self.config_file = config_file
        self.config_data = self.load_config()
        self.results = []
        self.max_workers = max_workers
        self.result_queue = Queue()  # Queue for API call results
        self.processing_queue = Queue()  # Queue for transform/load processing
        self.lock = threading.Lock()  # Lock for thread-safe operations
        self.call_count = 0
        self.total_calls = 0
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(threadName)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
    
    def load_config(self) -> List[Dict]:
        """Load API config from JSON file"""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            print(f"✓ Loaded {len(config)} API configurations from {self.config_file}")
            return config
        except FileNotFoundError:
            print(f"✗ Config file not found: {self.config_file}")
            print("  Run the scraper first to generate tiktok_api_config.json")
            sys.exit(1)
        except json.JSONDecodeError as e:
            print(f"✗ Error parsing config file: {e}")
            sys.exit(1)
    
    def replace_placeholders_in_template(self, template: str, access_token: str, **parameter_values) -> str:
        """
        Replace all placeholders in template string with actual values
        Handles {{Access-Token}}, {{access_token}}, {{field_name}}, etc.
        """
        result = template
        
        # Replace Access-Token (case-insensitive)
        result = re.sub(r'\{\{Access-Token\}\}', access_token, result, flags=re.IGNORECASE)
        result = re.sub(r'\{\{access_token\}\}', access_token, result, flags=re.IGNORECASE)
        
        # Replace other placeholders from parameter_values
        for key, value in parameter_values.items():
            placeholder_pattern = r'\{\{' + re.escape(key) + r'\}\}'
            if isinstance(value, list):
                # Format list as JSON array string
                result = re.sub(placeholder_pattern, json.dumps(value), result)
            else:
                result = re.sub(placeholder_pattern, str(value), result)
        
        return result
    
    def build_request_from_curl_structure(self, curl_structure: Dict, access_token: str, 
                                         parameter_values: Dict[str, Any]) -> tuple:
        """
        Build request from curl structure dynamically
        Returns: (url, headers, body_data, body_format)
        """
        # Build URL
        url_base = curl_structure.get('url_base', curl_structure.get('url_template', ''))
        
        # Build query parameters from template
        query_params = {}
        query_template = curl_structure.get('query_params_template', {})
        
        for param_name, param_info in query_template.items():
            template = param_info.get('template', '')
            param_type = param_info.get('type', 'string')
            
            # Check if we have a value for this parameter
            if param_name in parameter_values:
                value = parameter_values[param_name]
            elif '{{' + param_name + '}}' in template:
                # Try to get from parameter_values with different naming
                value = parameter_values.get(param_name, None)
            else:
                # Use template as-is (may contain placeholders)
                value = self.replace_placeholders_in_template(template, access_token, **parameter_values)
            
            if value is not None:
                if param_type == 'array':
                    if isinstance(value, list):
                        # Format as JSON array string: ["item1","item2"]
                        query_params[param_name] = json.dumps(value)
                    else:
                        query_params[param_name] = str(value)
                else:
                    query_params[param_name] = str(value)
        
        # Build final URL with query params
        if query_params:
            # Encode query parameters properly
            url = url_base + '?' + urllib.parse.urlencode(query_params, doseq=True)
        else:
            url = url_base
        
        # Build headers
        headers = {}
        headers_template = curl_structure.get('headers', {})
        for header_name, header_value in headers_template.items():
            headers[header_name] = self.replace_placeholders_in_template(
                header_value, access_token, **parameter_values
            )
        
        # Build body
        body_data = None
        body_format = curl_structure.get('body_format', 'json')
        
        if curl_structure.get('has_body'):
            body_template = curl_structure.get('body_template')
            if body_template:
                if body_format == 'json':
                    # Parse JSON template and replace placeholders
                    try:
                        # Replace placeholders in JSON string
                        body_str = self.replace_placeholders_in_template(
                            body_template, access_token, **parameter_values
                        )
                        # Parse as JSON to get dict
                        body_data = json.loads(body_str)
                    except:
                        # If parsing fails, try to build from parameters
                        body_data = {}
                        for param_name in parameter_values.keys():
                            if param_name in body_template:
                                body_data[param_name] = parameter_values[param_name]
                elif body_format == 'form-data':
                    body_data = {}
                    for param_name in parameter_values.keys():
                        if param_name in body_template:
                            body_data[param_name] = parameter_values[param_name]
                elif body_format == 'multipart':
                    # Handle multipart form data
                    body_data = {}
                    for param_name in parameter_values.keys():
                        body_data[param_name] = parameter_values[param_name]
        
        return url, headers, body_data, body_format
    
    def make_api_call(self, api_config: Dict, access_token: str, **parameter_values) -> Dict[str, Any]:
        """
        Make API call using config and access token
        
        Args:
            api_config: API configuration dict from config JSON
            access_token: TikTok access token
            **parameter_values: Values for parameters (e.g., business_id="123", video_id="456")
        
        Returns:
            Dict with response data, status, and metadata
        """
        method = api_config.get('method', 'GET').upper()
        url = api_config.get('endpoint_url', '')
        headers_config = api_config.get('headers', {})
        parameters_config = api_config.get('parameters', {})
        parameter_types = api_config.get('parameter_types', {})
        call_format = api_config.get('call_format', {})
        
        # Build headers - replace placeholders
        headers = {}
        for header_name, header_value in headers_config.items():
            if isinstance(header_value, str):
                headers[header_name] = self.replace_placeholders(header_value, access_token, **parameter_values)
            else:
                headers[header_name] = str(header_value)
        
        # Build request
        result = {
            'api_name': api_config.get('api_name', ''),
            'endpoint_url': url,
            'method': method,
            'access_token': access_token[:20] + '...' if len(access_token) > 20 else access_token,  # Mask token
            'timestamp': datetime.now().isoformat(),
            'status': 'pending',
            'response': None,
            'error': None
        }
        
        try:
            if method == 'GET':
                # Handle GET requests with query parameters (including arrays)
                query_params = {}
                
                for param_name in parameters_config.keys():
                    if param_name in parameter_values:
                        value = parameter_values[param_name]
                        
                        # Handle array parameters (like fields=["item_id","create_time"])
                        if parameter_types.get(param_name) == 'array' or call_format.get('has_array_params'):
                            if isinstance(value, list):
                                # Format as JSON array string for query param
                                query_params[param_name] = json.dumps(value)
                            else:
                                query_params[param_name] = value
                        # Handle date parameters
                        elif parameter_types.get(param_name) == 'date':
                            query_params[param_name] = str(value)
                        else:
                            query_params[param_name] = value
                
                response = requests.get(url, headers=headers, params=query_params, timeout=30)
            elif method == 'POST':
                # Handle POST requests with body
                body_data = {}
                
                for param_name in parameters_config.keys():
                    if param_name in parameter_values:
                        value = parameter_values[param_name]
                        
                        # Handle array parameters
                        if parameter_types.get(param_name) == 'array':
                            if isinstance(value, list):
                                body_data[param_name] = value
                            else:
                                body_data[param_name] = value
                        else:
                            body_data[param_name] = value
                
                # Also add access_token if it's in parameters (like /tt_user/token_info/get/)
                if 'access_token' in parameters_config and 'access_token' not in body_data:
                    body_data['access_token'] = access_token
                if 'app_id' in parameters_config and 'app_id' not in body_data:
                    if 'app_id' in parameter_values:
                        body_data['app_id'] = parameter_values['app_id']
                
                response = requests.post(url, headers=headers, json=body_data, timeout=30)
            elif method == 'PUT':
                body_data = {}
                for param_name, param_template in parameters_config.items():
                    if param_name in parameter_values:
                        body_data[param_name] = parameter_values[param_name]
                
                response = requests.put(url, headers=headers, json=body_data, timeout=30)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, params=parameter_values, timeout=30)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            # Parse response
            result['status_code'] = response.status_code
            result['status'] = 'success' if 200 <= response.status_code < 300 else 'error'
            
            try:
                result['response'] = response.json()
            except:
                result['response'] = {'raw_text': response.text}
            
            if result['status'] == 'error':
                result['error'] = result['response'].get('message', f'HTTP {response.status_code}')
        
        except requests.exceptions.Timeout:
            result['status'] = 'timeout'
            result['error'] = 'Request timeout'
        except requests.exceptions.RequestException as e:
            result['status'] = 'error'
            result['error'] = str(e)
        except Exception as e:
            result['status'] = 'error'
            result['error'] = f"Unexpected error: {str(e)}"
        
        return result
    
    def call_all_apis(self, access_tokens: List[str], parameter_values: Dict[str, Any] = None, delay: float = 1.0):
        """
        Call all APIs in config with given access tokens
        
        Args:
            access_tokens: List of access tokens (one per shop/account)
            parameter_values: Dict of parameter values to use (e.g., {'business_id': '123', 'video_id': '456'})
            delay: Delay between API calls in seconds
        """
        if parameter_values is None:
            parameter_values = {}
        
        print(f"\n{'='*80}")
        print(f"Calling {len(self.config_data)} APIs with {len(access_tokens)} access token(s)")
        print(f"{'='*80}\n")
        
        total_calls = len(self.config_data) * len(access_tokens)
        call_count = 0
        
        for token_idx, access_token in enumerate(access_tokens, 1):
            print(f"\n[{token_idx}/{len(access_tokens)}] Processing access token: {access_token[:20]}...")
            
            for api_idx, api_config in enumerate(self.config_data, 1):
                call_count += 1
                api_name = api_config.get('api_name', f'API {api_idx}')
                
                print(f"  [{call_count}/{total_calls}] {api_name} ({api_config.get('method', 'GET')})")
                
                # Make API call
                result = self.make_api_call(api_config, access_token, **parameter_values)
                
                # Add token index to result
                result['token_index'] = token_idx
                result['token_id'] = f'token_{token_idx}'
                
                self.results.append(result)
                
                # Print status
                if result['status'] == 'success':
                    print(f"    ✓ Success (HTTP {result.get('status_code', 'N/A')})")
                else:
                    print(f"    ✗ Failed: {result.get('error', 'Unknown error')}")
                
                # Delay between calls
                if delay > 0 and call_count < total_calls:
                    time.sleep(delay)
        
        print(f"\n{'='*80}")
        print(f"Completed {call_count} API calls")
        print(f"{'='*80}\n")
    
    def save_results_json(self, filename='api_responses.json'):
        """Save API call results to JSON"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        print(f"✓ Results saved to {filename}")
    
    def save_results_excel(self, filename='api_responses.xlsx'):
        """Save API call results to Excel with multiple sheets"""
        if not self.results:
            print("⚠ No results to save")
            return
        
        with pd.ExcelWriter(filename, engine='openpyxl') as writer:
            # Sheet 1: Summary
            summary_data = []
            for result in self.results:
                summary_data.append({
                    'API Name': result.get('api_name', ''),
                    'Endpoint URL': result.get('endpoint_url', ''),
                    'Method': result.get('method', ''),
                    'Token ID': result.get('token_id', ''),
                    'Status': result.get('status', ''),
                    'Status Code': result.get('status_code', ''),
                    'Error': result.get('error', ''),
                    'Timestamp': result.get('timestamp', '')
                })
            
            df_summary = pd.DataFrame(summary_data)
            df_summary.to_excel(writer, sheet_name='Summary', index=False)
            
            # Sheet 2: Responses (flattened)
            response_data = []
            for result in self.results:
                if result.get('status') == 'success' and result.get('response'):
                    response = result['response']
                    
                    # Flatten response
                    row = {
                        'API Name': result.get('api_name', ''),
                        'Endpoint URL': result.get('endpoint_url', ''),
                        'Method': result.get('method', ''),
                        'Token ID': result.get('token_id', ''),
                        'Status Code': result.get('status_code', ''),
                        'Timestamp': result.get('timestamp', '')
                    }
                    
                    # Add response fields
                    if isinstance(response, dict):
                        for key, value in response.items():
                            if isinstance(value, (dict, list)):
                                row[key] = json.dumps(value, ensure_ascii=False)
                            else:
                                row[key] = value
                    else:
                        row['response'] = str(response)
                    
                    response_data.append(row)
            
            if response_data:
                df_responses = pd.DataFrame(response_data)
                df_responses.to_excel(writer, sheet_name='Responses', index=False)
            
            # Sheet 3: Errors
            error_data = []
            for result in self.results:
                if result.get('status') != 'success':
                    error_data.append({
                        'API Name': result.get('api_name', ''),
                        'Endpoint URL': result.get('endpoint_url', ''),
                        'Method': result.get('method', ''),
                        'Token ID': result.get('token_id', ''),
                        'Status': result.get('status', ''),
                        'Status Code': result.get('status_code', ''),
                        'Error': result.get('error', ''),
                        'Timestamp': result.get('timestamp', '')
                    })
            
            if error_data:
                df_errors = pd.DataFrame(error_data)
                df_errors.to_excel(writer, sheet_name='Errors', index=False)
        
        print(f"✓ Results saved to {filename}")
        print(f"  - Summary: {len(summary_data)} calls")
        if response_data:
            print(f"  - Responses: {len(response_data)} successful calls")
        if error_data:
            print(f"  - Errors: {len(error_data)} failed calls")


def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='TikTok API Caller - Make API calls using config file')
    parser.add_argument('--config', default='tiktok_api_config.json', help='API config JSON file')
    parser.add_argument('--tokens', required=True, help='Access tokens (comma-separated or file path)')
    parser.add_argument('--params', help='Parameter values as JSON string (e.g., \'{"business_id":"123","video_id":"456"}\')')
    parser.add_argument('--delay', type=float, default=1.0, help='Delay between API calls (seconds)')
    parser.add_argument('--max-workers', type=int, default=5, help='Maximum concurrent API call threads')
    parser.add_argument('--no-threading', action='store_true', help='Disable threading, use sequential execution')
    parser.add_argument('--output-json', default='api_responses.json', help='Output JSON filename')
    parser.add_argument('--output-excel', default='api_responses.xlsx', help='Output Excel filename')
    
    args = parser.parse_args()
    
    # Load tokens
    tokens = []
    if Path(args.tokens).exists():
        # Load from file (one token per line)
        with open(args.tokens, 'r') as f:
            tokens = [line.strip() for line in f if line.strip()]
    else:
        # Parse comma-separated tokens
        tokens = [t.strip() for t in args.tokens.split(',') if t.strip()]
    
    if not tokens:
        print("✗ No access tokens provided")
        sys.exit(1)
    
    # Load parameter values
    parameter_values = {}
    if args.params:
        try:
            parameter_values = json.loads(args.params)
        except json.JSONDecodeError:
            print("✗ Invalid JSON in --params")
            sys.exit(1)
    
    # Initialize caller
    caller = TikTokAPICaller(config_file=args.config, max_workers=args.max_workers)
    
    # Make API calls
    caller.call_all_apis(
        access_tokens=tokens, 
        parameter_values=parameter_values, 
        delay=args.delay,
        use_threading=not args.no_threading
    )
    
    # Save results
    caller.save_results_json(args.output_json)
    caller.save_results_excel(args.output_excel)
    
    print("\n✓ Done!")


if __name__ == "__main__":
    main()

