#!/bin/bash

# Git Dungeon Test Script

cd "$(dirname "$0")/.."

echo "Running Git Dungeon tests..."

# Activate virtual environment if exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Run pytest
python -m pytest tests/ -v --tb=short "$@"

echo ""
echo "Test run complete!"
