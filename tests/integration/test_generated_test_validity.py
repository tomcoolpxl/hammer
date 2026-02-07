"""Validate that generated test files are syntactically correct Python.

For each PE spec, build the grading bundle and compile() every generated .py file.
"""

from pathlib import Path

import pytest

from hammer.spec import load_spec_from_file
from hammer.builder import build_assignment

PROJECT_ROOT = Path(__file__).parent.parent.parent
REAL_EXAMPLES = PROJECT_ROOT / "real_examples"

PE_SPECS = [
    ("PE1", REAL_EXAMPLES / "PE1" / "spec.yaml"),
    ("PE2", REAL_EXAMPLES / "PE2" / "spec.yaml"),
    ("PE3", REAL_EXAMPLES / "PE3" / "spec.yaml"),
    ("PE4", REAL_EXAMPLES / "PE4" / "spec.yaml"),
]


@pytest.mark.parametrize("pe_name,spec_path", PE_SPECS,
                         ids=[p[0] for p in PE_SPECS])
def test_generated_tests_are_valid_python(pe_name, spec_path, tmp_path):
    """All generated .py test files must be syntactically valid."""
    if not spec_path.exists():
        pytest.skip(f"{spec_path} not found")

    spec = load_spec_from_file(spec_path)
    out_dir = tmp_path / pe_name
    build_assignment(spec=spec, output_dir=out_dir, spec_dir=spec_path.parent)

    tests_dir = out_dir / "grading_bundle" / "tests"
    assert tests_dir.exists(), f"Tests dir not generated for {pe_name}"

    py_files = list(tests_dir.rglob("*.py"))
    assert len(py_files) > 0, f"No .py files generated for {pe_name}"

    errors = []
    for py_file in py_files:
        source = py_file.read_text()
        try:
            compile(source, str(py_file), "exec")
        except SyntaxError as e:
            errors.append(f"{py_file.relative_to(out_dir)}: {e}")

    assert not errors, f"Syntax errors in generated tests:\n" + "\n".join(errors)
