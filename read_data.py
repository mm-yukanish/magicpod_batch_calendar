import requests
import json
import os
from datetime import datetime

# === CONFIGURATION ===
# You can set these as environment variables or update them directly
API_TOKEN = os.getenv("MAGICPOD_API_TOKEN", "YOUR_MAGICPOD_API_TOKEN")
ORGANIZATION = os.getenv("MAGICPOD_ORG_NAME", "YOUR_ORG_NAME")  # If using an organization account
BASE_URL = "https://app.magicpod.com/api/v1.0"

HEADERS = {
    "Authorization": f"Token {API_TOKEN}",
    "Content-Type": "application/json"
}

def get_projects():
    """Retrieve all projects from MagicPod"""
    url = f"{BASE_URL}/organizationprojects/"
    params = {"organization": ORGANIZATION} if ORGANIZATION and ORGANIZATION != "YOUR_ORG_NAME" else {}
    
    try:
        response = requests.get(url, headers=HEADERS, params=params)
        response.raise_for_status()
        return response.json()["projects"]
    except requests.exceptions.RequestException as e:
        print(f"Error fetching projects: {e}")
        return []

def get_scheduled_batch_runs(project):
    """Retrieve scheduled batch runs for a specific project"""
    project_fullname = project["fullName"]  # e.g., "org/project"
    url = f"{BASE_URL}/projects/{project_fullname}/batch-run/schedules/"
    
    try:
        response = requests.get(url, headers=HEADERS)
        if response.status_code == 404:
            return []  # No schedules for this project
        response.raise_for_status()
        return response.json().get("schedules", [])
    except requests.exceptions.RequestException as e:
        print(f"Error fetching schedules for project {project_fullname}: {e}")
        return []

def format_schedule_info(schedule):
    """Format schedule information for better readability"""
    info = []
    info.append(f"    ID: {schedule.get('id', 'N/A')}")
    info.append(f"    Name: {schedule.get('name', 'N/A')}")
    info.append(f"    Status: {schedule.get('status', 'N/A')}")
    
    if 'cron' in schedule:
        info.append(f"    Cron Expression: {schedule['cron']}")
    
    if 'next_run_at' in schedule:
        next_run = schedule['next_run_at']
        if next_run:
            info.append(f"    Next Run: {next_run}")
    
    if 'last_run_at' in schedule:
        last_run = schedule['last_run_at']
        if last_run:
            info.append(f"    Last Run: {last_run}")
    
    return "\n".join(info)

def main():
    """Main function to retrieve and display all scheduled batch runs"""
    print("=== MagicPod Scheduled Batch Runs ===")
    print(f"Organization: {ORGANIZATION if ORGANIZATION != 'YOUR_ORG_NAME' else 'All'}")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)
    
    # Check if API token is configured
    if API_TOKEN == "YOUR_MAGICPOD_API_TOKEN":
        print("ERROR: Please set your MagicPod API token!")
        print("You can either:")
        print("1. Set the MAGICPOD_API_TOKEN environment variable")
        print("2. Update the API_TOKEN variable in the script")
        return
    
    projects = get_projects()
    
    if not projects:
        print("No projects found or error occurred while fetching projects.")
        return
    
    print(f"Found {len(projects)} project(s)")
    print()
    
    all_schedules = []
    for project in projects:
        schedules = get_scheduled_batch_runs(project)
        for schedule in schedules:
            all_schedules.append({
                "project": project["fullName"],
                "schedule": schedule
            })
    
    if not all_schedules:
        print("No scheduled batch runs found across all projects.")
        return
    
    print(f"Found {len(all_schedules)} scheduled batch run(s) across all projects:")
    print()
    
    # Group by project for better organization
    projects_with_schedules = {}
    for entry in all_schedules:
        project_name = entry['project']
        if project_name not in projects_with_schedules:
            projects_with_schedules[project_name] = []
        projects_with_schedules[project_name].append(entry['schedule'])
    
    # Output results organized by project
    for project_name, schedules in projects_with_schedules.items():
        print(f"Project: {project_name}")
        print(f"  Scheduled Batch Runs: {len(schedules)}")
        print()
        
        for i, schedule in enumerate(schedules, 1):
            print(f"  Schedule {i}:")
            print(format_schedule_info(schedule))
            print()
        
        print("-" * 50)

if __name__ == "__main__":
    main()