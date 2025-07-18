import requests
import os
from datetime import datetime, timedelta
import math
import pandas as pd
import json
import re
import pytz

# === CONFIGURATION ===
# You can set these as environment variables or update them directly
API_TOKEN = os.getenv("MAGICPOD_API_TOKEN", "YOUR_MAGICPOD_API_TOKEN")
ORGANIZATION = os.getenv("MAGICPOD_ORG_NAME", "YOUR_ORG_NAME")  # If using an organization account
BASE_URL = os.getenv("MAGICPOD_BASE_URL", "https://app.magicpod.com/api/v1.0")

HEADERS = {
    "Authorization": f"Token {API_TOKEN}",
    "Content-Type": "application/json"
}

CONFLUENCE_BASE_URL = os.getenv("CONFLUENCE_BASE_URL", "https://macromill.atlassian.net/wiki")
API_USER = os.getenv("CONFLUENCE_API_USER", "")  # <-- Your Atlassian email
CONFL_API_TOKEN = os.environ.get("CONFLUENCE_API_TOKEN")
if not CONFL_API_TOKEN:
    raise ValueError("CONFLUENCE_API_TOKEN environment variable not set")
PAGE_ID = os.getenv("CONFLUENCE_PAGE_ID", "")  # <-- Your Confluence page ID
if not PAGE_ID:
    raise ValueError("CONFLUENCE_PAGE_ID environment variable not set")

def update_confluence_page_with_html(html_file_path):
    # Read HTML content
    with open(html_file_path, "r") as f:
        html_content = f.read()

    # Get current page info
    auth = (API_USER, str(CONFL_API_TOKEN))
    headers = {"Content-Type": "application/json"}
    resp = requests.get(
        f"{CONFLUENCE_BASE_URL}/rest/api/content/{PAGE_ID}?expand=body.storage,version",
        auth=auth,
        headers=headers
    )
    if resp.status_code != 200:
        print("Failed to fetch page info:", resp.text)
        return

    data = resp.json()
    current_version = data["version"]["number"]
    title = data["title"]

    # Prepare update payload
    new_version = current_version + 1
    update_data = {
        "id": PAGE_ID,
        "type": "page",
        "title": title,
        "version": {"number": new_version},
        "body": {
            "storage": {
                "value": html_content,
                "representation": "storage"
            }
        }
    }

    # Update the page
    update_resp = requests.put(
        f"{CONFLUENCE_BASE_URL}/rest/api/content/{PAGE_ID}",
        data=json.dumps(update_data),
        auth=auth,
        headers=headers
    )

    if update_resp.status_code == 200:
        print("Page updated successfully!")
    else:
        print("Failed to update page:", update_resp.text)

def get_projects():
    """Retrieve all projects from MagicPod"""
    if ORGANIZATION and ORGANIZATION != "YOUR_ORG_NAME":
        url = f"{BASE_URL}/{ORGANIZATION}/projects/"
        params = {}
    else:
        url = f"{BASE_URL}/projects/"
        params = {}
    
    try:
        response = requests.get(url, headers=HEADERS, params=params)
        response.raise_for_status()
        data = response.json()
        # If the response is a dict with 'projects', return that list
        if isinstance(data, dict) and "projects" in data:
            return data["projects"]
        # If the response is already a list, return as is
        if isinstance(data, list):
            return data
        # Otherwise, return empty list
        return []
    except requests.exceptions.RequestException as e:
        print(f"Error fetching projects: {e}")
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

def read_excel_schedule(file_path="mp_batch_plan.xlsx"):
    """Read the batch schedule from the Excel file and return as a DataFrame."""
    try:
        df = pd.read_excel(file_path)
        # Ensure required columns exist
        required_cols = ["Project", "Batch_Name", "Day", "Start_Time", "Duration"]
        for col in required_cols:
            if col not in df.columns:
                raise ValueError(f"Missing required column: {col}")
        return df
    except Exception as e:
        print(f"Error reading Excel file: {e}")
        return None

def get_next_week_dates():
    """Return a dict mapping day names to the next date for that day in the upcoming week."""
    today = datetime.now().date()
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    next_dates = {}
    for i in range(7):
        day = (today + timedelta(days=i))
        day_name = day.strftime("%A")
        if day_name not in next_dates:
            next_dates[day_name] = day
    return next_dates

