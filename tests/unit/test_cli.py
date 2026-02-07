"""Tests for HAMMER CLI module."""

import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

PROJECT_ROOT = Path(__file__).parent.parent.parent
REAL_EXAMPLES = PROJECT_ROOT / "real_examples"


class TestValidateCommand:
    """Tests for `hammer validate` subcommand."""

    def test_validate_valid_spec(self):
        """Valid spec exits 0 with success message."""
        result = subprocess.run(
            [sys.executable, "-m", "hammer.cli", "validate",
             "--spec", str(REAL_EXAMPLES / "PE1" / "spec.yaml")],
            capture_output=True, text=True, timeout=30,
        )
        assert result.returncode == 0
        assert "valid" in result.stdout.lower()

    def test_validate_nonexistent_spec(self):
        """Nonexistent spec file exits non-zero."""
        result = subprocess.run(
            [sys.executable, "-m", "hammer.cli", "validate",
             "--spec", "/nonexistent/spec.yaml"],
            capture_output=True, text=True, timeout=30,
        )
        assert result.returncode != 0

    def test_validate_invalid_yaml(self, tmp_path):
        """Invalid YAML content exits non-zero."""
        bad_spec = tmp_path / "bad.yaml"
        bad_spec.write_text("assignment_id: 123\n")  # int, not string
        result = subprocess.run(
            [sys.executable, "-m", "hammer.cli", "validate",
             "--spec", str(bad_spec)],
            capture_output=True, text=True, timeout=30,
        )
        assert result.returncode != 0


class TestMissingArgs:
    """Tests for missing required arguments."""

    def test_no_subcommand(self):
        """No subcommand exits non-zero."""
        result = subprocess.run(
            [sys.executable, "-m", "hammer.cli"],
            capture_output=True, text=True, timeout=30,
        )
        assert result.returncode != 0

    def test_validate_no_spec(self):
        """validate without --spec exits non-zero."""
        result = subprocess.run(
            [sys.executable, "-m", "hammer.cli", "validate"],
            capture_output=True, text=True, timeout=30,
        )
        assert result.returncode != 0

    def test_build_no_out(self):
        """build without --out exits non-zero."""
        result = subprocess.run(
            [sys.executable, "-m", "hammer.cli", "build",
             "--spec", str(REAL_EXAMPLES / "PE1" / "spec.yaml")],
            capture_output=True, text=True, timeout=30,
        )
        assert result.returncode != 0

    def test_grade_no_student_repo(self):
        """grade without --student-repo exits non-zero."""
        result = subprocess.run(
            [sys.executable, "-m", "hammer.cli", "grade",
             "--spec", str(REAL_EXAMPLES / "PE1" / "spec.yaml"),
             "--out", "/tmp/test-out"],
            capture_output=True, text=True, timeout=30,
        )
        assert result.returncode != 0


class TestInitCommand:
    """Tests for `hammer init` subcommand."""

    def test_init_creates_infrastructure_files(self, tmp_path):
        """init generates Vagrantfile, inventory, ansible.cfg, and host_vars."""
        out_dir = tmp_path / "lab"
        result = subprocess.run(
            [sys.executable, "-m", "hammer.cli", "init",
             "--spec", str(REAL_EXAMPLES / "PE1" / "spec.yaml"),
             "--out", str(out_dir)],
            capture_output=True, text=True, timeout=30,
        )
        assert result.returncode == 0
        assert "Init complete" in result.stdout

        # Check expected files exist
        assert (out_dir / "Vagrantfile").is_file()
        assert (out_dir / "inventory" / "hosts.yml").is_file()
        assert (out_dir / "ansible.cfg").is_file()
        assert (out_dir / "host_vars").is_dir()
        assert (out_dir / "roles").is_dir()

        # Check NO grading/test artifacts were generated
        assert not (out_dir / "student_bundle").exists()
        assert not (out_dir / "grading_bundle").exists()
        assert not (out_dir / "lock.json").exists()

    def test_init_no_out_arg(self):
        """init without --out exits non-zero."""
        result = subprocess.run(
            [sys.executable, "-m", "hammer.cli", "init",
             "--spec", str(REAL_EXAMPLES / "PE1" / "spec.yaml")],
            capture_output=True, text=True, timeout=30,
        )
        assert result.returncode != 0

    def test_init_invalid_spec(self, tmp_path):
        """init with invalid spec exits non-zero."""
        bad_spec = tmp_path / "bad.yaml"
        bad_spec.write_text("assignment_id: 123\n")
        result = subprocess.run(
            [sys.executable, "-m", "hammer.cli", "init",
             "--spec", str(bad_spec),
             "--out", str(tmp_path / "out")],
            capture_output=True, text=True, timeout=30,
        )
        assert result.returncode != 0

    def test_init_needs_no_tools(self):
        """init command doesn't require any external tools."""
        from hammer.prerequisites import check_prerequisites
        missing = check_prerequisites("init")
        assert missing == []


class TestValidationErrorFormatting:
    """Tests for user-friendly validation error formatting."""

    def test_format_validation_error(self):
        """Validation errors include field path information."""
        from pydantic import ValidationError
        from hammer.cli import _format_validation_error

        try:
            from hammer.spec import HammerSpec
            HammerSpec.model_validate({"assignment_id": "!!!"})
        except ValidationError as e:
            output = _format_validation_error(e, Path("test.yaml"))
            assert "test.yaml" in output
            assert "assignment_id" in output


class TestPrerequisiteChecks:
    """Tests for prerequisite checking."""

    def test_validate_needs_no_tools(self):
        """validate command doesn't require any external tools."""
        from hammer.prerequisites import check_prerequisites
        missing = check_prerequisites("validate")
        assert missing == []

    def test_build_needs_ansible(self):
        """build command requires ansible-playbook."""
        from hammer.prerequisites import check_prerequisites
        with patch("shutil.which", return_value=None):
            missing = check_prerequisites("build")
            assert any("ansible" in m.lower() for m in missing)

    def test_grade_needs_vagrant(self):
        """grade command requires vagrant."""
        from hammer.prerequisites import check_prerequisites
        with patch("shutil.which", return_value=None):
            missing = check_prerequisites("grade")
            assert any("vagrant" in m.lower() for m in missing)
