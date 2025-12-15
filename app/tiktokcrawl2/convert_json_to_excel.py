#!/usr/bin/env python3
"""
Utility script to convert JSON data to Excel
Use this if scraping completed but Excel save failed

Usage:
    python convert_json_to_excel.py [json_file] [excel_file]
    
Examples:
    python convert_json_to_excel.py
    python convert_json_to_excel.py tiktok_api_docs.json
    python convert_json_to_excel.py tiktok_api_docs.json output.xlsx
"""

import sys
import os
import json

# Add parent directory to path to import api_crawl
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from api_crawl import TikTokAPIDocScraperSelenium


def convert_json_to_excel(json_filename='tiktok_api_docs.json', excel_filename='tiktok_api_docs.xlsx'):
    """
    Convert existing JSON file to Excel
    """
    if not os.path.exists(json_filename):
        print(f"✗ JSON file not found: {json_filename}")
        print(f"  Current directory: {os.getcwd()}")
        return False
    
    print("="*80)
    print("JSON to Excel Converter")
    print("="*80)
    print(f"\nLoading data from: {json_filename}")
    
    scraper = TikTokAPIDocScraperSelenium(headless=True)
    
    try:
        # Load JSON data
        with open(json_filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        total = len(data)
        successful = len([d for d in data if d.get('scrape_status') == 'success'])
        failed = len([d for d in data if d.get('scrape_status') == 'failed'])
        
        print(f"✓ Loaded {total} endpoints from JSON")
        print(f"  - Successful: {successful}")
        if failed > 0:
            print(f"  - Failed: {failed}")
        
        # Save to Excel
        print(f"\nConverting to Excel: {excel_filename}...")
        print("  This may take a few minutes for large datasets...")
        
        scraper.save_to_excel(data, excel_filename, mode='overwrite')
        
        print("\n" + "="*80)
        print("✓ CONVERSION COMPLETE!")
        print("="*80)
        print(f"  → {total} endpoints saved to {excel_filename}")
        print(f"  → File location: {os.path.abspath(excel_filename)}")
        return True
        
    except Exception as e:
        print(f"\n✗ Error converting to Excel: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    # Get file names from command line or use defaults
    json_file = sys.argv[1] if len(sys.argv) > 1 else 'tiktok_api_docs.json'
    excel_file = sys.argv[2] if len(sys.argv) > 2 else 'tiktok_api_docs.xlsx'
    
    # Check if JSON file exists in current directory or tiktokcrawl2 directory
    if not os.path.exists(json_file):
        # Try in tiktokcrawl2 directory
        alt_path = os.path.join('tiktokcrawl2', json_file)
        if os.path.exists(alt_path):
            json_file = alt_path
            excel_file = os.path.join('tiktokcrawl2', excel_file)
    
    success = convert_json_to_excel(json_file, excel_file)
    sys.exit(0 if success else 1)