def print_batch_schedule_calendar(df):
    """Print a calendar of batch schedules for the next 7 days in a matrix format."""
    # Define days and time slots
    days_order = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
    days_short = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
    time_slots = [f"{str(h).zfill(2)}:{str(m).zfill(2)}" for h in range(0, 24) for m in (0, 30)]  # 00:00, 00:30, ..., 23:30
    
    # Map day names to short names for display
    day_name_to_short = dict(zip(days_order, days_short))
    # Map short names to column index
    short_to_col = {d: i for i, d in enumerate(days_short)}
    # Build a 2D matrix: rows=time slots, cols=days
    matrix = [[[] for _ in range(7)] for _ in range(len(time_slots))]

    # Get the next date for each day of week (to filter only next 7 days)
    next_dates = get_next_week_dates()  # e.g., {"Monday": date, ...}
    valid_days = set(next_dates.keys())

    short_to_full_day = {
        "Sun": "Sunday", "Mon": "Monday", "Tue": "Tuesday", "Wed": "Wednesday",
        "Thu": "Thursday", "Fri": "Friday", "Sat": "Saturday"
    }
    
    for idx, row in df.iterrows():
        project = row["Project"]
        batch_name = row["Batch_Name"]
        day_raw = str(row["Day"]) if row["Day"] is not None else ""
        start_time = row["Start_Time"]
        for day_part in day_raw.split(','):
            day_part = day_part.strip()
            day = short_to_full_day.get(day_part, day_part)
            if day not in valid_days:
                print(f"[DEBUG] Skipping row {idx}: day '{day}' not in valid_days {valid_days}")
                continue
            # Get column index for the day
            day_short = day_name_to_short.get(day)
            if day_short is None:
                print(f"[DEBUG] Skipping row {idx}: day_short for '{day}' is None")
                continue
            col = short_to_col[day_short]
            # Parse start time and find the slot
            try:
                t = pd.to_datetime(str(start_time)).time()
                slot = t.hour * 2 + (1 if t.minute >= 30 else 0)
                time_str = t.strftime('%H:%M')
                # Parse duration
                duration_str = str(row["Duration"]) if row["Duration"] is not None else "00:00:00"
                h, m, s = [int(x) for x in duration_str.split(":")] if ":" in duration_str else (0, 0, 0)
                duration_minutes = h * 60 + m + s // 60
                # Calculate how many slots to fill
                start_minute = t.hour * 60 + t.minute
                # The first slot may be partial, so we add the offset
                minutes_in_first_slot = 30 - (start_minute % 30)
                remaining_minutes = max(duration_minutes - minutes_in_first_slot, 0)
                slots_to_fill = 1 + math.ceil(remaining_minutes / 30) if duration_minutes > 0 else 1
            except Exception as e:
                print(f"[DEBUG] Skipping row {idx}: could not parse time/duration '{start_time}'/'{duration_str}' ({e})")
                continue
            # Place batch name and time in the matrix for all slots covered by duration
            label = f"{batch_name} ({time_str})"
            for slot_offset in range(slots_to_fill):
                slot_idx = slot + slot_offset
                if slot_idx >= len(matrix):
                    break
                print(f"[DEBUG] Row {idx}: day={day}, start_time={start_time}, duration={duration_str}, slot={slot_idx}, col={col}, label={label}")
                if label not in matrix[slot_idx][col]:
                    matrix[slot_idx][col].append(label)

    cell_width = 20
    # Print header
    header = "      " + " ".join([f"{d:^{cell_width}}" for d in days_short])
    print("\n=== Batch Schedule Calendar (Matrix View) ===\n")
    print(header)
    print("    +" + (f"{'-'*cell_width}+" * 7))
    # Print each row and build for Excel output
    matrix_rows = []
    # --- Assign unique colors to each batch name ---
    unique_batch_names = set()
    for idx, row in df.iterrows():
        batch_name = str(row["Batch_Name"]).strip()
        unique_batch_names.add(batch_name)  # use full name including bracket
    color_palette = [
        '#e6194b', '#3cb44b', '#ffe119', '#4363d8', '#f58231', '#911eb4', '#46f0f0', '#f032e6',
        '#bcf60c', '#fabebe', '#008080', '#e6beff', '#9a6324', '#fffac8', '#800000', '#aaffc3',
        '#808000', '#ffd8b1', '#000075', '#808080', '#ffffff', '#000000'
    ]
    batch_name_to_color = {}
    for idx, name in enumerate(sorted(unique_batch_names, key=lambda x: x.lower())):
        batch_name_to_color[name] = color_palette[idx % len(color_palette)]
    for i, slot in enumerate(time_slots):
        row_str = f"{slot} |"
        excel_row = [slot]
        for j in range(7):
            cell_batches = matrix[i][j]
            cell_batches_bulleted = []
            for b in cell_batches:
                batch_full = b.split(" (")[0].strip()  # get the full batch name (with bracket if present)
                # Actually, b is like 'SE Daily (JP) (11:00)', so we want the part before the last ' ('
                # Let's use rsplit to split only on the last ' ('
                batch_full = b.rsplit(' (', 1)[0].strip()
                color = batch_name_to_color.get(batch_full, "#000000")
                label_html = f"<span style='background:{color};color:white;padding:2px 8px;border-radius:12px;margin-right:4px;display:inline-block;font-size:90%;'>{b}</span>"
                cell_batches_bulleted.append(label_html)
            cell_disp = "<br />".join(cell_batches_bulleted) if cell_batches_bulleted else ""
            cell_disp_final = cell_disp
            td_style = "word-break: break-word; white-space: normal; vertical-align: top;"
            if len(cell_batches) >= 3:
                html_cell = f"<td style='background-color:crimson;color:white;{td_style}'>{cell_disp}</td>"
            else:
                html_cell = f"<td style='{td_style}'>{cell_disp}</td>"
            excel_row.append(html_cell)
            row_str += f"{cell_disp_final[:cell_width]:^{cell_width}}|"
        print(row_str)
        print("    +" + (f"{'-'*cell_width}+" * 7))
        matrix_rows.append(excel_row)
    print()

    # Output to HTML file (merged: all batches per day/slot in one cell)
    columns = ["Time"] + days_short
    df_out = pd.DataFrame(matrix_rows, columns=columns)  # type: ignore
    # --- Create legend of colored labels for each batch name ---
    # Modern CSS style block
    style_block = '''<style>
    body { font-family: 'Segoe UI', 'Roboto', 'Arial', sans-serif; background: #f7f7fa; }
    table { border-collapse: separate; border-spacing: 0; width: 100%; background: #fff; box-shadow: 0 2px 8px rgba(0,0,0,0.07); border-radius: 12px; overflow: hidden; }
    th, td { padding: 8px 12px; text-align: center; }
    th { background: #2d3e50; color: #fff; font-weight: 600; }
    tr:nth-child(even) { background: #f4f6fa; }
    tr:hover { background: #eaf1fb; }
    td { border-bottom: 1px solid #e0e0e0; font-size: 15px; }
    .legend { margin-bottom: 18px; }
    .legend-batch { display: inline-block; margin-right: 10px; margin-bottom: 6px; padding: 3px 12px; border-radius: 16px; font-size: 14px; font-weight: 500; box-shadow: 0 1px 3px rgba(0,0,0,0.08); }
    </style>'''
    # Add page title at the top
    jst = pytz.timezone('Asia/Tokyo')
    generated_time = datetime.now(jst).strftime('%Y-%m-%d %H:%M:%S JST')
    page_title = f"<div style='font-size:2.2em;font-weight:700;color:#2d3e50;margin-bottom:8px;margin-top:18px;letter-spacing:1px;'>MagicPod Batch Schedule</div>"
    page_title += f"<div style='font-size:1.1em;color:#2d3e50;margin-bottom:18px;'>Calendar generated: {generated_time}</div>"
    legend_html = "<div class='legend'><b>Batch Labels:</b> "
    for batch_name in sorted(unique_batch_names, key=lambda x: x.lower()):
        display_name = next((row.Batch_Name for row in df.itertuples(index=False) if str(row.Batch_Name).strip() == batch_name), batch_name)
        color = batch_name_to_color[batch_name]
        legend_html += f"<span class='legend-batch' style='background:{color};color:white;'>{display_name}</span>"
    legend_html += "</div>"
    # Build HTML table manually to preserve <td> styles
    html = page_title + style_block + legend_html
    html += "<table>\n<tr>" + ''.join([f"<th>{col}</th>" for col in columns]) + "</tr>\n"
    for _, row in df_out.iterrows():
        html += "<tr>"
        for idx, cell in enumerate(row):
            if idx == 0:
                html += f"<td>{cell}</td>"
            else:
                if not cell or cell == "<td style='word-break: break-word; white-space: normal; vertical-align: top;'></td>":
                    html += "<td></td>"
                else:
                    if cell.startswith("<td"):
                        inner = cell.split('>', 1)[1].rsplit('</td>', 1)[0]
                        html += f"<td>{inner}</td>"
                    else:
                        html += f"<td>{cell}</td>"
        html += "</tr>\n"
    html += "</table>"
    with open("batch_schedule_calendar.html", "w") as f:
        f.write(html)
    print("Modern stylish calendar matrix has been saved to 'batch_schedule_calendar.html'.")

