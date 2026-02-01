# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| 1.0.x   | ✅ Yes    |
| < 1.0   | ❌ No     |

## Reporting a Vulnerability

If you discover a security vulnerability in Git Dungeon, please report it by:

1. **Do not** open a public issue
2. Email the maintainer at: [security email]
3. Or use GitHub's private vulnerability reporting

When reporting, please include:
- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if any)

## Security Best Practices

- Git Dungeon only reads Git repository data
- No data is sent to external servers (except when you explicitly use GitHub remote repos)
- All game data is stored locally
- Review code before running in production environments

## Dependencies

This project uses the following dependencies. Please ensure they are kept up to date:
- GitPython
- Pydantic
- Rich
- Typer
- Textual (optional)
- lupa (optional, for Lua plugins)
