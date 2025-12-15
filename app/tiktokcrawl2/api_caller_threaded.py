#!/usr/bin/env python3
"""
TikTok API Caller with Threading and Async Processing
Separates API calling (threaded) from transform/load/parse (async)
"""

import json
import requests
import pandas as pd
from datetime import datetime
from pathlib import Path
import sys
from typing import List, Dict, Any, Optional
import time
import threading
from queue import Queue
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging
import re
import urllib.parse
import yaml
import signal
import traceback


class TikTokAPICallerThreaded:
    """
    Threaded API caller with separate async processing pipeline
    - API calls run in threads (rate limited)
    - Transform/load/parse runs asynchronously in separate thread
    - Supports API filtering, date ranges, checkpoint/resume, crash recovery
    """
    
    def __init__(self, config_file='tiktok_api_config.json', max_workers=5, 
                 api_selection_config=None, checkpoint_file='api_call_checkpoint.json'):
        """
        Initialize API caller
        
        Args:
            config_file: Path to API config JSON file
            max_workers: Maximum number of concurrent API call threads
            api_selection_config: Path to YAML config file for API selection and date ranges
            checkpoint_file: Path to checkpoint file for resume functionality
        """
        self.config_file = config_file
        self.config_data = self.load_config()
        self.max_workers = max_workers
        self.checkpoint_file = checkpoint_file
        
        # Load API selection config
        self.api_selection_config = None
        if api_selection_config and Path(api_selection_config).exists():
            self.api_selection_config = self.load_api_selection_config(api_selection_config)
        
        # Queues for async processing
        self.api_result_queue = Queue()  # Raw API call results
        self.processed_queue = Queue()  # Processed results ready for export
        
        # Threading control
        self.lock = threading.Lock()
        self.call_count = 0
        self.total_calls = 0
        self.processing_active = False
        self.should_stop = False
        
        # Results storage
        self.raw_results = []  # All API call results
        self.processed_results = []  # Processed/transformed results
        
        # Checkpoint tracking
        self.checkpoint_interval = 10
        self.last_checkpoint_time = time.time()
        self.completed_api_calls = set()  # Track completed (api_name, token_id, date_range)
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(threadName)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
    
    def _signal_handler(self, signum, frame):
        """Handle interrupt signals gracefully"""
        self.logger.warning(f"Received signal {signum}, saving checkpoint and exiting...")
        self.should_stop = True
        self.save_checkpoint()
        sys.exit(0)
    
    def load_api_selection_config(self, config_path: str) -> Dict:
        """Load API selection configuration from YAML file"""
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            self.logger.info(f"Loaded API selection config from {config_path}")
            
            # Set checkpoint interval from config
            if config.get('global', {}).get('checkpoint_interval'):
                self.checkpoint_interval = config['global']['checkpoint_interval']
            if config.get('global', {}).get('checkpoint_file'):
                self.checkpoint_file = config['global']['checkpoint_file']
            
            return config
        except Exception as e:
            self.logger.error(f"Error loading API selection config: {e}")
            return None
    
    def load_checkpoint(self) -> Dict:
        """Load checkpoint data if exists"""
        if Path(self.checkpoint_file).exists():
            try:
                with open(self.checkpoint_file, 'r') as f:
                    checkpoint = json.load(f)
                self.logger.info(f"Loaded checkpoint: {checkpoint.get('completed_count', 0)} completed calls")
                return checkpoint
            except Exception as e:
                self.logger.error(f"Error loading checkpoint: {e}")
        return {}
    
    def save_checkpoint(self):
        """Save current progress to checkpoint file"""
        try:
            checkpoint = {
                'timestamp': datetime.now().isoformat(),
                'completed_count': self.call_count,
                'total_calls': self.total_calls,
                'completed_api_calls': list(self.completed_api_calls),
                'raw_results_count': len(self.raw_results),
                'processed_results_count': len(self.processed_results)
            }
            
            with open(self.checkpoint_file, 'w') as f:
                json.dump(checkpoint, f, indent=2)
            
            self.logger.info(f"Checkpoint saved: {self.call_count}/{self.total_calls} calls completed")
        except Exception as e:
            self.logger.error(f"Error saving checkpoint: {e}")
    
    def has_date_parameters(self, api_config: Dict) -> tuple:
        """
        Check if API has date parameters and return their names
        Returns: (has_dates, date_param_names)
        Date parameters can be: start_date, end_date, date, start_time, end_time, etc.
        """
        parameters = api_config.get('parameters', {})
        parameter_types = api_config.get('parameter_types', {})
        curl_structure = api_config.get('curl_structure', {})
        
        # Check parameter types
        date_params = []
        for param_name, param_type in parameter_types.items():
            if param_type == 'date':
                date_params.append(param_name)
        
        # Check parameter names (common date parameter names)
        # Be more precise: only match actual date parameters, not fields that contain these words
        date_exact_matches = ['date', 'time', 'start_date', 'end_date', 'start_time', 'end_time']
        date_prefixes = ['start_', 'end_', 'from_', 'to_', 'since_', 'until_']
        date_suffixes = ['_date', '_time', '_start', '_end']
        
        for param_name in parameters.keys():
            param_lower = param_name.lower()
            
            # Exact match for common date parameters
            if param_lower in date_exact_matches:
                if param_name not in date_params:
                    date_params.append(param_name)
            # Starts with date prefix (e.g., start_date, from_date)
            elif any(param_lower.startswith(prefix) for prefix in date_prefixes):
                if param_name not in date_params:
                    date_params.append(param_name)
            # Ends with date suffix (e.g., created_date, updated_time)
            elif any(param_lower.endswith(suffix) for suffix in date_suffixes):
                # But exclude response fields like "create_date" in response schema
                # Only include if it's a parameter (not a response field)
                if param_name not in date_params:
                    date_params.append(param_name)
            # Contains 'date' or 'time' (but be careful)
            elif 'date' in param_lower or 'time' in param_lower:
                # Additional validation: check if it looks like a date parameter
                # Exclude things like "update_date" in response fields
                if param_name not in date_params:
                    date_params.append(param_name)
        
        # Check query params template (from curl structure)
        query_template = curl_structure.get('query_params_template', {})
        for param_name, param_info in query_template.items():
            param_lower = param_name.lower()
            template = param_info.get('template', '')
            # Check if it's a date parameter
            if any(keyword in param_lower for keyword in date_keywords):
                if param_name not in date_params:
                    date_params.append(param_name)
            # Also check template content for date format
            elif 'date' in template.lower() or re.search(r'\d{4}-\d{2}-\d{2}', template):
                if param_name not in date_params:
                    date_params.append(param_name)
        
        return len(date_params) > 0, date_params
    
    def apply_date_range_to_params(self, api_config: Dict, global_date_range: Dict) -> Dict:
        """
        Apply global date range to API parameters only if API has date parameters
        Handles different date parameter formats
        """
        has_dates, date_param_names = self.has_date_parameters(api_config)
        
        if not has_dates or not date_param_names:
            return {}  # No date parameters, don't add date range
        
        params = {}
        global_start = global_date_range.get('start_date')
        global_end = global_date_range.get('end_date')
        
        # Map global dates to API's date parameter names
        for date_param in date_param_names:
            param_lower = date_param.lower()
            
            # Match start date parameters (various formats)
            if any(keyword in param_lower for keyword in ['start', 'from', 'since', 'begin']):
                if 'start' in param_lower or 'from' in param_lower or 'since' in param_lower:
                    if global_start:
                        params[date_param] = global_start
            
            # Match end date parameters (various formats)
            elif any(keyword in param_lower for keyword in ['end', 'to', 'until', 'finish']):
                if 'end' in param_lower or 'to' in param_lower or 'until' in param_lower:
                    if global_end:
                        params[date_param] = global_end
            
            # Single date parameter (use start_date as default, or both if it's a range field)
            elif param_lower == 'date' or param_lower == 'date_range':
                if global_start:
                    params[date_param] = global_start
            # Time-based parameters
            elif 'time' in param_lower:
                if 'start' in param_lower or 'from' in param_lower:
                    if global_start:
                        params[date_param] = global_start
                elif 'end' in param_lower or 'to' in param_lower:
                    if global_end:
                        params[date_param] = global_end
        
        return params
    
    def should_call_api(self, api_config: Dict, token_id: str) -> tuple:
        """
        Determine if API should be called based on selection config
        Returns: (should_call, parameters_with_dates)
        Only applies date range to APIs that have date parameters
        """
        if not self.api_selection_config:
            return True, {}
        
        api_name = api_config.get('api_name', '')
        api_id = api_config.get('api_id', '')
        
        # Get global date range
        date_range = self.api_selection_config.get('date_range', {})
        
        # Apply date range only if API has date parameters
        date_params = self.apply_date_range_to_params(api_config, date_range)
        
        # Check if call_all_apis is enabled
        call_all = self.api_selection_config.get('call_all_apis', True)
        
        if call_all:
            # Call all APIs (with date params if applicable)
            return True, date_params
        
        # Check for specific API IDs
        api_ids = self.api_selection_config.get('api_ids', [])
        if isinstance(api_ids, str):
            api_ids = [api_ids]  # Convert single string to list
        
        if api_ids:
            # Only call if API ID matches
            if api_id in api_ids:
                return True, date_params
            else:
                return False, {}
        
        # Check for API pattern
        api_pattern = self.api_selection_config.get('api_pattern')
        if api_pattern:
            import fnmatch
            if fnmatch.fnmatch(api_name, api_pattern) or fnmatch.fnmatch(api_id, api_pattern):
                return True, date_params
            else:
                return False, {}
        
        # If no selection criteria, don't call anything
        return False, {}
    
    def filter_apis_by_config(self, access_tokens: List[str], parameter_values: Dict[str, Any]) -> List[tuple]:
        """
        Filter APIs based on selection config and return list of (api_config, token, params) tuples
        Uses global date range and simple API ID selection
        """
        api_call_list = []
        checkpoint = self.load_checkpoint() if self.api_selection_config and self.api_selection_config.get('resume_from_checkpoint', True) else {}
        completed_calls = set(tuple(call) for call in checkpoint.get('completed_api_calls', []))
        
        for api_config in self.config_data:
            for token_idx, access_token in enumerate(access_tokens, 1):
                token_id = f'token_{token_idx}'
                
                # Check if should call this API (returns params with date range)
                should_call, config_params = self.should_call_api(api_config, token_id)
                if not should_call:
                    continue
                
                # Merge parameters
                merged_params = parameter_values.copy()
                # Only add date params if API has date parameters (config_params will be empty if not)
                merged_params.update(config_params)
                
                # Check if already completed (from checkpoint)
                # Build checkpoint key with date info if applicable
                date_key_parts = []
                if config_params:
                    # Get date parameter values for checkpoint key
                    for k, v in sorted(config_params.items()):
                        if 'date' in k.lower() or 'time' in k.lower():
                            date_key_parts.append(f"{k}:{v}")
                date_key = '|'.join(date_key_parts) if date_key_parts else ''
                
                call_key = (api_config.get('api_name', ''), token_id, date_key)
                if call_key in completed_calls:
                    self.logger.info(f"Skipping already completed: {api_config.get('api_name')} for {token_id}")
                    continue
                
                api_call_list.append((api_config, access_token, token_idx, merged_params))
        
        return api_call_list
    
    def load_config(self) -> List[Dict]:
        """Load API config from JSON file"""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            self.logger.info(f"Loaded {len(config)} API configurations from {self.config_file}")
            return config
        except FileNotFoundError:
            self.logger.error(f"Config file not found: {self.config_file}")
            sys.exit(1)
        except json.JSONDecodeError as e:
            self.logger.error(f"Error parsing config file: {e}")
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
        import urllib.parse
        
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
        Dynamically executes curl structure from crawled example code
        
        Args:
            api_config: API configuration dict from config JSON
            access_token: TikTok access token
            **parameter_values: Values for parameters
        
        Returns:
            Dict with response data, status, and metadata
        """
        curl_structure = api_config.get('curl_structure', {})
        method = curl_structure.get('method', api_config.get('method', 'GET')).upper()
        endpoint_url = api_config.get('endpoint_url', '')
        
        result = {
            'api_name': api_config.get('api_name', ''),
            'endpoint_url': endpoint_url,
            'method': method,
            'access_token_masked': access_token[:20] + '...' if len(access_token) > 20 else access_token,
            'timestamp': datetime.now().isoformat(),
            'status': 'pending',
            'response': None,
            'error': None
        }
        
        try:
            # Build request from curl structure
            url, headers, body_data, body_format = self.build_request_from_curl_structure(
                curl_structure, access_token, parameter_values
            )
            
            result['endpoint_url'] = url  # Update with final URL
            
            # Make request based on method
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=30)
            elif method == 'POST':
                if body_format == 'json':
                    response = requests.post(url, headers=headers, json=body_data, timeout=30)
                elif body_format == 'form-data':
                    response = requests.post(url, headers=headers, data=body_data, timeout=30)
                elif body_format == 'multipart':
                    response = requests.post(url, headers=headers, files=body_data, timeout=30)
                else:
                    response = requests.post(url, headers=headers, data=body_data, timeout=30)
            elif method == 'PUT':
                response = requests.put(url, headers=headers, json=body_data, timeout=30)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=30)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
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
    
    def _api_call_worker(self, api_config: Dict, access_token: str, token_idx: int,
                        parameter_values: Dict[str, Any], delay: float):
        """
        Thread worker for API calls
        Makes API call and puts result in queue for async processing
        """
        try:
            api_name = api_config.get('api_name', 'Unknown API')
            method = api_config.get('method', 'GET')
            
            # Make API call
            result = self.make_api_call(api_config, access_token, **parameter_values)
            
            # Add token info
            result['token_index'] = token_idx
            result['token_id'] = f'token_{token_idx}'
            
            # Put in queue for async processing
            self.api_result_queue.put(result)
            
            # Thread-safe counter
            with self.lock:
                self.call_count += 1
                current_count = self.call_count
            
            # Log
            if result['status'] == 'success':
                self.logger.info(f"[{current_count}/{self.total_calls}] ✓ {api_name} ({method})")
            else:
                self.logger.warning(f"[{current_count}/{self.total_calls}] ✗ {api_name} ({method}) - {result.get('error', 'Failed')}")
            
            # Rate limiting
            if delay > 0:
                time.sleep(delay)
        
        except Exception as e:
            self.logger.error(f"Error in API call thread: {e}")
            error_result = {
                'api_name': api_config.get('api_name', 'Unknown'),
                'endpoint_url': api_config.get('endpoint_url', ''),
                'method': api_config.get('method', 'GET'),
                'token_index': token_idx,
                'token_id': f'token_{token_idx}',
                'status': 'error',
                'error': f"Thread error: {str(e)}",
                'timestamp': datetime.now().isoformat()
            }
            self.api_result_queue.put(error_result)
    
    def _transform_and_process(self, raw_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform/process raw API result
        This is where you can add custom processing logic
        Override this method or replace with your real transform logic
        
        Args:
            raw_result: Raw API call result
        
        Returns:
            Processed/transformed result
        """
        processed = raw_result.copy()
        
        # Example: Add processing timestamp
        processed['processed_at'] = datetime.now().isoformat()
        
        # Example: Extract key fields from response
        if processed.get('status') == 'success' and processed.get('response'):
            response = processed['response']
            if isinstance(response, dict):
                # Extract common fields
                processed['response_code'] = response.get('code')
                processed['response_message'] = response.get('message')
                processed['request_id'] = response.get('request_id')
                processed['response_data'] = response.get('data')
        
        return processed
    
    def _async_processor(self):
        """
        Async processing thread
        Continuously processes results from API call queue
        Runs transform/load/parse operations asynchronously
        """
        self.logger.info("Async processor started")
        processed_count = 0
        
        while self.processing_active or not self.api_result_queue.empty():
            try:
                # Get result from queue (with timeout)
                raw_result = self.api_result_queue.get(timeout=1)
                
                # Transform/process
                processed_result = self._transform_and_process(raw_result)
                
                # Store processed result
                with self.lock:
                    self.processed_results.append(processed_result)
                    self.raw_results.append(raw_result)
                
                # Put in processed queue (for export pipeline)
                self.processed_queue.put(processed_result)
                
                processed_count += 1
                self.api_result_queue.task_done()
                
            except:
                # Queue empty or timeout - check if we should continue
                continue
        
        self.logger.info(f"Async processor finished - processed {processed_count} results")
    
    def call_all_apis(self, access_tokens: List[str], parameter_values: Dict[str, Any] = None,
                      delay: float = 1.0):
        """
        Call APIs using threading with async processing
        Supports API filtering, date ranges, checkpoint/resume
        
        Args:
            access_tokens: List of access tokens
            parameter_values: Parameter values dict
            delay: Delay between API calls (rate limiting)
        """
        if parameter_values is None:
            parameter_values = {}
        
        # Filter APIs based on config
        if self.api_selection_config:
            api_call_list = self.filter_apis_by_config(access_tokens, parameter_values)
            self.total_calls = len(api_call_list)
            self.logger.info(f"Filtered to {self.total_calls} API calls based on config")
        else:
            # Call all APIs
            api_call_list = []
            for api_config in self.config_data:
                for token_idx, access_token in enumerate(access_tokens, 1):
                    api_call_list.append((api_config, access_token, token_idx, parameter_values))
            self.total_calls = len(api_call_list)
        
        # Load checkpoint if resuming
        checkpoint = self.load_checkpoint()
        if checkpoint and self.api_selection_config and self.api_selection_config.get('resume_from_checkpoint', True):
            self.call_count = checkpoint.get('completed_count', 0)
            self.logger.info(f"Resuming from checkpoint: {self.call_count} calls already completed")
        
        self.raw_results = []
        self.processed_results = []
        self.processing_active = True
        self.should_stop = False
        
        self.logger.info(f"Starting API calls: {self.total_calls} total calls")
        self.logger.info(f"Max workers: {self.max_workers}, Delay: {delay}s")
        self.logger.info(f"Checkpoint interval: {self.checkpoint_interval} calls")
        
        try:
            # Start async processing thread
            processor_thread = threading.Thread(
                target=self._async_processor,
                name="AsyncProcessor",
                daemon=False
            )
            processor_thread.start()
            
            # Execute API calls in thread pool
            with ThreadPoolExecutor(max_workers=self.max_workers, thread_name_prefix="APICall") as executor:
                futures = []
                
                for api_config, access_token, token_idx, params in api_call_list:
                    if self.should_stop:
                        break
                    
                    future = executor.submit(
                        self._api_call_worker,
                        api_config,
                        access_token,
                        token_idx,
                        params,
                        delay
                    )
                    futures.append(future)
                
                # Wait for all API calls to complete
                for future in as_completed(futures):
                    if self.should_stop:
                        break
                    try:
                        future.result()
                    except Exception as e:
                        self.logger.error(f"Future error: {e}")
                        self.logger.error(traceback.format_exc())
            
            # Signal processing thread to finish
            self.processing_active = False
            
            # Wait for processing to complete
            processor_thread.join(timeout=30)
            
            # Final checkpoint save
            self.save_checkpoint()
            
            self.logger.info(f"Completed {self.call_count} API calls")
            self.logger.info(f"Processed {len(self.processed_results)} results")
        
        except KeyboardInterrupt:
            self.logger.warning("Interrupted by user, saving checkpoint...")
            self.save_checkpoint()
            raise
        except Exception as e:
            self.logger.error(f"Fatal error: {e}")
            self.logger.error(traceback.format_exc())
            self.save_checkpoint()
            self._notify_crash(str(e), traceback.format_exc())
            raise
    
    def _notify_crash(self, error_message: str, traceback_str: str):
        """Notify about crash if configured"""
        if not self.api_selection_config:
            return
        
        notify = self.api_selection_config.get('notify_on_crash', False)
        if not notify:
            return
        
        email = self.api_selection_config.get('notification_email', '')
        
        crash_info = {
            'timestamp': datetime.now().isoformat(),
            'error': error_message,
            'traceback': traceback_str,
            'completed_calls': self.call_count,
            'total_calls': self.total_calls,
            'checkpoint_file': self.checkpoint_file
        }
        
        # Save crash log
        crash_log_file = 'api_call_crash.log'
        with open(crash_log_file, 'a') as f:
            f.write(f"\n{'='*80}\n")
            f.write(json.dumps(crash_info, indent=2))
            f.write(f"\n{'='*80}\n")
        
        self.logger.error(f"Crash logged to {crash_log_file}")
        
        # TODO: Send email notification if email configured
        if email:
            self.logger.info(f"Crash notification would be sent to {email}")
    
    def save_results_json(self, filename='api_responses.json', use_processed=True):
        """Save results to JSON"""
        results = self.processed_results if use_processed else self.raw_results
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"Saved {len(results)} results to {filename}")
    
    def save_results_excel(self, filename='api_responses.xlsx', use_processed=True):
        """Save results to Excel"""
        results = self.processed_results if use_processed else self.raw_results
        
        if not results:
            self.logger.warning("No results to save")
            return
        
        with pd.ExcelWriter(filename, engine='openpyxl') as writer:
            # Summary sheet
            summary_data = []
            for result in results:
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
            
            # Responses sheet
            response_data = []
            for result in results:
                if result.get('status') == 'success' and result.get('response'):
                    row = {
                        'API Name': result.get('api_name', ''),
                        'Endpoint URL': result.get('endpoint_url', ''),
                        'Method': result.get('method', ''),
                        'Token ID': result.get('token_id', ''),
                        'Status Code': result.get('status_code', ''),
                        'Timestamp': result.get('timestamp', '')
                    }
                    
                    # Add processed fields if available
                    if 'response_code' in result:
                        row['Response Code'] = result.get('response_code')
                        row['Response Message'] = result.get('response_message')
                        row['Request ID'] = result.get('request_id')
                    
                    # Add full response
                    response = result.get('response', {})
                    if isinstance(response, dict):
                        for key, value in response.items():
                            if isinstance(value, (dict, list)):
                                row[key] = json.dumps(value, ensure_ascii=False)
                            else:
                                row[key] = value
                    
                    response_data.append(row)
            
            if response_data:
                df_responses = pd.DataFrame(response_data)
                df_responses.to_excel(writer, sheet_name='Responses', index=False)
            
            # Errors sheet
            error_data = []
            for result in results:
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
        
        self.logger.info(f"Saved results to {filename}")


