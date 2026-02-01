# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.0] - 2026-02-01

### Added
- **Chinese Language Support** - Full i18n with ` --lang zh_CN` option
- **i18n Test Suite** - 6 tests for translation validation
- **CLI Argument Tests** - 3 tests for argument validation
- **Auto-battle Mode** - `--auto` flag for automatic combat demonstration

### Changed
- Updated README with Chinese documentation
- Enhanced CLI help with language options
- Improved game text consistency

### Fixed
- GitHub shallow clone issue (removed `--depth 1`)
- Gold sync issue between player and inventory
- Multiple test file organization

### Technical
- Added `src/git_dungeon/i18n/` module
- Created comprehensive translation dictionary
- Fixed PyInstaller spec file for proper packaging

## [1.0.0] - 2026-02-01

### Added
- Initial release of Git Dungeon
- CLI interface with Rich output
- Git repository parsing and commit analysis
- Chapter-based gameplay progression
- Combat system with enemies from commits
- Character stats and leveling system
- Inventory and equipment system
- Save/load functionality
- JSON logging support
- Seed-based reproducibility
- TUI interface (Textual-based, optional)
- Plugin system support (Lua)

### Changed
- Refactored to proper Python package structure (`src/git_dungeon/`)
- Updated all imports to use `git_dungeon` namespace

### Technical
- Python 3.10+ support
- PyInstaller support for standalone binaries
- PyPI package distribution
- GitHub Actions CI/CD

## [0.0.0] - 2025-01-01

### Added
- Initial prototype
