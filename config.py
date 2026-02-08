import os
import sys
from pathlib import Path
from pydantic import BaseModel
from typing import List, Optional

# Try to import tomllib (Python 3.11+) or toml (older versions)
try:
    import tomllib
except ImportError:
    try:
        import toml as tomllib
    except ImportError:
        raise ImportError("Either 'tomllib' (Python 3.11+) or 'toml' package is required")

# Import the models
from models import EmailAccount, WeatherConfig, DashboardConfig

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

# Create the DashboardConfig model from the loaded data
try:
    # Handle the case where email might be a single dict or a list
    if 'email' in config_data:
        email_data = config_data['email']
        if isinstance(email_data, dict):
            # Convert single email to list
            config_data['email'] = [email_data]

    # weather configuration
    print('getting weather config')
    weather_config = WeatherConfig(**config_data['weather'])
    
    # email accounts
    print('getting email config')
    accounts = []
    for acct in config_data["email"]:
        accounts.append(EmailAccount(**acct))

    # project listings
    print('getting projects config')
    config_projects = config_data['projects']
    project_paths = set()

    # Keep track of project group paths to exclude them later
    project_group_paths = set()
    
    for p in config_projects['project_roots']:
        current = Path(p).resolve()
        if current.exists() and current.is_dir():
            project_paths.add(current)

    for p in config_projects['project_groups']:
        current = Path(p)
        if current.exists() and current.is_dir():
            project_group_paths.add(current.resolve())
            for c in current.iterdir():
                if c.is_dir() and not c.name.startswith('.'):
                    project_paths.add(c.resolve())
    
    # Remove project group directories from the final project list
    # This ensures that directories that are project groups themselves are not included
    final_project_paths = set()
    for project_path in project_paths:
        # Check if this path is a project group directory
        is_project_group = False
        for group_path in project_group_paths:
            if project_path == group_path:
                is_project_group = True
                break
        
        if not is_project_group:
            final_project_paths.add(project_path)
    
    project_list = list(final_project_paths)

    # Create the full configuration model
    dashboard_config = DashboardConfig(
        weather = weather_config,
        email = accounts,
        projects = project_list
    )
    
    # Extract individual components
    EMAIL_ACCOUNTS = dashboard_config.email
    WEATHER_CONFIG = dashboard_config.weather
    PROJECTS = dashboard_config.projects
    
except Exception as e:
    print(f"Error creating configuration model: {e}")
    # Fallback to environment variables if model creation fails
    EMAIL_ACCOUNTS = []
    WEATHER_CONFIG = WeatherConfig(city="", lat=0.0, long=0.0, units="metric")
    PROJECTS = []
