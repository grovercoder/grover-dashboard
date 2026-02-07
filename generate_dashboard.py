import os
import json
import imaplib
import email
from datetime import datetime
import requests
from jinja2 import Environment, FileSystemLoader
from config import EMAIL_HOST, EMAIL_PORT, EMAIL_USER, EMAIL_PASSWORD, EMAIL_MAILBOXES, WEATHER_API_KEY, WEATHER_CITY, WEATHER_COUNTRY, WEATHER_UNITS, PROJECTS

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
            
            email_counts.append({
                'mailbox': mailbox,
                'count': len(email_ids)
            })
        
        mail.close()
        mail.logout()
        
    except Exception as e:
        print(f"Error fetching email counts: {e}")
        # Return default values if error occurs
        for mailbox in EMAIL_MAILBOXES:
            email_counts.append({
                'mailbox': mailbox,
                'count': 0
            })
    
    return email_counts

def get_weather():
    """Fetch weather data from API-Ninjas Weather API"""
    try:
        url = "https://api.api-ninjas.com/v1/weather"
        params = {
            'city': WEATHER_CITY,
            'country': WEATHER_COUNTRY
        }
        
        headers = {
            'X-Api-Key': WEATHER_API_KEY
        }
        
        response = requests.get(url, params=params, headers=headers)
        data = response.json()
        
        return {
            'city': WEATHER_CITY,
            'temperature': round(data.get('temp', 0)),
            'description': data.get('cloud_pct', 0),  # API-Ninjas doesn't provide description
            'humidity': data.get('humidity', 0),
            'wind_speed': data.get('wind_speed', 0)
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

def get_most_recent_modification_time(path):
    """Get the most recent modification time of files in a directory"""
    if not os.path.exists(path):
        return 0
    
    max_time = 0
    for root, dirs, files in os.walk(path):
        for file in files:
            file_path = os.path.join(root, file)
            try:
                file_time = os.path.getmtime(file_path)
                if file_time > max_time:
                    max_time = file_time
            except (OSError, IOError):
                # Skip files that can't be accessed
                continue
    
    return max_time

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
        for item in os.listdir(customers_dir):
            item_path = os.path.join(customers_dir, item)
            if os.path.isdir(item_path):
                projects.append({
                    'name': item,
                    'progress': 0,  # Customer projects typically don't have progress
                    'status': 'Customer Project',
                    'path': item_path,
                    'last_modified': get_most_recent_modification_time(item_path)
                })
    
    # Process research projects
    research_dir = os.path.join(projects_dir, "research")
    if os.path.exists(research_dir):
        for item in os.listdir(research_dir):
            item_path = os.path.join(research_dir, item)
            if os.path.isdir(item_path):
                # Check if it's a git repository to determine if it's active
                git_path = os.path.join(item_path, ".git")
                is_active = os.path.exists(git_path)
                
                projects.append({
                    'name': item,
                    'progress': 0,  # Research projects typically don't have progress
                    'status': 'Research Project' + (' (Active)' if is_active else ' (Inactive)'),
                    'path': item_path,
                    'last_modified': get_most_recent_modification_time(item_path)
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
