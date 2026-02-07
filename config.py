import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Email configuration
EMAIL_HOST = os.getenv('EMAIL_HOST')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', 993))
EMAIL_USER = os.getenv('EMAIL_USER')
EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD')
EMAIL_MAILBOXES = os.getenv('EMAIL_MAILBOXES', 'INBOX').split(',')

# Weather configuration
WEATHER_API_KEY = os.getenv('WEATHER_API_KEY')
WEATHER_CITY = os.getenv('WEATHER_CITY', 'London')
WEATHER_UNITS = os.getenv('WEATHER_UNITS', 'metric')

# Project configuration - will be populated dynamically
PROJECTS = []
