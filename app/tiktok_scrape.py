import json
import time
import re
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup

class TikTokAPIDocScraperSelenium:
    def __init__(self, headless=True):
        """
        Initialize Selenium-based scraper for JavaScript-rendered content
        """
        self.base_url = "https://business-api.tiktok.com"
        self.driver = None
        self.headless = headless
        
    def setup_driver(self):
        """
        Setup Chrome driver with appropriate options
        """
        chrome_options = Options()
        if self.headless:
            chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        # Try common ChromeDriver paths
        chromedriver_paths = [
            "/opt/homebrew/bin/chromedriver",  # Homebrew on Apple Silicon
            "/usr/local/bin/chromedriver",      # Homebrew on Intel Mac
            "chromedriver"                      # System PATH
        ]
        
        driver_service = None
        for path in chromedriver_paths:
            try:
                from selenium.webdriver.chrome.service import Service
                driver_service = Service(executable_path=path)
                self.driver = webdriver.Chrome(service=driver_service, options=chrome_options)
                print(f"✓ Using ChromeDriver at: {path}\n")
                break
            except Exception as e:
                continue
        
        # Fallback to default if none of the paths work
        if not self.driver:
            try:
                self.driver = webdriver.Chrome(options=chrome_options)
                print("✓ Using ChromeDriver from system PATH\n")
            except Exception as e:
                print(f"✗ Error: Could not initialize ChromeDriver")
                print(f"  {e}")
                print("\nPlease ensure ChromeDriver is installed:")
                print("  brew install chromedriver")
                raise
        
        self.driver.set_page_load_timeout(30)
        
    def get_iframe_content(self, url, wait_time=10):
        """
        Load page and extract iframe content using Selenium
        """
        try:
            print(f"Loading page: {url}")
            self.driver.get(url)
            
            # Wait for iframe to load
            print("Waiting for iframe to load...")
            iframe = WebDriverWait(self.driver, wait_time).until(
                EC.presence_of_element_located((By.TAG_NAME, "iframe"))
            )
            
            print("✓ Iframe found!")
            
            # Get iframe src
            iframe_src = iframe.get_attribute('src')
            print(f"Iframe URL: {iframe_src[:100]}...")
            
            # Switch to iframe
            self.driver.switch_to.frame(iframe)
            
            # Wait for content to load
            time.sleep(2)
            
            # Get page source from iframe
            iframe_html = self.driver.page_source
            
            # Switch back to main content
            self.driver.switch_to.default_content()
            
            return iframe_html, iframe_src
            
        except Exception as e:
            print(f"Error loading iframe: {e}")
            return None, None
    
    def get_endpoint_links_from_page(self, page_url):
        """
        Extract all endpoint links from the documentation page
        """
        print("\n" + "="*80)
        print("STEP 1: Getting list of endpoint documentation pages")
        print("="*80)
        print(f"\nFetching endpoint links from: {page_url}")
        
        iframe_html, iframe_src = self.get_iframe_content(page_url)
        
        if not iframe_html:
            print("✗ Could not load iframe content")
            return []
        
        soup = BeautifulSoup(iframe_html, 'html.parser')
        
        endpoint_links = []
        all_links = soup.find_all('a', href=True)
        
        print(f"Found {len(all_links)} total links in iframe")
        
        for link in all_links:
            href = link.get('href')
            text = link.get_text(strip=True)
            
            # Look for documentation links with id parameter
            if href and 'id=' in href and text and len(text) > 3:
                # Convert to full URL
                if href.startswith('/portal/docs'):
                    full_url = self.base_url + href
                elif not href.startswith('http'):
                    full_url = self.base_url + '/portal/docs' + href
                else:
                    full_url = href
                
                endpoint_links.append({
                    'text': text,
                    'url': full_url
                })
        
        # Remove duplicates
        seen = set()
        unique_links = []
        for link in endpoint_links:
            if link['url'] not in seen:
                seen.add(link['url'])
                unique_links.append(link)
        
        print(f"✓ Found {len(unique_links)} unique endpoint links\n")
        return unique_links
    
    def extract_table_data(self, table):
        """
        Extract data from a table
        """
        if not table:
            return []
        
        rows = table.find_all('tr')
        data = []
        
        for row in rows[1:]:  # Skip header
            cells = row.find_all(['td', 'th'])
            if len(cells) >= 3:
                data.append({
                    'field': cells[0].get_text(strip=True),
                    'data_type': cells[1].get_text(strip=True),
                    'description': cells[2].get_text(strip=True)
                })
            elif len(cells) == 2:
                data.append({
                    'field': cells[0].get_text(strip=True),
                    'data_type': '',
                    'description': cells[1].get_text(strip=True)
                })
        
        return data
    
    def extract_endpoint_details(self, url, endpoint_text):
        """
        Extract endpoint details from a documentation page
        """
        print(f"  Scraping details...")
        
        iframe_html, iframe_src = self.get_iframe_content(url)
        
        if not iframe_html:
            print(f"  ✗ Could not load iframe")
            return None
        
        soup = BeautifulSoup(iframe_html, 'html.parser')
        
        endpoint_data = {
            'endpoint_name': endpoint_text,
            'doc_url': url,
            'endpoint': None,
            'method': None,
            'headers': [],
            'parameters': [],
            'response': []
        }
        
        # Extract endpoint URL
        text_content = soup.get_text()
        
        # Look for API endpoint URL
        api_url_pattern = r'https://business-api\.tiktok\.com/open_api/[v\d\./a-zA-Z_]+'
        matches = re.findall(api_url_pattern, text_content)
        if matches:
            endpoint_data['endpoint'] = matches[0]
        
        if not endpoint_data['endpoint']:
            rel_url_pattern = r'/open_api/[v\d\./a-zA-Z_]+'
            matches = re.findall(rel_url_pattern, text_content)
            if matches:
                endpoint_data['endpoint'] = 'https://business-api.tiktok.com' + matches[0]
        
        # Extract HTTP method
        method_keywords = ['POST', 'GET', 'PUT', 'DELETE', 'PATCH']
        for method in method_keywords:
            if re.search(rf'\b{method}\b', text_content, re.IGNORECASE):
                endpoint_data['method'] = method
                break
        
        # Extract tables
        all_headings = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
        
        for heading in all_headings:
            heading_text = heading.get_text(strip=True).lower()
            next_table = heading.find_next('table')
            
            if not next_table:
                continue
            
            if 'header' in heading_text and not endpoint_data['headers']:
                endpoint_data['headers'] = self.extract_table_data(next_table)
                if endpoint_data['headers']:
                    print(f"    ✓ Extracted {len(endpoint_data['headers'])} headers")
            
            elif 'parameter' in heading_text and 'response' not in heading_text and not endpoint_data['parameters']:
                endpoint_data['parameters'] = self.extract_table_data(next_table)
                if endpoint_data['parameters']:
                    print(f"    ✓ Extracted {len(endpoint_data['parameters'])} parameters")
            
            elif 'response' in heading_text and not endpoint_data['response']:
                endpoint_data['response'] = self.extract_table_data(next_table)
                if endpoint_data['response']:
                    print(f"    ✓ Extracted {len(endpoint_data['response'])} response fields")
        
        print(f"  ✓ Endpoint: {endpoint_data['endpoint']}")
        print(f"  ✓ Method: {endpoint_data['method']}")
        
        return endpoint_data
    
    def scrape_all_endpoints(self, start_url, delay=2):
        """
        Main scraping function
        """
        self.setup_driver()
        
        try:
            # Get endpoint links
            endpoint_links = self.get_endpoint_links_from_page(start_url)
            
            if not endpoint_links:
                print("\n✗ No endpoint links found!")
                return []
            
            print("\n" + "="*80)
            print("STEP 2: Scraping each endpoint's details")
            print("="*80 + "\n")
            
            all_data = []
            
            for i, link_info in enumerate(endpoint_links, 1):
                print(f"[{i}/{len(endpoint_links)}] {link_info['text']}")
                
                endpoint_data = self.extract_endpoint_details(link_info['url'], link_info['text'])
                
                if endpoint_data:
                    all_data.append(endpoint_data)
                    print()
                
                if i < len(endpoint_links):
                    time.sleep(delay)
            
            return all_data
            
        finally:
            if self.driver:
                self.driver.quit()
    
    def save_to_json(self, data, filename='tiktok_api_docs.json'):
        """Save to JSON"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"\n✓ JSON data saved to {filename}")
    
    def save_to_excel(self, data, filename='tiktok_api_docs.xlsx'):
        """Save to Excel with unified metrics"""
        # Create summary
        summary_data = []
        for item in data:
            summary_data.append({
                'Endpoint Name': item.get('endpoint_name', ''),
                'Documentation URL': item.get('doc_url', ''),
                'API Endpoint': item.get('endpoint', ''),
                'Method': item.get('method', ''),
                'Headers Count': len(item.get('headers', [])),
                'Parameters Count': len(item.get('parameters', [])),
                'Response Fields Count': len(item.get('response', []))
            })
        
        with pd.ExcelWriter(filename, engine='openpyxl') as writer:
            pd.DataFrame(summary_data).to_excel(writer, sheet_name='Summary', index=False)
            
            # Create unified metrics sheets
            self._create_unified_metrics_sheets(data, writer)
            
            # Individual endpoint sheets
            for i, item in enumerate(data, 1):
                sheet_name = item.get('endpoint_name', f'Endpoint_{i}')[:31]
                
                details_data = []
                details_data.append(['Endpoint Name', item.get('endpoint_name', '')])
                details_data.append(['Documentation URL', item.get('doc_url', '')])
                details_data.append(['API Endpoint', item.get('endpoint', '')])
                details_data.append(['Method', item.get('method', '')])
                details_data.append(['', ''])
                
                if item.get('headers'):
                    details_data.append(['HEADERS', '', ''])
                    details_data.append(['Field', 'Data Type', 'Description'])
                    for h in item['headers']:
                        details_data.append([h.get('field', ''), h.get('data_type', ''), h.get('description', '')])
                    details_data.append(['', '', ''])
                
                if item.get('parameters'):
                    details_data.append(['PARAMETERS', '', ''])
                    details_data.append(['Field', 'Data Type', 'Description'])
                    for p in item['parameters']:
                        details_data.append([p.get('field', ''), p.get('data_type', ''), p.get('description', '')])
                    details_data.append(['', '', ''])
                
                if item.get('response'):
                    details_data.append(['RESPONSE', '', ''])
                    details_data.append(['Field', 'Data Type', 'Description'])
                    for r in item['response']:
                        details_data.append([r.get('field', ''), r.get('data_type', ''), r.get('description', '')])
                
                df = pd.DataFrame(details_data)
                df.to_excel(writer, sheet_name=sheet_name, index=False, header=False)
        
        print(f"✓ Excel data saved to {filename}")
    
    def _create_unified_metrics_sheets(self, data, writer):
        """Create unified metrics sheets"""
        # [Same implementation as in the requests-based scraper]
        # Collect unique fields
        headers_map = {}
        parameters_map = {}
        response_map = {}
        
        for item in data:
            endpoint_info = {
                'endpoint_name': item.get('endpoint_name', ''),
                'api_endpoint': item.get('endpoint', ''),
                'doc_url': item.get('doc_url', ''),
                'method': item.get('method', '')
            }
            
            for header in item.get('headers', []):
                field = header.get('field', '')
                if field:
                    if field not in headers_map:
                        headers_map[field] = {
                            'data_type': header.get('data_type', ''),
                            'description': header.get('description', ''),
                            'endpoints': []
                        }
                    headers_map[field]['endpoints'].append(endpoint_info)
            
            for param in item.get('parameters', []):
                field = param.get('field', '')
                if field:
                    if field not in parameters_map:
                        parameters_map[field] = {
                            'data_type': param.get('data_type', ''),
                            'description': param.get('description', ''),
                            'endpoints': []
                        }
                    parameters_map[field]['endpoints'].append(endpoint_info)
            
            for resp in item.get('response', []):
                field = resp.get('field', '')
                if field:
                    if field not in response_map:
                        response_map[field] = {
                            'data_type': resp.get('data_type', ''),
                            'description': resp.get('description', ''),
                            'endpoints': []
                        }
                    response_map[field]['endpoints'].append(endpoint_info)
        
        # Create sheets (same format as before)
        for field_map, sheet_name in [
            (headers_map, 'All Headers'),
            (parameters_map, 'All Parameters'),
            (response_map, 'All Response Fields')
        ]:
            if field_map:
                rows = []
                for field, info in sorted(field_map.items()):
                    for idx, ep in enumerate(info['endpoints']):
                        rows.append({
                            'Field': field if idx == 0 else '',
                            'Data Type': info['data_type'] if idx == 0 else '',
                            'Description': info['description'] if idx == 0 else '',
                            'Usage Count': len(info['endpoints']) if idx == 0 else '',
                            'Endpoint Name': ep['endpoint_name'],
                            'API Endpoint URL': ep['api_endpoint'],
                            'Method': ep['method'],
                            'Documentation URL': ep['doc_url']
                        })
                    rows.append({k: '' for k in rows[0].keys()})  # Empty row
                
                pd.DataFrame(rows).to_excel(writer, sheet_name=sheet_name, index=False)
        
        print(f"  ✓ Created unified metrics sheets")


def main():
    print("\n" + "="*80)
    print("TikTok Business API Documentation Scraper (Selenium)")
    print("="*80 + "\n")
    
    scraper = TikTokAPIDocScraperSelenium(headless=True)
    start_url = "https://business-api.tiktok.com/portal/docs?id=1735713875563521"
    
    data = scraper.scrape_all_endpoints(start_url, delay=2)
    
    if data:
        print("\n" + "="*80)
        print(f"SUCCESS: Scraped {len(data)} endpoints")
        print("="*80 + "\n")
        
        scraper.save_to_json(data)
        scraper.save_to_excel(data)
        
        print("\n" + "="*80)
        print("OUTPUT FILES")
        print("="*80)
        print("✓ tiktok_api_docs.json")
        print("✓ tiktok_api_docs.xlsx (with unified metrics)")
    else:
        print("\n✗ No data was scraped.")


if __name__ == "__main__":
    main()