# API ID Consolidation Guide

## Overview

All files are now consolidated to use `api_id` consistently:

1. **Scraper** (`api_crawl.py`) - Generates `api_id` from endpoint URL
2. **Config JSON** (`tiktok_api_config.json`) - Contains `api_id` for each API
3. **API Caller** (`api_caller_threaded.py`) - Uses `api_id` for API selection
4. **Config YAML** (`api_config.yaml`) - Uses `api_id` to select APIs

## How API ID is Generated

API ID is automatically generated from the endpoint URL:

**Examples:**
- `https://business-api.tiktok.com/open_api/v1.3/business/get/` → `business_get`
- `https://business-api.tiktok.com/open_api/v1.3/business/comment/create/` → `business_comment_create`
- `https://business-api.tiktok.com/open_api/v1.3/tt_user/token_info/get/` → `tt_user_token_info_get`

**Fallback:** If endpoint URL is not available, generates from API name or page title.

## Finding API IDs

### Method 1: List All API IDs

```bash
python list_api_ids.py
```

Output:
```
  1. ID: business_get                          | GET  | Get profile data of a TikTok account
     URL: https://business-api.tiktok.com/open_api/v1.3/business/get/

  2. ID: business_comment_create                 | POST | Create a new comment on an owned video
     URL: https://business-api.tiktok.com/open_api/v1.3/business/comment/create/
```

### Method 2: Check Config JSON

```bash
cat tiktok_api_config.json | grep -A 2 "api_id"
```

### Method 3: Check Excel File

Open `tiktok_api_docs.xlsx` → "API Fields Detail" sheet → Look for API names, then find corresponding ID in JSON.

## Config JSON Structure

Each API in `tiktok_api_config.json` now includes:

```json
{
  "api_id": "business_get",
  "api_name": "Get profile data of a TikTok account",
  "page_title": "Get profile data of a TikTok account",
  "method": "GET",
  "endpoint_url": "https://business-api.tiktok.com/open_api/v1.3/business/get/",
  "headers": {...},
  "parameters": {...},
  "curl_structure": {...}
}
```

## Using API IDs in Config

### Example 1: Call Single API

```yaml
date_range:
  start_date: "2024-01-01"
  end_date: "2024-12-31"
call_all_apis: false
api_ids: "business_get"  # Use the api_id from JSON
```

### Example 2: Call Multiple APIs

```yaml
date_range:
  start_date: "2024-01-01"
  end_date: "2024-12-31"
call_all_apis: false
api_ids: ["business_get", "business_comment_create", "tt_user_token_info_get"]
```

## Verification

After running the scraper, verify API IDs are present:

```python
import json

with open('tiktok_api_config.json', 'r') as f:
    config = json.load(f)

# Check if all APIs have IDs
missing_ids = [api for api in config if not api.get('api_id')]
if missing_ids:
    print(f"⚠ {len(missing_ids)} APIs missing api_id")
else:
    print(f"✓ All {len(config)} APIs have api_id")

# List all IDs
for api in config[:5]:  # First 5
    print(f"{api.get('api_id')}: {api.get('api_name')}")
```

## Files Consolidated

✅ **api_crawl.py** - Generates `api_id` and saves to config JSON
✅ **tiktok_api_config.json** - Contains `api_id` for each API
✅ **api_caller_threaded.py** - Uses `api_id` for API selection
✅ **api_config.yaml** - Uses `api_id` to select APIs
✅ **list_api_ids.py** - Utility to list all API IDs

All parts are now consolidated and use `api_id` consistently!

