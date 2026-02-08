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
from generate_dashboard import get_latest_mtime

def get_project_list():
    """Get the list of projects from the dashboard configuration"""
    projects = []
    
    # Process research projects
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
    
    # Check if checklist already exists
    if checklist_path.exists():
        print(f"Checklist already exists for {project_path.name}")
        return False

    # Create docs directory if it doesn't exist
    docs_dir.mkdir(parents=True, exist_ok=True)
    
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

def main(project_path=None, process_all=False):
    """Main function to process projects"""
    if project_path:
        # Process a specific project
        project_path = Path(project_path).resolve()
        if not project_path.exists():
            print(f"Project path does not exist: {project_path}")
            return
        
        # Get the last modified time for this specific project
        last_modified_date = datetime.fromtimestamp(get_latest_mtime(project_path))
        
        try:
            if create_acceptance_checklist(project_path, last_modified_date):
                print(f"Created checklist for {project_path.name}")
            else:
                print(f"No checklist created for {project_path.name}")
        except Exception as e:
            print(f"Error processing {project_path.name}: {e}")
    elif process_all:
        # Process all projects
        print("Scanning all projects for missing acceptance checklists...")
        
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
        
        print(f"\nCreated {created_count} checklists.")
    else:
        # Default behavior: process the current directory
        current_dir = Path('.').resolve()
        print(f"Processing current directory: {current_dir}")
        
        # Get the last modified time for current directory
        last_modified_date = datetime.fromtimestamp(get_latest_mtime(current_dir))
        
        try:
            if create_acceptance_checklist(current_dir, last_modified_date):
                print(f"Created checklist for {current_dir.name}")
            else:
                print(f"No checklist created for {current_dir.name}")
        except Exception as e:
            print(f"Error processing {current_dir.name}: {e}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Create acceptance checklists for projects')
    parser.add_argument('project_path', nargs='?', help='Specific project path to process (default: current directory)')
    parser.add_argument('--all', action='store_true', help='Process all projects')
    
    args = parser.parse_args()
    
    main(project_path=args.project_path, process_all=args.all)
