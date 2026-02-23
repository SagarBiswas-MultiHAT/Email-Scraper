# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-02-23

### Added

- Modular `src/email_harvester` package architecture.
- Installable CLI entrypoint `email-harvester`.
- Deterministic pytest suite with coverage gate.
- Ruff, mypy, pre-commit, Docker, Makefile, and CI workflow.
- Governance and security docs (`LICENSE`, `SECURITY.md`, `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`).

### Changed

- Replaced monolithic script internals with package modules.
- Preserved backward compatibility via wrapper `email_harvester_ultimate.py`.
- Rewrote README for complete onboarding, usage, and maintenance guidance.

### Removed

- Tracked generated output CSV from repository source control.

