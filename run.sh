#!/bin/bash

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Use python from the .venv directory directly
PYTHON_EXEC="$SCRIPT_DIR/.venv/bin/python"

# Run the generate_dashboard script
"$PYTHON_EXEC" "$SCRIPT_DIR/generate_dashboard.py"
