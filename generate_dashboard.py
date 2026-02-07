import os
from pathlib import Path
import json
import imaplib
import email
from datetime import datetime
import requests
from jinja2 import Environment, FileSystemLoader
from config import EMAIL_HOST, EMAIL_PORT, EMAIL_USER, EMAIL_PASSWORD, EMAIL_MAILBOXES, WEATHER_CITY, WEATHER_LAT, WEATHER_LONG, WEATHER_UNITS, PROJECTS

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

def get_email_counts():
    """Fetch email counts from multiple mailboxes"""
    email_counts = []
    
    try:
        # Connect to the email server
        mail = imaplib.IMAP4_SSL(EMAIL_HOST)
        mail.login(EMAIL_USER, EMAIL_PASSWORD)
        
        for mailbox in EMAIL_MAILBOXES:
            # Select mailbox
            mail.select(mailbox)
            
            # Search for unread emails
            status, messages = mail.search(None, 'UNSEEN')
            email_ids = messages[0].split()
            
            # Get mailbox user from email address
            mailbox_user = EMAIL_USER.split('@')[0] if '@' in EMAIL_USER else EMAIL_USER
            
            email_counts.append({
                'mailbox': mailbox_user,
                'count': len(email_ids)
            })
        
        mail.close()
        mail.logout()
        
    except Exception as e:
        print(f"Error fetching email counts: {e}")
        # Return default values if error occurs
        for mailbox in EMAIL_MAILBOXES:
            # Get mailbox user from email address
            mailbox_user = EMAIL_USER.split('@')[0] if '@' in EMAIL_USER else EMAIL_USER
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
        is_metric = WEATHER_UNITS == 'metric'
        params = {
            'latitude': WEATHER_LAT,  # London latitude
            'longitude': WEATHER_LONG,  # London longitude
            'current': 'temperature_2m,relative_humidity_2m,wind_speed_10m,weather_code',
            'temperature_unit': 'celsius' if is_metric else 'fahrenheit',
            'wind_speed_unit': 'kmh' if is_metric else 'mph',
            'precipitation_unit': 'mm' if is_metric else 'inch'
        }
        
        response = requests.get(url, params=params)
        data = response.json()
        
        # Extract weather information
        current = data.get('current', {})
        
        # Map weather code to description (simplified)
        weather_descriptions = {
            0: "Clear sky",
            1: "Mainly clear",
            2: "Partly cloudy",
            3: "Overcast",
            45: "Fog",
            48: "Depositing rime fog",
            51: "Light drizzle",
            53: "Moderate drizzle",
            55: "Dense drizzle",
            56: "Light freezing drizzle",
            57: "Dense freezing drizzle",
            61: "Slight rain",
            63: "Moderate rain",
            65: "Heavy rain",
            66: "Light freezing rain",
            67: "Heavy freezing rain",
            71: "Slight snow fall",
            73: "Moderate snow fall",
            75: "Heavy snow fall",
            77: "Snow grains",
            80: "Slight rain showers",
            81: "Moderate rain showers",
            82: "Violent rain showers",
            85: "Slight snow showers",
            86: "Heavy snow showers",
            95: "Thunderstorm",
            96: "Thunderstorm with slight hail",
            99: "Thunderstorm with heavy hail"
        }
        
        return {
            'city': WEATHER_CITY,
            'temperature': round(current.get('temperature_2m', 0)),
            'description': weather_descriptions.get(current.get('weather_code', 0), "Unknown"),
            'humidity': current.get('relative_humidity_2m', 0),
            'wind_speed': current.get('wind_speed_10m', 0)
        }
    
    except Exception as e:
        print(f"Error fetching weather data: {e}")
        return {
            'city': WEATHER_CITY,
            'temperature': 'N/A',
            'description': 'Error fetching data',
            'humidity': 'N/A',
            'wind_speed': 'N/A'
        }

def get_projects_from_directory():
    """Read projects from ~/Projects directory structure"""
    projects = []
    
    # Define the projects directory
    projects_dir = os.path.expanduser("~/Projects")
    
    # Check if the directory exists
    if not os.path.exists(projects_dir):
        print(f"Projects directory not found: {projects_dir}")
        return projects
    
    # Process customer projects
    customers_dir = os.path.join(projects_dir, "customers")
    if os.path.exists(customers_dir):
        customer_projects = get_projects_by_activity(customers_dir)
        for item in customer_projects:
            projects.append({
                'name': item['name'],
                'progress': 0,  # Customer projects typically don't have progress
                'status': 'Customer Project',
                'path': str(item['path']),
                'last_modified': item['last_mod']
            })
    
    # Process research projects
    research_dir = os.path.join(projects_dir, "research")
    if os.path.exists(research_dir):
        research_projects = get_projects_by_activity(research_dir)
        for item in research_projects:
            item_path = str(item['path'])
            # Check if it's a git repository to determine if it's active
            git_path = os.path.join(item_path, ".git")
            is_active = os.path.exists(git_path)
            
            projects.append({
                'name': item['name'],
                'progress': 0,  # Research projects typically don't have progress
                'status': 'Research Project' + (' (Active)' if is_active else ' (Inactive)'),
                'path': item_path,
                'last_modified': item['last_mod']
            })
    
    # Sort projects by last modified time (most recent first)
    projects.sort(key=lambda x: x['last_modified'], reverse=True)
    
    return projects

def generate_dashboard():
    """Generate the HTML dashboard"""
    
    # Create dist folder if it doesn't exist
    dist_folder = 'dist'
    if not os.path.exists(dist_folder):
        os.makedirs(dist_folder)
    
    # Copy styles.css to dist folder
    styles_source = 'styles.css'
    styles_dest = os.path.join(dist_folder, 'styles.css')
    
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
        'date': datetime.now().strftime("%A, %B %d, %Y")
    }
    
    # Set up Jinja2 environment
    env = Environment(loader=FileSystemLoader('templates'))
    template = env.get_template('dashboard.html')
    
    # Render template
    html_output = template.render(template_data)
    
    # Write to file in dist folder
    output_path = os.path.join(dist_folder, 'dashboard.html')
    with open(output_path, 'w') as f:
        f.write(html_output)
    
    print(f"Dashboard generated successfully! File saved to {output_path}")

if __name__ == '__main__':
    generate_dashboard()
