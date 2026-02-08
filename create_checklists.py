#!/usr/bin/env python3
"""
Script to create acceptance checklists for projects that don't have them.
"""

import os
import re
import sys
from pathlib import Path
from datetime import datetime
import argparse

# Add the project root to the path so we can import config
sys.path.insert(0, str(Path(__file__).parent))

from config import dashboard_config

def get_latest_mtime(project_path):
    """Get the most recent modification time for a project directory"""
    # Get the mtime of the folder itself as a starting point
    max_mtime = project_path.stat().st_mtime
    
    # Recursively check all files
    for file in project_path.rglob('*'):
        # Skip hidden files/folders (like .git, .venv, or __pycache__)
        if any(part.startswith('.') for part in file.parts):
            continue
            
        try:
            mtime = file.stat().st_mtime
            if mtime > max_mtime:
                max_mtime = mtime
        except OSError:
            # Handle cases where files might be deleted/locked during scan
            continue
            
    return max_mtime

def get_project_list():
    """Get the list of projects from the dashboard configuration"""
    projects = []
    
    for item in dashboard_config.projects:
        if not item.exists():
            continue
            
        # determine the most recent modification date for the project directory
        last_updated = get_latest_mtime(item)
        projects.append({
            'name': item.name,
            'project_path': item.resolve().absolute(),
            'path': item.resolve().absolute(),
            'last_modified': last_updated
        })
    
    # Sort projects by last modified time (most recent first)
    projects.sort(key=lambda x: x['last_modified'] or 0, reverse=True)
    
    return projects

def create_acceptance_checklist(project_path, last_modified_date):
    """Create an acceptance checklist for a project if it doesn't exist"""
    docs_dir = project_path / "docs"
    checklist_path = docs_dir / "acceptance_checklist.md"
    
    # Create docs directory if it doesn't exist
    docs_dir.mkdir(parents=True, exist_ok=True)
    
    # Check if checklist already exists
    if checklist_path.exists():
        print(f"Checklist already exists for {project_path.name}")
        return False
    
    # Read the example checklist
    example_path = Path(__file__).parent / "docs" / "acceptance_checklist.example.md"
    
    if not example_path.exists():
        print(f"Example checklist not found at {example_path}")
        return False
    
    # Read the example content
    with open(example_path, 'r') as f:
        example_content = f.read()
    
    # Replace the last modified date with the actual date
    # Format: Last modified: YYYY-MM-DD
    formatted_date = last_modified_date.strftime("%Y-%m-%d")
    updated_content = re.sub(r'Last modified: \d{4}-\d{2}-\d{2}', f'Last modified: {formatted_date}', example_content)
    
    # Write the new checklist
    with open(checklist_path, 'w') as f:
        f.write(updated_content)
    
    print(f"Created checklist for {project_path.name}")
    return True

def main(dry_run=True):
    """Main function to process all projects"""
    print("Scanning projects for missing acceptance checklists...")
    
    projects = get_project_list()
    
    if not projects:
        print("No projects found.")
        return
    
    created_count = 0
    
    for project in projects:
        project_path = project['path']
        last_modified_date = datetime.fromtimestamp(project['last_modified'])
        
        try:
            if create_acceptance_checklist(project_path, last_modified_date):
                created_count += 1
        except Exception as e:
            print(f"Error processing {project_path.name}: {e}")
    
    if dry_run:
        print(f"\n(Dry run) Would have created {created_count} checklists.")
    else:
        print(f"\nCreated {created_count} checklists.")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Create acceptance checklists for projects')
    parser.add_argument('--no-dry-run', action='store_true', help='Actually create the files instead of dry run')
    
    args = parser.parse_args()
    
    main(dry_run=not args.no_dry_run)
