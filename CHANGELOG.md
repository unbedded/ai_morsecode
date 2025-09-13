# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html)
with [PEP 440](https://peps.python.org/pep-0440/) Python-specific versioning.

## [Unreleased]

### Added
- Initial template setup for Python Claude Code development
- GitFlow workflow integration with branch naming conventions
- PEP 440 compliant version management system
- Claude Code slash commands for development automation
- Comprehensive code quality pipeline (ruff, mypy, pytest)
- Pre-commit hooks for automated code formatting and checking
- VS Code configuration for consistent development environment
- GitHub Actions CI/CD pipeline
- Module scaffolding tools following CLAUDE.md standards

### Changed
- Nothing yet

### Deprecated
- Nothing yet

### Removed
- Nothing yet

### Fixed
- Nothing yet

### Security
- Nothing yet

## [0.1.0] - 2025-09-08

### Added
- Initial release of Python Claude Code Development Template
- Basic project structure with placeholder configurations
- CLAUDE.md coding standards and configuration management patterns
- Template files for rapid project bootstrapping

---

## Version Format

This project uses PEP 440 compliant versioning:

- **Major.Minor.Patch** (e.g., `1.0.0`) - Stable releases
- **Major.Minor.PatchaN** (e.g., `1.0.0a1`) - Alpha pre-releases
- **Major.Minor.PatchbN** (e.g., `1.0.0b1`) - Beta pre-releases  
- **Major.Minor.PatchrcN** (e.g., `1.0.0rc1`) - Release candidates

### Release Guidelines

- **Major**: Breaking changes, API incompatibility
- **Minor**: New features, backwards compatible
- **Patch**: Bug fixes, small improvements
- **Pre-release**: Development versions, testing builds

Use `.claude/tools/version_bump.py` or `/version-bump` slash command to manage versions automatically.