import os
import json
import imaplib
import email
from datetime import datetime
import requests
from jinja2 import Environment, FileSystemLoader
from config import EMAIL_HOST, EMAIL_PORT, EMAIL_USER, EMAIL_PASSWORD, EMAIL_MAILBOXES, WEATHER_API_KEY, WEATHER_CITY, WEATHER_UNITS, PROJECTS

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
    """Fetch weather data from OpenWeatherMap API"""
    try:
        url = f"http://api.openweathermap.org/data/2.5/weather"
        params = {
            'q': WEATHER_CITY,
            'appid': WEATHER_API_KEY,
            'units': WEATHER_UNITS
        }
        
        response = requests.get(url, params=params)
        data = response.json()
        
        return {
            'city': data['name'],
            'temperature': round(data['main']['temp']),
            'description': data['weather'][0]['description'].title(),
            'humidity': data['main']['humidity'],
            'wind_speed': data['wind']['speed']
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

def generate_dashboard():
    """Generate the HTML dashboard"""
    
    # Get data
    email_counts = get_email_counts()
    weather_data = get_weather()
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Prepare data for template
    template_data = {
        'email_counts': email_counts,
        'weather': weather_data,
        'projects': PROJECTS,
        'current_time': current_time,
        'date': datetime.now().strftime("%A, %B %d, %Y")
    }
    
    # Set up Jinja2 environment
    env = Environment(loader=FileSystemLoader('templates'))
    template = env.get_template('dashboard.html')
    
    # Render template
    html_output = template.render(template_data)
    
    # Write to file
    with open('dashboard.html', 'w') as f:
        f.write(html_output)
    
    print("Dashboard generated successfully!")

if __name__ == '__main__':
    generate_dashboard()