def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='TikTok API Caller (Threaded)')
    parser.add_argument('--config', default='tiktok_api_config.json', help='API config JSON file')
    parser.add_argument('--tokens', required=True, help='Access tokens (comma-separated or file path)')
    parser.add_argument('--params', help='Parameter values as JSON string')
    parser.add_argument('--delay', type=float, default=1.0, help='Delay between API calls (seconds)')
    parser.add_argument('--max-workers', type=int, default=5, help='Maximum concurrent threads')
    parser.add_argument('--output-json', default='api_responses.json', help='Output JSON filename')
    parser.add_argument('--output-excel', default='api_responses.xlsx', help='Output Excel filename')
    
    args = parser.parse_args()
    
    # Load tokens
    tokens = []
    if Path(args.tokens).exists():
        with open(args.tokens, 'r') as f:
            tokens = [line.strip() for line in f if line.strip()]
    else:
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
    caller = TikTokAPICallerThreaded(
        config_file=args.config, 
        max_workers=args.max_workers,
        api_selection_config=args.api_config,
        checkpoint_file=args.checkpoint_file
    )
    
    # Make API calls
    caller.call_all_apis(
        access_tokens=tokens,
        parameter_values=parameter_values,
        delay=args.delay
    )
    
    # Save results (append mode for incremental saves)
    caller.save_results_json(args.output_json, append=True)
    caller.save_results_excel(args.output_excel)
    
    print("\n✓ Done!")


if __name__ == "__main__":
    main()

