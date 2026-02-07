"""Shared fixtures for HAMMER test suite."""

from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).parent.parent
FIXTURES_DIR = Path(__file__).parent / "fixtures"
REAL_EXAMPLES_DIR = PROJECT_ROOT / "real_examples"


@pytest.fixture(scope="session")
def project_root():
    """Return the project root directory."""
    return PROJECT_ROOT


@pytest.fixture(scope="session")
def fixtures_dir():
    """Return the test fixtures directory."""
    return FIXTURES_DIR


@pytest.fixture(scope="session")
def real_examples_dir():
    """Return the real_examples directory."""
    return REAL_EXAMPLES_DIR


@pytest.fixture(scope="session")
def pe1_spec():
    """Load and return the PE1 spec."""
    from hammer.spec import load_spec_from_file
    return load_spec_from_file(REAL_EXAMPLES_DIR / "PE1" / "spec.yaml")


@pytest.fixture(scope="session")
def pe3_spec():
    """Load and return the PE3 spec."""
    from hammer.spec import load_spec_from_file
    return load_spec_from_file(REAL_EXAMPLES_DIR / "PE3" / "spec.yaml")


@pytest.fixture(scope="session")
def pe4_spec():
    """Load and return the PE4 spec."""
    from hammer.spec import load_spec_from_file
    return load_spec_from_file(REAL_EXAMPLES_DIR / "PE4" / "spec.yaml")
