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
    
    # Create the full configuration model
    dashboard_config = DashboardConfig(**config_data)
    
    # Extract individual components for backward compatibility
    EMAIL_ACCOUNTS = dashboard_config.email
    WEATHER_CONFIG = dashboard_config.weather
    PROJECTS = dashboard_config.projects
    
    # For backward compatibility, set individual variables from the first account
    if EMAIL_ACCOUNTS:
        EMAIL_HOST = EMAIL_ACCOUNTS[0].server
        EMAIL_PORT = EMAIL_ACCOUNTS[0].port
        EMAIL_USER = EMAIL_ACCOUNTS[0].user
        EMAIL_PASSWORD = EMAIL_ACCOUNTS[0].password
        EMAIL_MAILBOXES = ["INBOX"]  # Default mailbox, can be extended if needed
    else:
        # Fallback to environment variables
        EMAIL_HOST = os.getenv('EMAIL_HOST')
        EMAIL_PORT = int(os.getenv('EMAIL_PORT', 993))
        EMAIL_USER = os.getenv('EMAIL_USER')
        EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD')
        EMAIL_MAILBOXES = os.getenv('EMAIL_MAILBOXES', 'INBOX').split(',') if os.getenv('EMAIL_MAILBOXES') else ['INBOX']
        
    # Set weather variables
    WEATHER_CITY = WEATHER_CONFIG.city
    WEATHER_LAT = WEATHER_CONFIG.lat
    WEATHER_LONG = WEATHER_CONFIG.long
    WEATHER_UNITS = WEATHER_CONFIG.units
    
except Exception as e:
    print(f"Error creating configuration model: {e}")
    # Fallback to environment variables if model creation fails
    EMAIL_HOST = os.getenv('EMAIL_HOST')
    EMAIL_PORT = int(os.getenv('EMAIL_PORT', 993))
    EMAIL_USER = os.getenv('EMAIL_USER')
    EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD')
    EMAIL_MAILBOXES = os.getenv('EMAIL_MAILBOXES', 'INBOX').split(',') if os.getenv('EMAIL_MAILBOXES') else ['INBOX']
    
    WEATHER_CITY = os.getenv('WEATHER_CITY')
    WEATHER_LAT = os.getenv('WEATHER_LAT')
    WEATHER_LONG = os.getenv('WEATHER_LONG')
    WEATHER_UNITS = os.getenv('WEATHER_UNITS', 'metric')
    
    # Initialize empty project list
    PROJECTS = []
