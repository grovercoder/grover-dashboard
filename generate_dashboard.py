import os
import re
import subprocess
from pathlib import Path
import json
import imaplib
import email
from datetime import datetime
import requests
from jinja2 import Environment, FileSystemLoader
from config import dashboard_config
import argparse

def get_projects_by_activity(base_path):
    project_list = []
    base = Path(base_path)

    # Iterate through each item in the projects folder
    for entry in base.iterdir():
        if entry.is_dir():
            latest_mtime = 0
            
            # Deep dive into the project to find the newest file
            for root, _, files in os.walk(entry):
                for f in files:
                    try:
                        file_path = os.path.join(root, f)
                        mtime = os.path.getmtime(file_path)
                        if mtime > latest_mtime:
                            latest_mtime = mtime
                    except (OSError, PermissionError):
                        continue
            
            # If the folder is empty, use the folder's own mtime
            if latest_mtime == 0:
                latest_mtime = entry.stat().st_mtime
                
            project_list.append({
                'name': entry.name,
                'path': entry,
                'last_mod': latest_mtime
            })

    # Sort by timestamp (descending = most recent first)
    project_list.sort(key=lambda x: x['last_mod'], reverse=True)
    return project_list

def get_project_last_modified_date(project_path, ignore=None):
    """Determine the last modified date for a project using multiple methods"""
    max_date = 0
    checklist_path = project_path / "docs/acceptance_checklist.md"
    
    # 1. Check for git repository and get most recent commit date
    git_path = project_path / ".git"
    if git_path.exists():
        try:
            # Get the most recent commit date
            result = subprocess.run(
                ["git", "log", "-1", "--format=%ct"],
                cwd=project_path,
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                commit_timestamp = int(result.stdout.strip())
                max_date = max(max_date, commit_timestamp)
        except Exception:
            pass
    
    # 2. Find the max modified time of project files
    try:
        file_mtime = get_latest_mtime(project_path, ignore=checklist_path.resolve())
        max_date = max(max_date, file_mtime)
    except Exception:
        pass
    
    # 3. Check acceptance_checklist.md for last modified date
    if checklist_path.exists():
        try:
            with open(checklist_path, 'r') as f:
                content = f.read()
            
            # Look for the Last modified line
            last_modified_match = re.search(r'Last modified:\s*(\d{4}-\d{2}-\d{2})', content)
            
            if last_modified_match:
                last_modified_str = last_modified_match.group(1)
                checklist_date = datetime.strptime(last_modified_str, '%Y-%m-%d')
                checklist_timestamp = checklist_date.timestamp()
                max_date = max(max_date, checklist_timestamp)
        except Exception:
            pass
    
    return max_date

def get_progress(project_path):
    """Calculate project progress based on multiple methods"""
    # 1. Tier 1: Python Acceptance Tests
    test_file = project_path / "tests/acceptance.py"
    if test_file.exists():
        try:
            # Run pytest quietly, just collecting results
            # We use --collect-only first to see total tests, then run to see passes
            result = subprocess.run(
                ["pytest", test_file, "--json-report"], # Requires pytest-json-report plugin
                capture_output=True, text=True
            )
            
            # Simple fallback if you don't want plugins: Check exit code & output
            # 0 = all pass, 1 = some fail, 5 = no tests found
            process = subprocess.run(["pytest", "-q", "--tb=no", test_file], capture_output=True, text=True)
            output = process.stdout
            
            # Extract "5 passed, 2 failed" style strings
            passed = re.search(r'(\d+) passed', output)
            failed = re.search(r'(\d+) failed', output)
            
            p_count = int(passed.group(1)) if passed else 0
            f_count = int(failed.group(1)) if failed else 0
            
            if (p_count + f_count) > 0:
                return round((p_count / (p_count + f_count)) * 100, 2)
        except Exception:
            pass # Fall back to next tier if pytest fails

    # 2. Tier 2: Markdown Checklist
    checklist_path = project_path / "docs/planning/acceptance.md"
    if not checklist_path.exists():
        checklist_path = project_path / "docs/acceptance_checklist.md"

    if checklist_path.exists():
        try:
            with open(checklist_path, 'r') as f:
                content = f.read()
                done = len(re.findall(r'\[x\]', content, re.IGNORECASE))
                todo = len(re.findall(r'\[ \]', content, re.IGNORECASE))
                avg = round((done / (done + todo)) * 100, 2) if done + todo > 0 else 0
                print(f'>> checklist_path: {str(checklist_path)} : avg: {avg}')
                if (done + todo) > 0:
                    return avg
        except Exception:
            pass

    # 3. Tier 3: Unknown
    return "Unknown"

def get_project_status(project_path):
    """Determine project status based on last modified date in acceptance checklist"""
    # the "new" path to find the acceptance criteria
    checklist_path = project_path / "docs/planning/acceptance.md"

    if not checklist_path.exists():
        # the old path to find the acceptance criteria
        checklist_path = project_path / "docs/acceptance_checklist.md"
    
    if not checklist_path.exists():
        return "Unknown"
    
    try:
        with open(checklist_path, 'r') as f:
            content = f.read()
            
        # Look for the Last modified line
        last_modified_match = re.search(r'Last modified:\s*(\d{4}-\d{2}-\d{2})', content)
        
        if not last_modified_match:
            return "Unknown"
            
        last_modified_str = last_modified_match.group(1)
        last_modified_date = datetime.strptime(last_modified_str, '%Y-%m-%d')
        current_date = datetime.now()
        days_diff = (current_date - last_modified_date).days
        
        if days_diff < 30:
            return "Active"
        elif days_diff < 180:
            return "Dormant"
        elif days_diff < 365:
            return "Stale"
        else:
            return "Abandoned"
            
    except Exception:
        return "Unknown"

def get_email_counts():
    """Fetch email counts from multiple mailboxes across all email accounts"""
    email_counts = []
    
    try:
        # Iterate through all email accounts
        for account in dashboard_config.email:
            # Connect to the email server
            mail = imaplib.IMAP4_SSL(account.host)
            mail.login(account.user, account.password)
            
            for mailbox in account.mailboxes:
                # Select mailbox
                mail.select(mailbox)
                
                # Search for unread emails
                status, messages = mail.search(None, 'UNSEEN')
                email_ids = messages[0].split()
                
                # Get mailbox user from email address
                mailbox_user = account.user.split('@')[0] if '@' in account.user else account.user
                
                email_counts.append({
                    'mailbox': mailbox_user,
                    'count': len(email_ids)
                })
            
            mail.close()
            mail.logout()
        
    except Exception as e:
        print(f"Error fetching email counts: {e}")
        # Return default values if error occurs
        if dashboard_config.email:
            for account in dashboard_config.email:
                for mailbox in account.mailboxes:
                    # Get mailbox user from email address
                    mailbox_user = account.user.split('@')[0] if '@' in account.user else account.user
                    email_counts.append({
                        'mailbox': mailbox_user,
                        'count': 0
                    })
        else:
            # Fallback to environment variables if no account
            mailbox_user = os.getenv('EMAIL_USER', '').split('@')[0] if '@' in os.getenv('EMAIL_USER', '') else os.getenv('EMAIL_USER', '')
            email_counts.append({
                'mailbox': mailbox_user,
                'count': 0
            })
    
    return email_counts

def get_weather():
    """Fetch weather data from Open-Meteo API"""
    try:
        # Open-Meteo API endpoint for current weather
        url = "https://api.open-meteo.com/v1/forecast"
        
        # Get coordinates for the city (this is a simplified approach)
        # For a more robust solution, you'd want to use a geocoding API
        is_metric = dashboard_config.weather.units == 'metric'
        params = {
            'latitude': dashboard_config.weather.lat,  # London latitude
            'longitude': dashboard_config.weather.long,  # London longitude
            'current': 'temperature_2m,relative_humidity_2m,wind_speed_10m,weather_code',
            'temperature_unit': 'celsius' if is_metric else 'fahrenheit',
            'wind_speed_unit': 'kmh' if is_metric else 'mph',
            'precipitation_unit': 'mm' if is_metric else 'inch'
        }
        
        response = requests.get(url, params=params)
        data = response.json()
        
        # Extract weather information
        current = data.get('current', {})
        
        # Create WeatherResponse model instance
        weather_response = {
            'code': current.get('weather_code', 0),
            'city': dashboard_config.weather.city,
            'temperature': round(current.get('temperature_2m', 0)),
            'humidity': current.get('relative_humidity_2m', 0),
            'wind_speed': current.get('wind_speed_10m', 0)
        }
        
        # Use the model to compute derived fields
        from models import WeatherResponse
        weather_model = WeatherResponse(**weather_response)
        
        return weather_model
            
    except Exception as e:
        print(f"Error fetching weather data: {e}")
        # Return a default WeatherResponse model
        from models import WeatherResponse
        return WeatherResponse(
            code=0,
            city=dashboard_config.weather.city,
            temperature=0,
            humidity=0,
            wind_speed=0,
            description="Error fetching data"
        )

def get_projects_from_directory():
    """Read projects from ~/Projects directory structure"""
    projects = []
    
    # Process research projects
    for item in dashboard_config.projects:
        if not item.exists():
            continue

        
        # Calculate progress
        progress = get_progress(item)
        
        # Determine project status based on acceptance checklist
        status = get_project_status(item)
        
        # Get the last modified date using the new method
        # Ignore the acceptance checklist file when calculating file modification times
        checklist_path = item / "docs/acceptance_checklist.md"
        ignore_paths = [str(checklist_path)] if checklist_path.exists() else []
        
        last_modified_timestamp = get_project_last_modified_date(item, ignore=ignore_paths)
        
        # Convert timestamp to datetime for display
        last_modified_datetime = datetime.fromtimestamp(last_modified_timestamp)
        
        projects.append({
            'name': item.name,
            'project_path': item.resolve().absolute(),
            'status': status,
            'progress': progress,
            'path': item.resolve().absolute(),
            'last_modified': last_modified_timestamp,
            'last_modified_string': last_modified_datetime.strftime('%Y-%m-%d %H:%M')
        })
    
    # Sort projects by last modified time (most recent first)
    # Handle None values by sorting them last
    projects.sort(key=lambda x: x['last_modified'] or 0, reverse=True)
    
    return projects

def get_latest_mtime(project_path, ignore=None):
    # Get the mtime of the folder itself as a starting point
    max_mtime = project_path.stat().st_mtime
    
    # If ignore is a string, convert to list
    if isinstance(ignore, str):
        ignore = [ignore]
    
    # Recursively check all files
    for file in project_path.rglob('*'):
        # Skip hidden files/folders (like .git, .venv, or __pycache__)
        if any(part.startswith('.') for part in file.parts):
            continue
            
        # Skip ignored paths
        if ignore:
            file_path_str = str(file)
            if file_path_str in ignore:
                continue
                
        try:
            mtime = file.stat().st_mtime
            if mtime > max_mtime:
                max_mtime = mtime
        except OSError:
            # Handle cases where files might be deleted/locked during scan
            continue
            
    return max_mtime

def generate_dashboard():
    """Generate the HTML dashboard"""
    
    # Create dist folder if it doesn't exist
    dist_folder = Path(__file__).parent / 'dist'
    dist_folder.mkdir(parents=True, exist_ok=True)
    
    # Copy styles.css to dist folder
    styles_source = Path(__file__).parent / 'styles.css'
    styles_dest = dist_folder / 'styles.css'
    
    if os.path.exists(styles_source):
        with open(styles_source, 'r') as f:
            styles_content = f.read()
        
        with open(styles_dest, 'w') as f:
            f.write(styles_content)
    else:
        # Create default styles if file doesn't exist
        default_styles = """body {
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    margin: 0;
    padding: 20px;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    min-height: 100vh;
}

.container {
    max-width: 1200px;
    margin: 0 auto;
}

header {
    text-align: center;
    margin-bottom: 30px;
    padding: 20px;
    background: rgba(255, 255, 255, 0.1);
    border-radius: 10px;
    backdrop-filter: blur(10px);
}

.dashboard-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 20px;
    margin-bottom: 30px;
}

.card {
    background: rgba(255, 255, 255, 0.15);
    border-radius: 10px;
    padding: 20px;
    backdrop-filter: blur(10px);
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
}

.card h2 {
    margin-top: 0;
    border-bottom: 1px solid rgba(255, 255, 255, 0.3);
    padding-bottom: 10px;
}

.email-item {
    display: flex;
    justify-content: space-between;
    padding: 8px 0;
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.email-item:last-child {
    border-bottom: none;
}

.project-item {
    margin-bottom: 15px;
}

.progress-bar {
    width: 100%;
    height: 10px;
    background: rgba(255, 255, 255, 0.2);
    border-radius: 5px;
    overflow: hidden;
    margin-top: 5px;
}

.progress-fill {
    height: 100%;
    background: #4CAF50;
    border-radius: 5px;
}

.weather-icon {
    font-size: 3em;
    text-align: center;
    margin: 10px 0;
}

.timestamp {
    text-align: center;
    font-size: 0.9em;
    opacity: 0.8;
}"""
        
        with open(styles_dest, 'w') as f:
            f.write(default_styles)
    
    # Get data
    email_counts = get_email_counts()
    weather_data = get_weather()
    projects = get_projects_from_directory()
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Prepare data for template
    template_data = {
        'email_counts': email_counts,
        'weather': weather_data,
        'projects': projects,
        'current_time': current_time,
        'date': datetime.now().strftime("%a, %b %d, %Y"),
        'temp_units': 'C' if dashboard_config.weather.units == 'metric' else 'F',
        'wind_units': 'kph' if dashboard_config.weather.units == 'metric' else 'mph'
    }
    
    # Set up Jinja2 environment
    template_dir = Path(__file__).parent / "templates"
    env = Environment(loader=FileSystemLoader(template_dir.resolve()))
    template = env.get_template('dashboard.html')
    
    # Render template
    html_output = template.render(template_data)
    
    # Write to file in dist folder
    output_path = dist_folder / 'dashboard.html'
    output_path.write_text(html_output)
    
    print(f"Dashboard generated successfully! File saved to {str(output_path)}")

def list_projects():
    """Print each project from dashboard_config.projects to stdout as a single line"""
    for project in dashboard_config.projects:
        print(str(project))

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Generate dashboard or list projects')
    parser.add_argument('--list-projects', action='store_true', 
                        help='Print each project path to stdout as a single line')
    
    args = parser.parse_args()
    
    if args.list_projects:
        list_projects()
    else:
        generate_dashboard()
