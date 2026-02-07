# Personal Dashboard

A Python-based personal dashboard that generates an HTML file every hour with:
- Email notifications (multiple mailboxes)
- Weather information
- Project progress tracking
- Current date and time

## Features

- **Email Integration**: Shows unread email counts from multiple mailboxes
- **Weather Data**: Current weather information from OpenWeatherMap
- **Project Tracking**: Progress indicators for your projects
- **Responsive Design**: Works well on different screen sizes
- **Automated Updates**: Can be scheduled to run hourly

## Setup

1. Clone the repository
2. Install dependencies using uv:
   ```
   uv pip install -e .
   ```
3. Create a `.env` file based on `.env.example`:
   ```
   cp .env.example .env
   ```
4. Fill in your email and weather API credentials
5. Run the dashboard generator:
   ```
   python generate_dashboard.py
   ```

## Usage

The dashboard will generate a `dashboard.html` file that you can set as your browser's new tab page.

## Scheduling

To run this hourly, add to your crontab:
