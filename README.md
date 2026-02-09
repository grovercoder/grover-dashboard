# Personal Dashboard

A Python-based personal dashboard that generates an HTML file every hour with:
- Email notifications (multiple mailboxes)
- Weather information
- Project progress tracking
- Current date and time

## Screenshot
<img src="docs/img/screenshot.png" width="600" alt="Project Screenshot">

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
6. Add a cron job to periodically call this process (usually via `crontab -e`).
   ```
   # to update every 30 minutes
   */30 * * * * cd /home/USERNAME/path/grover-dashboard/run.sh
   ```
## Usage

The dashboard will generate a `dashboard.html` file in the `dist` folder that you can set as your browser's new tab page.

## Background

I create "research" projects on a regular basis to learn or explore various coding concepts, or even just to see if a project might be feasible.  This adds up over time and I wanted a better way to track those random projects.  I also wanted a way to have an "at-a-glance" page to show me the status of various things I might be interested in.  To start with I'm focusing on the current weather in my area and how many unread emails I have (without having to switch to my mail client).  This project provides a tool that does all of that for me.  

Eventually I'd like to expand this to include tracking my finances, appointments, and more.

## Projects

A project is just a working directory for something.  This could be a python application, a book, a graphic or video project, or whatever else you want.

Projects are specified in the `config.toml` file.  "project_roots" are a list of specific project directories you wish to track.  "project_groups" are directories that contain project directories.  If all your projects are in a `/home/USERNAME/coding/research` folder, then you only need that one group entry.  Practical use might also include specific directories in "project_roots" if you have projects outside your grouping folder.  For example `/home/USERNAME/Tools/grover-dashboard`.

### Project Progress

Progress is determined in one of two ways:

2. a `docs/acceptance_checklist.md` file exits.  The "checked" items are used to calculate the progress. (See [docs/acceptance_checklist.example.md](docs/acceptance_checklist.example.md))
1. a `tests/acceptance.py` unit testing file exists in the project directory.  This unit test file indicates what tests must pass to consider the project completed.  (Only applies to Python projects with unit testing)
3. If neither option is found "Unknown" is returned.  Any project marked Unknown is an indicator that project should be updated or pruned.

### Project Status

A project's status is determined by the "age" of the project's last modified date.

|Status|Notes|
|---|---|
|Active|updated less than a month ago|
|Dormant|updated between one month and six months ago|
|Stale|updated between six months and 1 year ago|
|Abandoned|updated over a year ago|

The date used is as follows:

- The most recent git commit date, if git is available
- The most recent file modified date for the project files (ignoring the acceptance_checklist.md file due to possible bulk update scenarios)
- The "Last modified:" value from the acceptance_checklist.md file for the project, if available
- The maximum date value from these items is used

This calculated project last modified value is used for sorting the projects as well, from most recently changed to oldest changed.

## Acceptance Checklists

To add the acceptance checklist file to all of your projects at once, run:

```
# change into this project's working directory
cd grover-dashboard

# add the checklist file to all projects
uv run create_checklists.py --all

# add the checklist file to a single project
uv run create_checklists.py /path/to/project
```

The `docs/acceptance_checklist.example.md` file is used as a template.


