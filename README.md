# MagicPod Scheduled Batch Runs Script

This script retrieves information about all scheduled batch runs across all projects in your MagicPod organization.

## Features

- Retrieves all projects from your MagicPod account
- Fetches scheduled batch runs for each project
- Displays detailed information including:
  - Schedule ID and name
  - Status
  - Cron expression
  - Next run time
  - Last run time
- Organized output grouped by project
- Error handling for API failures

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure API Token

You have two options to set your MagicPod API token:

#### Option A: Environment Variable (Recommended)
```bash
export MAGICPOD_API_TOKEN="your_actual_api_token_here"
export MAGICPOD_ORG_NAME="your_organization_name"  # Optional
```

#### Option B: Edit the Script
Update the variables in the script:
```python
API_TOKEN = "your_actual_api_token_here"
ORGANIZATION = "your_organization_name"  # Optional
```

### 3. Get Your MagicPod API Token

1. Log in to your MagicPod account
2. Go to Settings → API Tokens
3. Create a new API token or copy an existing one
4. Make sure the token has appropriate permissions to read projects and batch run schedules

## Usage

Run the script:
```bash
python magicpod_batchrun_schedules.py
```

## Sample Output

```
=== MagicPod Scheduled Batch Runs ===
Organization: your-org
Timestamp: 2024-01-15 14:30:25
==================================================
Found 3 project(s)

Found 5 scheduled batch run(s) across all projects:

Project: your-org/project-1
  Scheduled Batch Runs: 2

  Schedule 1:
    ID: 12345
    Name: Daily Smoke Tests
    Status: active
    Cron Expression: 0 9 * * *
    Next Run: 2024-01-16T09:00:00Z
    Last Run: 2024-01-15T09:00:00Z

  Schedule 2:
    ID: 12346
    Name: Weekly Regression
    Status: active
    Cron Expression: 0 10 * * 1
    Next Run: 2024-01-22T10:00:00Z
    Last Run: 2024-01-15T10:00:00Z

--------------------------------------------------
```

## Error Handling

The script includes error handling for:
- Invalid API tokens
- Network connectivity issues
- API rate limiting
- Projects without scheduled batch runs

## Notes

- If you're not using an organization account, leave the `ORGANIZATION` variable as is
- The script will skip projects that don't have any scheduled batch runs
- All API calls use proper error handling to prevent crashes 