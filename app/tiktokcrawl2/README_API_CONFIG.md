# API Caller Configuration Guide

## Overview

Simple configuration system:
- **Global Date Range**: Set once, applies to all APIs
- **API Selection**: Just set API ID(s) to call specific APIs
- **Checkpoint/Resume**: Resume from crashes automatically
- **Crash Notification**: Get notified when crashes occur
- **Incremental Saves**: Results saved incrementally to prevent data loss

## Configuration File (`api_config.yaml`)

### Basic Structure

```yaml
# Global date range - applies to ALL APIs
date_range:
  start_date: "2024-01-01"
  end_date: "2024-12-31"

# Call all APIs (uses global date range)
call_all_apis: true

# OR call specific API by ID
# call_all_apis: false
# api_ids: "business_get"  # Single API

# Checkpoint settings
checkpoint_interval: 10
checkpoint_file: "api_call_checkpoint.json"
resume_from_checkpoint: true
```

### Simple Usage

**Call all APIs:**
```yaml
date_range:
  start_date: "2024-01-01"
  end_date: "2024-12-31"
call_all_apis: true
```

**Call one API:**
```yaml
date_range:
  start_date: "2024-01-01"
  end_date: "2024-12-31"
call_all_apis: false
api_ids: "business_get"  # Just set the API ID
```

**Call multiple APIs:**
```yaml
date_range:
  start_date: "2024-01-01"
  end_date: "2024-12-31"
call_all_apis: false
api_ids: ["business_get", "comment_create", "video_list"]
```

## Usage Examples

### 1. Call All APIs with Global Date Range

```yaml
date_range:
  start_date: "2024-01-01"
  end_date: "2024-12-31"
call_all_apis: true
```

###  **Command:**
```bash
python api_caller_threaded.py --tokens "token1" --api-config api_config.yaml
```

### 2. Call Single API by ID

```yaml
date_range:
  start_date: "2024-01-01"
  end_date: "2024-12-31"
call_all_apis: false
api_ids: "business_get"  # Just set the API ID
```

  **Command:**
```bash
python api_caller_threaded.py --tokens "token1" --api-config api_config.yaml
```

### 3. Call Multiple APIs by ID

```yaml
date_range:
  start_date: "2024-01-01"
  end_date: "2024-12-31"
call_all_apis: false
api_ids: ["business_get", "comment_create", "video_list"]
```

### 4. Call APIs Matching Pattern

```yaml
date_range:
  start_date: "2024-01-01"
  end_date: "2024-12-31"
call_all_apis: false
api_pattern: "*video*"  # All APIs with "video" in name
```

## Command Line Usage

```bash
# With API selection config
python api_caller_threaded.py \
  --tokens "token1,token2" \
  --api-config api_config.yaml \
  --params '{"business_id":"123"}' \
  --checkpoint-file my_checkpoint.json

# Resume from checkpoint
python api_caller_threaded.py \
  --tokens "token1" \
  --api-config api_config.yaml \
  --checkpoint-file my_checkpoint.json
```

## Checkpoint/Resume

### How It Works

1. **Checkpoint Saving**: Automatically saves progress every N calls (configurable)
2. **Resume**: On restart, skips already completed API calls
3. **Crash Recovery**: If crash occurs, checkpoint is saved automatically

### Checkpoint File Format

```json
{
  "timestamp": "2024-01-15T10:30:00",
  "completed_count": 150,
  "total_calls": 500,
  "completed_api_calls": [
    ["Get profile data", "token_1", "2024-01-01", "2024-12-31"],
    ["List videos", "token_1", "2024-01-01", "2024-12-31"]
  ]
}
```

### Manual Checkpoint Management

```python
from api_caller_threaded import TikTokAPICallerThreaded

caller = TikTokAPICallerThreaded(
    config_file='tiktok_api_config.json',
    api_selection_config='api_config.yaml',
    checkpoint_file='my_checkpoint.json'
)

# Load checkpoint
checkpoint = caller.load_checkpoint()
print(f"Completed: {checkpoint.get('completed_count', 0)}")

# Save checkpoint manually
caller.save_checkpoint()
```

## Crash Handling

### Automatic Crash Detection

- Saves checkpoint on interrupt (Ctrl+C)
- Saves checkpoint on exceptions
- Logs crash details to `api_call_crash.log`

### Crash Notification

Configure in `api_config.yaml`:

```yaml
global:
  notify_on_crash: true
  notification_email: "your@email.com"
```

Crash log includes:
- Timestamp
- Error message
- Stack trace
- Progress (completed/total calls)
- Checkpoint file location

## Incremental Saves

Results are saved incrementally:

```python
# Append mode (default)
caller.save_results_json('responses.json', append=True)

# This merges with existing results, avoiding duplicates
```

## Best Practices

1. **Use API IDs**: Assign `api_id` for easier reference
2. **Set Date Ranges**: Configure date ranges per API
3. **Enable Checkpoints**: Set `checkpoint_interval` based on call frequency
4. **Monitor Progress**: Check checkpoint file regularly
5. **Resume After Crashes**: Always use `resume_from_checkpoint: true`

## Example: Call Single API for Single Date

```yaml
apis:
  - api_name: "Get profile data"
    enabled: true
    date_range:
      start_date: "2024-06-15"
      end_date: "2024-06-15"  # Single day
    parameters:
      business_id: "{{business_id}}"
```

## Example: Call All APIs Except Some

```yaml
call_all_apis: true  # Call all by default

apis:
  - api_name: "Create comment"
    enabled: false  # Skip this one
```

