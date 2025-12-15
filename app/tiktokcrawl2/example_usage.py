#!/usr/bin/env python3
"""
Example usage of TikTok API Caller
"""

from api_caller import TikTokAPICaller

# Example 1: Single access token with default parameters
def example_single_token():
    """Example: Call all APIs with one access token"""
    caller = TikTokAPICaller(config_file='tiktok_api_config.json')
    
    # Single access token
    access_tokens = ['your_access_token_here']
    
    # Parameter values (these will replace {{business_id}}, {{video_id}}, etc.)
    parameter_values = {
        'business_id': '1234567890',
        'video_id': '1234567890123456789',
        'text': 'Great video!'
    }
    
    # Make API calls
    caller.call_all_apis(
        access_tokens=access_tokens,
        parameter_values=parameter_values,
        delay=1.0  # 1 second delay between calls
    )
    
    # Save results
    caller.save_results_json('api_responses.json')
    caller.save_results_excel('api_responses.xlsx')


# Example 2: Multiple access tokens (multiple shops)
def example_multiple_tokens():
    """Example: Call all APIs with multiple access tokens (one per shop)"""
    caller = TikTokAPICaller(config_file='tiktok_api_config.json')
    
    # Multiple access tokens (one per shop)
    access_tokens = [
        'shop1_token_here',
        'shop2_token_here',
        'shop3_token_here'
    ]
    
    # Parameter values (same for all shops, or you can customize per shop)
    parameter_values = {
        'business_id': '1234567890',
        'video_id': '1234567890123456789'
    }
    
    # Make API calls
    caller.call_all_apis(
        access_tokens=access_tokens,
        parameter_values=parameter_values,
        delay=1.0
    )
    
    # Save results
    caller.save_results_json('api_responses.json')
    caller.save_results_excel('api_responses.xlsx')


# Example 3: Load tokens from file
def example_tokens_from_file():
    """Example: Load access tokens from a file (one token per line)"""
    caller = TikTokAPICaller(config_file='tiktok_api_config.json')
    
    # Load tokens from file
    with open('access_tokens.txt', 'r') as f:
        access_tokens = [line.strip() for line in f if line.strip()]
    
    parameter_values = {
        'business_id': '1234567890'
    }
    
    caller.call_all_apis(
        access_tokens=access_tokens,
        parameter_values=parameter_values,
        delay=1.0
    )
    
    caller.save_results_json('api_responses.json')
    caller.save_results_excel('api_responses.xlsx')


if __name__ == "__main__":
    # Run example
    print("Choose an example:")
    print("1. Single token")
    print("2. Multiple tokens")
    print("3. Tokens from file")
    
    choice = input("Enter choice (1-3): ")
    
    if choice == '1':
        example_single_token()
    elif choice == '2':
        example_multiple_tokens()
    elif choice == '3':
        example_tokens_from_file()
    else:
        print("Invalid choice")

