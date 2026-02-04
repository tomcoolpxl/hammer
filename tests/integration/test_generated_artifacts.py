"""Integration tests for validating generated artifact syntax."""

import ast
import subprocess
import tempfile
import pytest
from pathlib import Path

from hammer.spec import load_spec_from_file
from hammer.builder import build_assignment


PROJECT_ROOT = Path(__file__).parents[2]
REAL_EXAMPLES_DIR = PROJECT_ROOT / "real_examples"


def ruby_available():
    """Check if Ruby is available for Vagrantfile syntax checking."""
    try:
        result = subprocess.run(
            ["ruby", "--version"],
            capture_output=True,
            timeout=5,
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


@pytest.fixture
def pe1_artifacts():
    """Build PE1 and return paths to generated artifacts."""
    spec_path = REAL_EXAMPLES_DIR / "PE1" / "spec.yaml"
    spec = load_spec_from_file(spec_path)

    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir)
        build_assignment(
            spec=spec,
            output_dir=output_dir,
            spec_dir=spec_path.parent,
        )

        yield {
            "student_vagrantfile": output_dir / "student_bundle" / "Vagrantfile",
            "grading_vagrantfile": output_dir / "grading_bundle" / "Vagrantfile",
            "tests_dir": output_dir / "grading_bundle" / "tests",
            "conftest": output_dir / "grading_bundle" / "tests" / "conftest.py",
        }


class TestVagrantfileSyntax:
    """Test that generated Vagrantfiles have valid Ruby syntax."""

    @pytest.mark.skipif(not ruby_available(), reason="Ruby not available")
    def test_student_vagrantfile_valid_ruby(self, pe1_artifacts):
        """Student Vagrantfile should pass Ruby syntax check."""
        vagrantfile = pe1_artifacts["student_vagrantfile"]
        result = subprocess.run(
            ["ruby", "-c", str(vagrantfile)],
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert result.returncode == 0, f"Ruby syntax error: {result.stderr}"

    @pytest.mark.skipif(not ruby_available(), reason="Ruby not available")
    def test_grading_vagrantfile_valid_ruby(self, pe1_artifacts):
        """Grading Vagrantfile should pass Ruby syntax check."""
        vagrantfile = pe1_artifacts["grading_vagrantfile"]
        result = subprocess.run(
            ["ruby", "-c", str(vagrantfile)],
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert result.returncode == 0, f"Ruby syntax error: {result.stderr}"

    def test_vagrantfile_has_configure_block(self, pe1_artifacts):
        """Vagrantfile should contain Vagrant.configure block."""
        vagrantfile = pe1_artifacts["student_vagrantfile"]
        content = vagrantfile.read_text()
        assert "Vagrant.configure" in content
        assert "config.vm.define" in content

    def test_vagrantfile_has_provider_config(self, pe1_artifacts):
        """Vagrantfile should contain libvirt provider configuration."""
        vagrantfile = pe1_artifacts["student_vagrantfile"]
        content = vagrantfile.read_text()
        assert "libvirt" in content


class TestPytestFileSyntax:
    """Test that generated pytest files have valid Python syntax."""

    def test_conftest_valid_python(self, pe1_artifacts):
        """conftest.py should be valid Python."""
        conftest = pe1_artifacts["conftest"]
        content = conftest.read_text()

        # Should parse without errors
        try:
            ast.parse(content)
        except SyntaxError as e:
            pytest.fail(f"conftest.py syntax error: {e}")

    def test_conftest_has_fixtures(self, pe1_artifacts):
        """conftest.py should define testinfra host fixtures."""
        conftest = pe1_artifacts["conftest"]
        content = conftest.read_text()

        # Should have pytest fixture decorator
        assert "@pytest.fixture" in content
        # Should have testinfra host setup
        assert "testinfra" in content or "host" in content

    def test_all_test_files_valid_python(self, pe1_artifacts):
        """All generated test files should be valid Python."""
        tests_dir = pe1_artifacts["tests_dir"]

        # Tests are in phase subdirectories (baseline/, mutation/, idempotence/)
        test_files = list(tests_dir.glob("*/test_*.py"))
        assert len(test_files) >= 1, "No test files found"

        for test_file in test_files:
            content = test_file.read_text()
            try:
                ast.parse(content)
            except SyntaxError as e:
                pytest.fail(f"{test_file.name} syntax error: {e}")

    def test_test_files_have_test_functions(self, pe1_artifacts):
        """Generated test files should contain test functions."""
        tests_dir = pe1_artifacts["tests_dir"]

        for test_file in tests_dir.glob("*/test_*.py"):
            content = test_file.read_text()
            tree = ast.parse(content)

            # Find test functions or test classes
            test_items = []
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
                    test_items.append(node.name)
                elif isinstance(node, ast.ClassDef) and node.name.startswith("Test"):
                    test_items.append(node.name)

            assert len(test_items) >= 1, f"{test_file.name} has no test functions/classes"

    def test_test_files_import_pytest(self, pe1_artifacts):
        """Generated test files should import pytest."""
        tests_dir = pe1_artifacts["tests_dir"]

        for test_file in tests_dir.glob("*/test_*.py"):
            content = test_file.read_text()
            # Should import pytest (directly or via testinfra)
            assert "import pytest" in content or "pytest" in content


class TestGeneratedArtifactsForAllPEs:
    """Test generated artifacts for all PE specs."""

    @pytest.mark.parametrize("pe_name", ["PE1", "PE2", "PE3", "PE4"])
    def test_vagrantfile_syntax(self, pe_name):
        """Each PE should generate syntactically valid Vagrantfile."""
        spec_path = REAL_EXAMPLES_DIR / pe_name / "spec.yaml"
        if not spec_path.exists():
            pytest.skip(f"{pe_name} spec not found")

        spec = load_spec_from_file(spec_path)

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            build_assignment(
                spec=spec,
                output_dir=output_dir,
                spec_dir=spec_path.parent,
            )

            vagrantfile = output_dir / "student_bundle" / "Vagrantfile"
            content = vagrantfile.read_text()

            # Basic structure checks
            assert "Vagrant.configure" in content
            assert "config.vm.define" in content

            # If Ruby available, do syntax check
            if ruby_available():
                result = subprocess.run(
                    ["ruby", "-c", str(vagrantfile)],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                assert result.returncode == 0, f"{pe_name} Vagrantfile: {result.stderr}"

    @pytest.mark.parametrize("pe_name", ["PE1", "PE2", "PE3", "PE4"])
    def test_test_files_syntax(self, pe_name):
        """Each PE should generate syntactically valid test files."""
        spec_path = REAL_EXAMPLES_DIR / pe_name / "spec.yaml"
        if not spec_path.exists():
            pytest.skip(f"{pe_name} spec not found")

        spec = load_spec_from_file(spec_path)

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            build_assignment(
                spec=spec,
                output_dir=output_dir,
                spec_dir=spec_path.parent,
            )

            tests_dir = output_dir / "grading_bundle" / "tests"

            for test_file in tests_dir.glob("*.py"):
                content = test_file.read_text()
                try:
                    ast.parse(content)
                except SyntaxError as e:
                    pytest.fail(f"{pe_name}/{test_file.name}: {e}")
