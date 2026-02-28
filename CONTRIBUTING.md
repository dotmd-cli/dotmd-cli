# Contributing to dotmd

Thank you for your interest in contributing! This document covers how to set up a development environment, run tests, and submit pull requests.

---

## Development Setup

**Requirements:** Python 3.9+, pip

```bash
# Clone the repo
git clone https://github.com/dotmd/dotmd-cli.git
cd dotmd-cli

# Create a virtual environment
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# Install in editable mode with dev dependencies
pip install -e ".[dev]"
```

---

## Running Tests

```bash
pytest
```

Tests live in `tests/`. The suite uses `pytest` with `unittest.mock` — no network calls are made.

To run a specific test file:

```bash
pytest tests/test_cli.py -v
```

---

## Project Structure

```
dotmd/
├── __init__.py     # Package version
├── api.py          # Supabase REST client (all network I/O)
├── art.py          # ASCII art banner (pyfiglet + rich)
├── cli.py          # Typer CLI commands
├── formats.py      # Format → output path mapping
└── mascot.png      # Bundled brand asset

tests/
├── test_api.py     # API client unit tests
└── test_cli.py     # CLI integration tests (mocked)
```

---

## Code Style

- Follow PEP 8.
- Use type annotations on all public functions.
- Keep functions small and focused.
- No external dependencies beyond what's in `pyproject.toml`.

---

## Submitting a Pull Request

1. Fork the repository and create a branch: `git checkout -b my-feature`
2. Make your changes and add tests.
3. Ensure all tests pass: `pytest`
4. Push your branch and open a pull request against `main`.
5. Describe what your PR does and why.

---

## Releasing (maintainers only)

1. Bump the version in `pyproject.toml` and `dotmd/__init__.py`.
2. Commit: `git commit -am "chore: bump version to X.Y.Z"`
3. Tag: `git tag vX.Y.Z`
4. Push: `git push origin main --tags`

The `publish.yml` GitHub Actions workflow will automatically build and publish to PyPI when a `v*` tag is pushed.

**PyPI trusted publishing** is used — no API tokens needed. The `pypi` environment must be configured in the GitHub repository settings with the trusted publisher set to this repo.