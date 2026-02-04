"""Integration tests for hammer build output structure."""

import pytest
import tempfile
import shutil
from pathlib import Path

from hammer.spec import load_spec_from_file
from hammer.builder import build_assignment


PROJECT_ROOT = Path(__file__).parents[2]
REAL_EXAMPLES_DIR = PROJECT_ROOT / "real_examples"


@pytest.fixture(scope="module")
def pe1_build():
    """Build PE1 and return the output directory."""
    spec_path = REAL_EXAMPLES_DIR / "PE1" / "spec.yaml"
    spec = load_spec_from_file(spec_path)

    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir)
        lock = build_assignment(
            spec=spec,
            output_dir=output_dir,
            spec_dir=spec_path.parent,
        )
        yield {
            "output_dir": output_dir,
            "lock": lock,
            "spec": spec,
            # Copy files for inspection after tmpdir cleanup
            "student_files": list((output_dir / "student_bundle").rglob("*")),
            "grading_files": list((output_dir / "grading_bundle").rglob("*")),
        }


@pytest.fixture
def build_output():
    """Create a fresh build for each test that needs it."""
    spec_path = REAL_EXAMPLES_DIR / "PE1" / "spec.yaml"
    spec = load_spec_from_file(spec_path)

    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir)
        lock = build_assignment(
            spec=spec,
            output_dir=output_dir,
            spec_dir=spec_path.parent,
        )
        yield output_dir, lock, spec


class TestBuildDirectoryStructure:
    """Test that hammer build creates the expected directory structure."""

    def test_creates_student_bundle(self, build_output):
        """Build should create student_bundle directory."""
        output_dir, _, _ = build_output
        student_dir = output_dir / "student_bundle"
        assert student_dir.exists()
        assert student_dir.is_dir()

    def test_creates_grading_bundle(self, build_output):
        """Build should create grading_bundle directory."""
        output_dir, _, _ = build_output
        grading_dir = output_dir / "grading_bundle"
        assert grading_dir.exists()
        assert grading_dir.is_dir()

    def test_creates_lock_json(self, build_output):
        """Build should create lock.json file."""
        output_dir, _, _ = build_output
        lock_path = output_dir / "lock.json"
        assert lock_path.exists()
        assert lock_path.is_file()


class TestStudentBundle:
    """Test student bundle contents."""

    def test_has_vagrantfile(self, build_output):
        """Student bundle should have a Vagrantfile."""
        output_dir, _, _ = build_output
        vagrantfile = output_dir / "student_bundle" / "Vagrantfile"
        assert vagrantfile.exists()

    def test_has_inventory(self, build_output):
        """Student bundle should have inventory directory."""
        output_dir, _, _ = build_output
        inventory = output_dir / "student_bundle" / "inventory"
        assert inventory.exists()
        assert (inventory / "hosts.yml").exists()

    def test_has_ansible_cfg(self, build_output):
        """Student bundle should have ansible.cfg."""
        output_dir, _, _ = build_output
        ansible_cfg = output_dir / "student_bundle" / "ansible.cfg"
        assert ansible_cfg.exists()

    def test_has_readme(self, build_output):
        """Student bundle should have README.md."""
        output_dir, _, _ = build_output
        readme = output_dir / "student_bundle" / "README.md"
        assert readme.exists()

    def test_has_group_vars(self, build_output):
        """Student bundle should have group_vars directory."""
        output_dir, _, _ = build_output
        group_vars = output_dir / "student_bundle" / "group_vars"
        assert group_vars.exists()

    def test_has_provided_files(self, build_output):
        """Student bundle should contain provided_files from spec."""
        output_dir, _, spec = build_output
        if spec.entrypoints.provided_files:
            for pf in spec.entrypoints.provided_files:
                dest = output_dir / "student_bundle" / pf.destination
                assert dest.exists(), f"Missing provided file: {pf.destination}"


class TestGradingBundle:
    """Test grading bundle contents."""

    def test_has_vagrantfile(self, build_output):
        """Grading bundle should have a Vagrantfile."""
        output_dir, _, _ = build_output
        vagrantfile = output_dir / "grading_bundle" / "Vagrantfile"
        assert vagrantfile.exists()

    def test_has_inventory(self, build_output):
        """Grading bundle should have inventory directory."""
        output_dir, _, _ = build_output
        inventory = output_dir / "grading_bundle" / "inventory"
        assert inventory.exists()
        assert (inventory / "hosts.yml").exists()

    def test_has_ansible_cfg(self, build_output):
        """Grading bundle should have ansible.cfg."""
        output_dir, _, _ = build_output
        ansible_cfg = output_dir / "grading_bundle" / "ansible.cfg"
        assert ansible_cfg.exists()

    def test_has_tests_directory(self, build_output):
        """Grading bundle should have tests directory."""
        output_dir, _, _ = build_output
        tests = output_dir / "grading_bundle" / "tests"
        assert tests.exists()

    def test_has_phase_tests(self, build_output):
        """Grading bundle should have test files for phases."""
        output_dir, _, _ = build_output
        tests_dir = output_dir / "grading_bundle" / "tests"

        # Tests are organized in phase subdirectories (baseline, mutation, idempotence)
        # Should have at least one phase directory with test files
        test_files = list(tests_dir.glob("*/test_*.py"))
        assert len(test_files) >= 1, "No test files generated"

    def test_has_phase_overlays(self, build_output):
        """Grading bundle should have phase overlay directories."""
        output_dir, _, spec = build_output
        overlays_dir = output_dir / "grading_bundle" / "overlays"

        # Should have baseline overlay if variable_contracts exist
        if spec.variable_contracts:
            assert overlays_dir.exists()
            assert (overlays_dir / "baseline").exists()

    def test_has_conftest(self, build_output):
        """Grading bundle should have conftest.py for testinfra."""
        output_dir, _, _ = build_output
        conftest = output_dir / "grading_bundle" / "tests" / "conftest.py"
        assert conftest.exists()


class TestMultiplePEBuilds:
    """Test building different PE specs."""

    @pytest.mark.parametrize("pe_name", ["PE1", "PE2", "PE3", "PE4"])
    def test_pe_builds_successfully(self, pe_name):
        """Each PE spec should build without errors."""
        spec_path = REAL_EXAMPLES_DIR / pe_name / "spec.yaml"
        if not spec_path.exists():
            pytest.skip(f"{pe_name} spec not found")

        spec = load_spec_from_file(spec_path)

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            lock = build_assignment(
                spec=spec,
                output_dir=output_dir,
                spec_dir=spec_path.parent,
            )

            assert (output_dir / "student_bundle").exists()
            assert (output_dir / "grading_bundle").exists()
            assert (output_dir / "lock.json").exists()
            assert lock.spec_hash is not None
