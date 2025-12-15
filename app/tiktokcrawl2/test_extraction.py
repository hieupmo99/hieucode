#!/usr/bin/env python3
"""
Test script to verify extraction from a specific TikTok API documentation page
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from api_crawl import TikTokAPIDocScraperSelenium
from bs4 import BeautifulSoup

def test_specific_endpoint():
    """Test extraction from the specific endpoint"""
    url = "https://business-api.tiktok.com/portal/docs?id=1762228442072066"
    endpoint_name = "Create a new comment on an owned video"
    
    print("="*80)
    print("Testing Endpoint Extraction")
    print("="*80)
    print(f"\nURL: {url}")
    print(f"Expected Title: {endpoint_name}\n")
    
    scraper = TikTokAPIDocScraperSelenium(headless=False)  # Set to False to see browser
    scraper.setup_driver()
    
    try:
        # Get iframe content
        print("Loading page...")
        iframe_html, iframe_src = scraper.get_iframe_content(url)
        
        if not iframe_html:
            print("✗ Could not load iframe")
            return
        
        soup = BeautifulSoup(iframe_html, 'html.parser')
        
        # Test title extraction
        print("\n" + "-"*80)
        print("TITLE EXTRACTION TEST")
        print("-"*80)
        
        title_div = soup.find('div', class_='DefaultView_title__3-BU8')
        if title_div:
            title_text = title_div.get_text(strip=True)
            print(f"✓ Found DefaultView_title__3-BU8 div: '{title_text}'")
        else:
            print("✗ DefaultView_title__3-BU8 div not found")
            # Try alternative selectors
            title_divs = soup.find_all('div', class_=lambda x: x and 'title' in x.lower())
            print(f"  Found {len(title_divs)} divs with 'title' in class")
            for div in title_divs[:5]:
                print(f"    - {div.get('class')}: {div.get_text(strip=True)[:50]}")
        
        # Test table extraction
        print("\n" + "-"*80)
        print("TABLE EXTRACTION TEST")
        print("-"*80)
        
        all_tables = soup.find_all('table')
        print(f"Found {len(all_tables)} tables")
        
        all_headings = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'strong', 'b'])
        print(f"Found {len(all_headings)} headings")
        
        # Check for headers
        print("\nChecking for HEADERS:")
        header_found = False
        for heading in all_headings:
            heading_text = heading.get_text(strip=True).lower()
            if 'header' in heading_text:
                print(f"  ✓ Found heading: '{heading.get_text(strip=True)}'")
                next_table = heading.find_next('table')
                if next_table:
                    print(f"    → Found table with {len(next_table.find_all('tr'))} rows")
                    header_found = True
        
        if not header_found:
            print("  ✗ No header headings found")
            # Check tables directly
            for i, table in enumerate(all_tables[:3]):
                headers = table.find_all('th')
                header_text = ' '.join([th.get_text(strip=True).lower() for th in headers[:3]])
                print(f"  Table {i+1} headers: {header_text[:100]}")
        
        # Check for parameters
        print("\nChecking for PARAMETERS:")
        param_found = False
        for heading in all_headings:
            heading_text = heading.get_text(strip=True).lower()
            if 'parameter' in heading_text and 'response' not in heading_text:
                print(f"  ✓ Found heading: '{heading.get_text(strip=True)}'")
                next_table = heading.find_next('table')
                if next_table:
                    print(f"    → Found table with {len(next_table.find_all('tr'))} rows")
                    param_found = True
        
        if not param_found:
            print("  ✗ No parameter headings found")
            # Check tables directly
            for i, table in enumerate(all_tables[:3]):
                headers = table.find_all('th')
                header_text = ' '.join([th.get_text(strip=True).lower() for th in headers[:3]])
                if 'field' in header_text or 'name' in header_text:
                    print(f"  Table {i+1} might be parameters: {header_text[:100]}")
        
        # Test code extraction
        print("\n" + "-"*80)
        print("CODE EXTRACTION TEST")
        print("-"*80)
        
        pre_blocks = soup.find_all('pre')
        print(f"Found {len(pre_blocks)} <pre> blocks")
        code_blocks = soup.find_all('code')
        print(f"Found {len(code_blocks)} <code> blocks")
        
        for i, pre in enumerate(pre_blocks[:3]):
            code_text = pre.get_text().strip()
            print(f"\nPre block {i+1}:")
            print(f"  Length: {len(code_text)}")
            print(f"  Preview: {code_text[:100]}...")
            print(f"  Classes: {pre.get('class', [])}")
        
        print(f"\nStandalone <code> blocks:")
        for i, code in enumerate(code_blocks[:5]):
            code_text = code.get_text().strip()
            print(f"\nCode block {i+1}:")
            print(f"  Length: {len(code_text)}")
            print(f"  Preview: {code_text[:150]}...")
            print(f"  Classes: {code.get('class', [])}")
            print(f"  Parent: {code.find_parent().name if code.find_parent() else 'None'}")
        
        # Test full extraction
        print("\n" + "-"*80)
        print("FULL EXTRACTION TEST")
        print("-"*80)
        
        endpoint_data = scraper.extract_endpoint_details(url, endpoint_name)
        
        print(f"\nResults:")
        print(f"  Title: {endpoint_data.get('page_title', 'NOT FOUND')}")
        print(f"  Endpoint: {endpoint_data.get('endpoint', 'NOT FOUND')}")
        print(f"  Method: {endpoint_data.get('method', 'NOT FOUND')}")
        print(f"  Headers: {len(endpoint_data.get('headers', []))}")
        print(f"  Parameters: {len(endpoint_data.get('parameters', []))}")
        print(f"  Response: {len(endpoint_data.get('response', []))}")
        print(f"  Example Code: {len(endpoint_data.get('example_code', []))}")
        
        if endpoint_data.get('headers'):
            print(f"\n  Headers found:")
            for h in endpoint_data['headers'][:3]:
                print(f"    - {h.get('field', '')}")
        
        if endpoint_data.get('parameters'):
            print(f"\n  Parameters found:")
            for p in endpoint_data['parameters'][:5]:
                print(f"    - {p.get('field', '')}: {p.get('data_type', '')}")
        
    finally:
        scraper.driver.quit()

if __name__ == "__main__":
    test_specific_endpoint()

