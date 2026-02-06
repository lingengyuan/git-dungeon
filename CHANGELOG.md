# Changelog

All notable changes to this project are documented in this file.

This project follows:

- [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)
- [Semantic Versioning](https://semver.org/spec/v2.0.0.html)

## [1.2.0] - 2026-02-06

### Added

- CI package smoke job (`wheel + clean venv`) in `.github/workflows/ci.yml`.
- Reusable smoke script: `scripts/ci_smoke_demo.sh`.
- Release workflow gates: lint, `pytest -m "not slow"`, wheel build, wheel install smoke.
- `docs/FAQ.md` with save path, reproducibility, AI, and performance guidance.
- Local release validation commands: `make build-wheel`, `make smoke-install`.

### Changed

- Updated README and README.zh-CN with 3-step Quickstart and release-friendly install flow.
- Standardized release pipeline around wheel artifacts.
- Aligned package version metadata for shipping.

### Fixed

- Release process no longer depends on direct PyPI publish during every release trigger.
- Documented save directory override (`GIT_DUNGEON_SAVE_DIR`) for CI-safe runs.

## [1.1.0] - 2026-02-01

### Added

- Chinese language support (`--lang zh_CN`, `--lang zh`).
- Auto-battle mode (`--auto`).
- CLI argument tests and i18n test coverage.

### Fixed

- GitHub clone depth handling.
- Gold synchronization and test organization issues.

## [1.0.0] - 2026-02-01

### Added

- Initial public release with chapter progression, combat, rewards, save/load, and CLI flow.
