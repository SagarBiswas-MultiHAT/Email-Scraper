# Contributing

Thanks for contributing to Email-Scraper.

## Development Setup

1. Create and activate a virtual environment.
2. Install dependencies:
   ```bash
   python -m pip install -e .[dev]
   ```

## Local Quality Checks

Run these before opening a pull request:

```bash
python -m ruff check src tests
python -m ruff format --check src tests
python -m pytest
python -m mypy src/email_harvester
```

## Pull Request Guidelines

- Keep PRs focused and small.
- Add or update tests for behavior changes.
- Update documentation for any CLI or interface changes.
- Include a short risk summary in the PR description.

## Commit Style

Use clear, imperative commit messages. Example:

- `Refactor pipeline into modular package`
- `Add deterministic tests for fallback search flow`

