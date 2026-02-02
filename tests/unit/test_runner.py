"""Unit tests for HAMMER runner module."""

import sys
import tempfile
from pathlib import Path

import pytest

# Ensure src is in path
PROJECT_ROOT = Path(__file__).parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from hammer.spec import load_spec_from_file, HammerSpec
from hammer.plan import build_execution_plan
from hammer.runner.results import (
    ConvergeResult,
    TestResult,
    TestCaseResult,
    PhaseResult,
    GradeReport,
    calculate_phase_score,
    calculate_total_score,
)
from hammer.runner.ansible import check_idempotence
from hammer.runner.snapshot import get_files_to_check, render_snapshot_playbook

FIXTURES_DIR = PROJECT_ROOT / "tests" / "fixtures"


@pytest.fixture
def full_spec() -> HammerSpec:
    return load_spec_from_file(FIXTURES_DIR / "valid_full.yaml")


@pytest.fixture
def plan(full_spec):
    return build_execution_plan(full_spec)


class TestConvergeResult:
    """Tests for ConvergeResult model."""

    def test_converge_result_defaults(self):
        """ConvergeResult should have sensible defaults."""
        result = ConvergeResult()
        assert result.ok == 0
        assert result.changed == 0
        assert result.failed == 0
        assert result.success is True

    def test_converge_result_with_values(self):
        """ConvergeResult should accept values."""
        result = ConvergeResult(
            ok=10,
            changed=2,
            failed=1,
            unreachable=0,
            skipped=3,
            success=False,
            error_message="Test failed",
        )
        assert result.ok == 10
        assert result.changed == 2
        assert result.failed == 1
        assert result.success is False


class TestIdempotenceCheck:
    """Tests for idempotence checking."""

    def test_idempotent_result(self):
        """A result with changed=0 should be idempotent."""
        result = ConvergeResult(ok=10, changed=0, failed=0, success=True)
        is_idempotent, msg = check_idempotence(result)
        assert is_idempotent is True
        assert "idempotent" in msg.lower()

    def test_non_idempotent_changed(self):
        """A result with changed>0 should not be idempotent."""
        result = ConvergeResult(ok=10, changed=2, failed=0, success=True)
        is_idempotent, msg = check_idempotence(result)
        assert is_idempotent is False
        assert "changed" in msg.lower()

    def test_non_idempotent_failed(self):
        """A result with failures should not be idempotent."""
        result = ConvergeResult(ok=10, changed=0, failed=1, success=True)
        is_idempotent, msg = check_idempotence(result)
        assert is_idempotent is False
        assert "failed" in msg.lower()

    def test_non_idempotent_unsuccessful(self):
        """An unsuccessful result should not be idempotent."""
        result = ConvergeResult(success=False, error_message="Playbook failed")
        is_idempotent, msg = check_idempotence(result)
        assert is_idempotent is False


class TestTestResult:
    """Tests for TestResult model."""

    def test_test_result_defaults(self):
        """TestResult should have sensible defaults."""
        result = TestResult()
        assert result.passed == 0
        assert result.failed == 0
        assert result.total_weight == 0.0
        assert result.earned_weight == 0.0

    def test_test_result_with_details(self):
        """TestResult should aggregate test case details."""
        details = [
            TestCaseResult(name="test_one", outcome="passed", weight=1.0),
            TestCaseResult(name="test_two", outcome="failed", weight=2.0),
            TestCaseResult(name="test_three", outcome="passed", weight=1.0),
        ]
        result = TestResult(
            passed=2,
            failed=1,
            total_weight=4.0,
            earned_weight=2.0,
            details=details,
        )
        assert result.passed == 2
        assert result.failed == 1
        assert len(result.details) == 3


class TestScoreCalculation:
    """Tests for score calculation functions."""

    def test_phase_score_calculation(self):
        """Phase score should be based on earned vs total weight."""
        tests = TestResult(
            passed=3,
            failed=1,
            total_weight=10.0,
            earned_weight=7.5,
        )
        earned, max_score = calculate_phase_score(tests)
        assert earned == 7.5
        assert max_score == 10.0

    def test_phase_score_zero_weight(self):
        """Zero total weight should return zero scores."""
        tests = TestResult(total_weight=0.0, earned_weight=0.0)
        earned, max_score = calculate_phase_score(tests)
        assert earned == 0.0
        assert max_score == 0.0

    def test_total_score_calculation(self):
        """Total score should aggregate across phases."""
        phases = {
            "baseline": PhaseResult(
                phase="baseline",
                converge=ConvergeResult(),
                tests=TestResult(),
                score=8.0,
                max_score=10.0,
            ),
            "mutation": PhaseResult(
                phase="mutation",
                converge=ConvergeResult(),
                tests=TestResult(),
                score=7.0,
                max_score=10.0,
            ),
        }
        total, max_score, pct = calculate_total_score(phases)
        assert total == 15.0
        assert max_score == 20.0
        assert pct == 75.0


class TestGradeReport:
    """Tests for GradeReport model."""

    def test_grade_report_creation(self):
        """GradeReport should be creatable with required fields."""
        report = GradeReport(
            assignment_id="test-assignment",
            spec_version="1.0",
        )
        assert report.assignment_id == "test-assignment"
        assert report.total_score == 0.0
        assert report.success is True

    def test_grade_report_serialization(self):
        """GradeReport should serialize to JSON."""
        report = GradeReport(
            assignment_id="test-assignment",
            spec_version="1.0",
            total_score=15.0,
            max_score=20.0,
            percentage=75.0,
        )
        json_str = report.model_dump_json()
        assert "test-assignment" in json_str
        assert "75.0" in json_str


class TestSnapshotPlaybook:
    """Tests for snapshot playbook generation."""

    def test_get_files_to_check(self, full_spec, plan):
        """Should extract files from spec."""
        files = get_files_to_check(full_spec, plan)
        assert len(files) > 0
        # Should include nginx config file from spec
        assert any("nginx" in f for f in files)

    def test_render_snapshot_playbook(self, full_spec, plan):
        """Should render valid YAML playbook."""
        import yaml

        with tempfile.TemporaryDirectory() as tmpdir:
            snapshot_dir = Path(tmpdir) / "snapshots"
            content = render_snapshot_playbook(
                full_spec, plan, "baseline", snapshot_dir
            )

            # Should be valid YAML
            parsed = yaml.safe_load(content)
            assert isinstance(parsed, list)
            assert len(parsed) > 0

            # Should have tasks
            play = parsed[0]
            assert "tasks" in play
            assert len(play["tasks"]) > 0
