#!/bin/bash

# Git Dungeon Lint Script

cd "$(dirname "$0")/.."

echo "Running code quality checks..."

# Activate virtual environment if exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Run formatters in check mode
echo "Checking code format..."
python -m black --check src/
python -m isort --check-only src/
python -m flake8 src/

# Run type checker
echo "Checking types..."
python -m mypy src/

echo ""
echo "Lint complete!"
