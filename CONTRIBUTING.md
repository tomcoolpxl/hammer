# Contributing to HAMMER

## Development Setup

```bash
git clone <repo-url>
cd hammer
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Running Tests

```bash
# Unit + Integration tests (fast, no VMs needed)
.venv/bin/python -m pytest tests/unit/ tests/integration/ -v

# E2E tests (requires Vagrant + libvirt)
.venv/bin/python -m pytest tests/e2e/ -v -s -m e2e

# Run specific test file
.venv/bin/python -m pytest tests/unit/test_security.py -v
```

## Project Structure

```
src/hammer/
    spec/           # Pydantic models (split into submodules)
    plan.py         # Execution plan builder
    builder/        # Artifact generation (Vagrantfile, inventory, tests)
    testgen/        # Pytest/Testinfra test generation
    runner/         # Grading pipeline (converge, verify, report)
    cli.py          # CLI entry point
    validators.py   # Input validation types
    utils.py        # Shared utilities
    constants.py    # Shared constants
    exceptions.py   # Exception hierarchy
    prerequisites.py # External tool checks
```

## Coding Standards

- Python 3.10+, type hints on public functions
- Pydantic v2 for all data models
- Tests required for new functionality
- Use `SafeIdentifier`, `SafePath`, etc. from `validators.py` for user inputs
- Use constants from `constants.py` for phase names

## Making Changes

1. Create a feature branch from `main`
2. Write tests first (or alongside)
3. Run `pytest tests/unit/ tests/integration/` before committing
4. Keep commits focused and well-described

## Test Categories

| Category | Directory | What it tests |
|----------|-----------|---------------|
| Unit | `tests/unit/` | Individual functions and classes |
| Integration | `tests/integration/` | Build artifacts, spec loading |
| E2E | `tests/e2e/` | Full grading with Vagrant VMs |
| Security | `tests/unit/test_security.py` | Input validation, injection |
