# Contributing to Git Dungeon

Thank you for your interest in contributing! This document outlines the process for contributing to the project.

## Getting Started

### Prerequisites
- Python 3.10+
- Git
- A Git repository to test with

### Development Setup

1. Fork the repository on GitHub

2. Clone your fork:
```bash
git clone https://github.com/YOUR-USERNAME/git-dungeon.git
cd git-dungeon
```

3. Set up development environment:
```bash
python -m venv .venv
source .venv/bin/activate  # or `.venv\Scripts\activate` on Windows
pip install -e ".[tui,mods]"
pip install pytest ruff mypy
```

4. Run tests:
```bash
pytest -q
```

5. Run linters:
```bash
ruff check src/ tests/
mypy src/ --ignore-missing-imports
```

## Project Structure

```
git-dungeon/
├── src/git_dungeon/
│   ├── main.py           # CLI entry point
│   ├── main_cli.py       # CLI game logic
│   ├── main_tui.py       # TUI interface (Textual)
│   ├── engine/           # Game rules and systems
│   ├── core/             # Core components (combat, character, etc.)
│   ├── config/           # Configuration
│   └── utils/            # Utilities
├── tests/                # Test suite
└── pyproject.toml        # Project configuration
```

## Coding Standards

- Follow PEP 8 style guide
- Use type hints for all public functions
- Write docstrings for new functions
- Add tests for new features
- Run linters before submitting PR

## Submitting Changes

1. Create a feature branch:
```bash
git checkout -b feature/your-feature-name
```

2. Make your changes

3. Run tests and linters:
```bash
pytest -q
ruff check src/ tests/
mypy src/
```

4. Commit your changes:
```bash
git add .
git commit -m "feat: description of your changes"
```

5. Push to your fork and create a PR

## Commit Message Format

We follow [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` New features
- `fix:` Bug fixes
- `docs:` Documentation changes
- `refactor:` Code refactoring
- `test:` Adding tests
- `chore:` Maintenance tasks

## Reporting Issues

When reporting issues, please include:
- A clear description of the problem
- Steps to reproduce
- Expected vs actual behavior
- Python version and OS
