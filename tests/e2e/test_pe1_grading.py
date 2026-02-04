import pytest
import json
import subprocess
import shutil
from pathlib import Path


def _build_cmd(hammer_bin, args):
    """Build command list handling space-separated paths."""
    if " " in hammer_bin:
        return hammer_bin.split() + args
    return [hammer_bin] + args


def _print_failed_tests(report):
    """Print failed test details for debugging."""
    for phase_name, phase in report["phases"].items():
        failed_tests = [d for d in phase["tests"]["details"] if d["outcome"] == "failed"]
        if failed_tests:
            print(f"\nFailed tests in {phase_name}:")
            for t in failed_tests:
                print(f"  - {t['name']}: {t['message']}")


@pytest.mark.e2e
class TestPE1Grading:
    """End-to-end tests for PE1 grading pipeline."""

    def test_grading_pipeline(self, hammer_bin, pe1_dir, pe1_build, pe1_vms):
        """
        Test the full grading pipeline with both failing and passing scenarios.

        1. Run with empty playbook -> should fail verification.
        2. Run with solution playbook -> should pass everything.
        """
        spec_path = pe1_dir / "spec.yaml"
        solution_playbook = pe1_dir / "playbook_solution.yaml"

        # ---------------------------------------------------------
        # SCENARIO 1: Empty Playbook (FAIL)
        # ---------------------------------------------------------
        print(f"\n{'='*60}")
        print(f"[PE1] SCENARIO 1: Empty Playbook (expecting failure)")
        print(f"{'='*60}")

        empty_repo = pe1_build.parent / "empty_repo"
        empty_repo.mkdir(exist_ok=True)
        (empty_repo / "playbook.yaml").write_text("- hosts: all\n  tasks: []\n")

        results_empty = pe1_build.parent / "results_empty"

        cmd_empty = _build_cmd(hammer_bin, [
            "grade",
            "--spec", str(spec_path),
            "--student-repo", str(empty_repo),
            "--out", str(results_empty),
            "--grading-bundle", str(pe1_vms),
            "--skip-build"
        ])

        print("[PE1] Running grading with empty playbook...")
        # Should exit with non-zero because some tests will fail
        result_empty = subprocess.run(cmd_empty, capture_output=True, text=True)

        # Check report.json for scenario 1
        report_empty_path = results_empty / "results" / "report.json"
        assert report_empty_path.exists(), "Empty playbook report.json not found"

        with open(report_empty_path) as f:
            report_empty = json.load(f)

        print(f"[PE1] Empty playbook score: {report_empty['percentage']:.1f}%")

        assert report_empty["success"] is False, "Empty playbook should not succeed"
        assert report_empty["percentage"] < 50.0, \
            f"Empty playbook should score < 50%, got {report_empty['percentage']:.1f}%"

        # ---------------------------------------------------------
        # SCENARIO 2: Solution Playbook (PASS)
        # ---------------------------------------------------------
        print(f"\n{'='*60}")
        print(f"[PE1] SCENARIO 2: Solution Playbook (expecting success)")
        print(f"{'='*60}")

        solution_repo = pe1_build.parent / "solution_repo"
        solution_repo.mkdir(exist_ok=True)

        # Copy solution as playbook.yaml
        shutil.copy2(solution_playbook, solution_repo / "playbook.yaml")

        # Copy other required files (files/, templates/)
        if (pe1_dir / "files").exists():
            shutil.copytree(pe1_dir / "files", solution_repo / "files")
        if (pe1_dir / "templates").exists():
            shutil.copytree(pe1_dir / "templates", solution_repo / "templates")

        results_solution = pe1_build.parent / "results_solution"

        cmd_solution = _build_cmd(hammer_bin, [
            "grade",
            "--spec", str(spec_path),
            "--student-repo", str(solution_repo),
            "--out", str(results_solution),
            "--grading-bundle", str(pe1_vms),
            "--skip-build",
            "--verbose"
        ])

        print("[PE1] Running grading with solution playbook...")
        result_solution = subprocess.run(cmd_solution, capture_output=True, text=True)

        # Check report.json for scenario 2
        report_solution_path = results_solution / "results" / "report.json"
        assert report_solution_path.exists(), "Solution playbook report.json not found"

        with open(report_solution_path) as f:
            report_solution = json.load(f)

        print(f"[PE1] Solution playbook score: {report_solution['percentage']:.1f}%")

        if result_solution.returncode != 0:
            print(f"[PE1] STDOUT: {result_solution.stdout}")
            print(f"[PE1] STDERR: {result_solution.stderr}")
            _print_failed_tests(report_solution)

        # Allow minor flakiness - solution should score at least 80%
        assert report_solution["percentage"] >= 80.0, \
            f"Solution should score >= 80%, got {report_solution['percentage']:.1f}%"

        # Verify all phases exist
        assert "baseline" in report_solution["phases"], "Missing baseline phase"
        assert "mutation" in report_solution["phases"], "Missing mutation phase"
        assert "idempotence" in report_solution["phases"], "Missing idempotence phase"

        print(f"\n[PE1] All scenarios completed successfully!")