def html_to_confluence_table_xml(html_file_path, xml_file_path):
    """Convert the generated HTML file to Confluence Storage Format XML with only supported tags/macros."""
    import re
    from bs4 import BeautifulSoup, Tag
    with open(html_file_path, "r") as f:
        html_content = f.read()
    soup = BeautifulSoup(html_content, "html.parser")
    # Color mapping for Confluence status macro
    color_map = {
        '#e6194b': 'Red', '#3cb44b': 'Green', '#ffe119': 'Yellow', '#4363d8': 'Blue',
        '#f58231': 'Yellow', '#911eb4': 'Purple', '#46f0f0': 'Grey', '#f032e6': 'Purple',
        '#bcf60c': 'Green', '#fabebe': 'Grey', '#008080': 'Blue', '#e6beff': 'Purple',
        '#9a6324': 'Grey', '#fffac8': 'Yellow', '#800000': 'Red', '#aaffc3': 'Green',
        '#808000': 'Yellow', '#ffd8b1': 'Yellow', '#000075': 'Blue', '#808080': 'Grey',
        '#ffffff': 'Grey', '#000000': 'Grey',
    }
    # Legend
    legend_spans = soup.find_all("span", class_="legend-batch")
    legend_xml = ["<p><strong>Batch Labels:</strong> "]
    for span in legend_spans:
        batch_name = span.text.strip()
        style = span.get("style", "")
        color_match = re.search(r"background(?:-color)?:\s*([^;]+);", style)
        color = color_match.group(1) if color_match else "Grey"
        macro_color = color_map.get(color.lower(), 'Grey')
        legend_xml.append(
            f'<ac:structured-macro ac:name="status">'
            f'<ac:parameter ac:name="title">{batch_name}</ac:parameter>'
            f'<ac:parameter ac:name="color">{macro_color}</ac:parameter>'
            f'</ac:structured-macro> '
        )
    legend_xml.append("</p>")
    # Table
    table = soup.find("table")
    table_xml = ["<table>"]
    # Only process if table is a Tag
    if table and isinstance(table, Tag):
        for row in [r for r in table.find_all("tr") if isinstance(r, Tag)]:
            table_xml.append("<tr>")
            for cell in [c for c in row.find_all(["th", "td"]) if isinstance(c, Tag)]:
                cell_content = ""
                for span in cell.find_all("span"):
                    batch_name = span.text.strip()
                    style = span.get("style", "")
                    color_match = re.search(r"background(?:-color)?:\s*([^;]+);", style)
                    color = color_match.group(1) if color_match else "Grey"
                    macro_color = color_map.get(color.lower(), 'Grey')
                    cell_content += (
                        f'<ac:structured-macro ac:name="status">'
                        f'<ac:parameter ac:name="title">{batch_name}</ac:parameter>'
                        f'<ac:parameter ac:name="color">{macro_color}</ac:parameter>'
                        f'</ac:structured-macro><br/>'
                    )
                if not cell_content:
                    cell_content = cell.get_text(" ", strip=True)
                tag = cell.name
                table_xml.append(f"<{tag}>{cell_content}</{tag}>")
            table_xml.append("</tr>")
    table_xml.append("</table>")
    # Write XML file
    with open(xml_file_path, "w") as f:
        jst = pytz.timezone('Asia/Tokyo')
        generated_time = datetime.now(jst).strftime('%Y-%m-%d %H:%M:%S JST')
        f.write('<ac:structured-macro ac:name="info"><ac:rich-text-body><p><strong>MagicPod Batch Schedule</strong></p>'
                f'<p>Calendar generated: {generated_time}</p></ac:rich-text-body></ac:structured-macro>\n')
        f.write(''.join(legend_xml))
        f.write(''.join(table_xml))
    return xml_file_path

def send_calendar_to_confluence(df):
    # 1. Generate HTML
    print_batch_schedule_calendar(df)
    # 2. Convert HTML to Confluence XML
    xml_file = html_to_confluence_table_xml("batch_schedule_calendar.html", "batch_schedule_calendar.xml")
    # 3. Send to Confluence
    update_confluence_page_with_html(xml_file)

def main():
    """Main function to retrieve and display all projects (without batch run schedules)"""
    print("=== MagicPod Projects ===")
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
    print("Projects fetched:")
    for project in projects:
        project_name = project.get("fullName") or project.get("name") or project.get("id")
        print(" -", project_name)
    if not projects:
        print("No projects found or error occurred while fetching projects.")
        return
    
    print(f"Found {len(projects)} project(s)")
    print()
    # No schedule fetching or display

def main_excel_calendar():
    """Main function to generate batch schedule calendar from Excel file and send to Confluence."""
    df = read_excel_schedule()
    if df is None:
        print("No schedule data available.")
        return
    print("\n[DEBUG] Data read from Excel file:")
    print(df)
    send_calendar_to_confluence(df)

if __name__ == "__main__":
    main_excel_calendar()