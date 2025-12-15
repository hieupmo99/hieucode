#!/usr/bin/env python3
"""
Example: Using API Caller with Configuration File
Demonstrates API selection, date ranges, checkpoint/resume
"""

from api_caller_threaded import TikTokAPICallerThreaded

# Example 1: Call specific API with date range
def example_single_api_single_date():
    """Call one API for one specific date"""
    caller = TikTokAPICallerThreaded(
        config_file='tiktok_api_config.json',
        api_selection_config='api_config.yaml',  # Use config file
        checkpoint_file='checkpoint.json',
        max_workers=3
    )
    
    caller.call_all_apis(
        access_tokens=['your_token_here'],
        parameter_values={'business_id': '123'},
        delay=1.0
    )
    
    caller.save_results_json('results.json', append=True)
    caller.save_results_excel('results.xlsx')


# Example 2: Resume from checkpoint after crash
def example_resume_after_crash():
    """Resume from checkpoint if previous run crashed"""
    caller = TikTokAPICallerThreaded(
        config_file='tiktok_api_config.json',
        api_selection_config='api_config.yaml',
        checkpoint_file='checkpoint.json',  # Same checkpoint file
        max_workers=5
    )
    
    # Checkpoint will be loaded automatically
    # Already completed calls will be skipped
    
    caller.call_all_apis(
        access_tokens=['token1', 'token2'],
        parameter_values={'business_id': '123'},
        delay=1.0
    )
    
    caller.save_results_json('results.json', append=True)


# Example 3: Call multiple APIs with different date ranges
def example_multiple_apis_different_dates():
    """
    Configure api_config.yaml:
    
    apis:
      - api_name: "Get profile data"
        enabled: true
        date_range:
          start_date: "2024-01-01"
          end_date: "2024-03-31"
      
      - api_name: "List videos"
        enabled: true
        date_range:
          start_date: "2024-04-01"
          end_date: "2024-06-30"
    """
    caller = TikTokAPICallerThreaded(
        config_file='tiktok_api_config.json',
        api_selection_config='api_config.yaml',
        checkpoint_file='checkpoint.json'
    )
    
    caller.call_all_apis(
        access_tokens=['token1'],
        parameter_values={'business_id': '123'},
        delay=1.0
    )


# Example 4: Check checkpoint status
def example_check_status():
    """Check current progress from checkpoint"""
    caller = TikTokAPICallerThreaded(
        config_file='tiktok_api_config.json',
        checkpoint_file='checkpoint.json'
    )
    
    checkpoint = caller.load_checkpoint()
    
    if checkpoint:
        print(f"Completed: {checkpoint.get('completed_count', 0)}")
        print(f"Total: {checkpoint.get('total_calls', 0)}")
        print(f"Last update: {checkpoint.get('timestamp', 'N/A')}")
    else:
        print("No checkpoint found")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        example = sys.argv[1]
        if example == "single":
            example_single_api_single_date()
        elif example == "resume":
            example_resume_after_crash()
        elif example == "multiple":
            example_multiple_apis_different_dates()
        elif example == "status":
            example_check_status()
        else:
            print("Usage: python example_config_usage.py [single|resume|multiple|status]")
    else:
        print("Usage: python example_config_usage.py [single|resume|multiple|status]")

