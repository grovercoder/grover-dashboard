import os
import sys
from pathlib import Path

# Try to import tomllib (Python 3.11+) or toml (older versions)
try:
    import tomllib
except ImportError:
    try:
        import toml as tomllib
    except ImportError:
        raise ImportError("Either 'tomllib' (Python 3.11+) or 'toml' package is required")

# Get the directory containing this config.py file
config_dir = Path(__file__).parent

# Try to load config.toml
config_file = config_dir / "config.toml"
if config_file.exists():
    with open(config_file, "rb") as f:
        config_data = tomllib.load(f)
else:
    # Fallback to environment variables if config.toml doesn't exist
    config_data = {}

# Email configuration - handle multiple email accounts
EMAIL_ACCOUNTS = []

# Get email accounts from config
email_configs = config_data.get('email', [])
if isinstance(email_configs, dict):
    # Single email account
    EMAIL_ACCOUNTS = [email_configs]
elif isinstance(email_configs, list):
    # Multiple email accounts
    EMAIL_ACCOUNTS = email_configs
else:
    # Fallback to environment variables if no config
    EMAIL_ACCOUNTS = [{
        'host': os.getenv('EMAIL_HOST'),
        'port': int(os.getenv('EMAIL_PORT', 993)),
        'user': os.getenv('EMAIL_USER'),
        'password': os.getenv('EMAIL_PASSWORD'),
        'mailboxes': os.getenv('EMAIL_MAILBOXES', 'INBOX').split(',') if os.getenv('EMAIL_MAILBOXES') else ['INBOX']
    }]

# For backward compatibility, set individual variables from the first account
if EMAIL_ACCOUNTS:
    EMAIL_HOST = EMAIL_ACCOUNTS[0].get('host') or os.getenv('EMAIL_HOST')
    EMAIL_PORT = int(EMAIL_ACCOUNTS[0].get('port', 993) or os.getenv('EMAIL_PORT', 993))
    EMAIL_USER = EMAIL_ACCOUNTS[0].get('user') or os.getenv('EMAIL_USER')
    EMAIL_PASSWORD = EMAIL_ACCOUNTS[0].get('password') or os.getenv('EMAIL_PASSWORD')
    EMAIL_MAILBOXES = EMAIL_ACCOUNTS[0].get('mailboxes', ['INBOX'])
    if isinstance(EMAIL_MAILBOXES, str):
        EMAIL_MAILBOXES = [EMAIL_MAILBOXES]
else:
    # Fallback to environment variables
    EMAIL_HOST = os.getenv('EMAIL_HOST')
    EMAIL_PORT = int(os.getenv('EMAIL_PORT', 993))
    EMAIL_USER = os.getenv('EMAIL_USER')
    EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD')
    EMAIL_MAILBOXES = os.getenv('EMAIL_MAILBOXES', 'INBOX').split(',') if os.getenv('EMAIL_MAILBOXES') else ['INBOX']

# Weather configuration
WEATHER_CITY = config_data.get('weather', {}).get('city') or os.getenv('WEATHER_CITY')
WEATHER_LAT = config_data.get('weather', {}).get('lat') or os.getenv('WEATHER_LAT')
WEATHER_LONG = config_data.get('weather', {}).get('long') or os.getenv('WEATHER_LONG')
WEATHER_UNITS = config_data.get('weather', {}).get('units', 'metric') or os.getenv('WEATHER_UNITS', 'metric')

# Project configuration
PROJECTS = []

# Get project groups and roots from config
project_groups = config_data.get('project_groups', [])
project_roots = config_data.get('project_roots', [])

# Function to find all project directories
def find_project_directories():
    projects = set()
    
    # Process project groups
    for group_path in project_groups:
        group_path = Path(group_path)
        if group_path.exists() and group_path.is_dir():
            # Walk through the directory tree
            for root, dirs, files in os.walk(group_path):
                # Check if this directory contains a project (has a .git directory or pyproject.toml or setup.py)
                if any((Path(root) / item).exists() for item in ['.git', 'pyproject.toml', 'setup.py']):
                    projects.add(root)
                # Also add directories that contain subdirectories with projects
                for dir_name in dirs:
                    dir_path = Path(root) / dir_name
                    if (dir_path / '.git').exists() or (dir_path / 'pyproject.toml').exists() or (dir_path / 'setup.py').exists():
                        projects.add(str(dir_path))
    
    # Process project roots
    for root_path in project_roots:
        root_path = Path(root_path)
        if root_path.exists() and root_path.is_dir():
            # Check if this root itself is a project
            if (root_path / '.git').exists() or (root_path / 'pyproject.toml').exists() or (root_path / 'setup.py').exists():
                projects.add(str(root_path))
            else:
                # If it's not a project itself, look for projects within it
                for root, dirs, files in os.walk(root_path):
                    if any((Path(root) / item).exists() for item in ['.git', 'pyproject.toml', 'setup.py']):
                        projects.add(root)
    
    return list(projects)

# Populate PROJECTS with discovered directories
PROJECTS = find_project_directories()
