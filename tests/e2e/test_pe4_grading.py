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
class TestPE4Grading:
    """End-to-end tests for PE4 grading pipeline."""

    def test_empty_role_fails(self, hammer_bin, pe4_dir, pe4_build, pe4_vms):
        """Empty role should score < 50%."""
        spec_path = pe4_dir / "spec.yaml"

        print(f"\n{'='*60}")
        print(f"[PE4] SCENARIO 1: Empty Role (expecting failure)")
        print(f"{'='*60}")

        empty_repo = pe4_build.parent / "empty_repo_pe4"
        empty_repo.mkdir(exist_ok=True)

        # Create minimal playbook that uses the role
        (empty_repo / "playbook.yml").write_text(
            "---\n"
            "- name: Run exam role\n"
            "  hosts: all\n"
            "  become: true\n"
            "  roles:\n"
            "    - pxl_exam_role\n"
        )

        # Create empty role structure
        role_dir = empty_repo / "roles" / "pxl_exam_role" / "tasks"
        role_dir.mkdir(parents=True, exist_ok=True)
        (role_dir / "main.yml").write_text("---\n# Empty role\n")

        results_empty = pe4_build.parent / "results_empty_pe4"

        cmd_empty = _build_cmd(hammer_bin, [
            "grade",
            "--spec", str(spec_path),
            "--student-repo", str(empty_repo),
            "--out", str(results_empty),
            "--grading-bundle", str(pe4_vms),
            "--skip-build"
        ])

        print("[PE4] Running grading with empty role...")
        result_empty = subprocess.run(cmd_empty, capture_output=True, text=True)

        # Check report.json
        report_empty_path = results_empty / "results" / "report.json"
        assert report_empty_path.exists(), "Empty role report.json not found"

        with open(report_empty_path) as f:
            report_empty = json.load(f)

        print(f"[PE4] Empty role score: {report_empty['percentage']:.1f}%")

        assert report_empty["success"] is False, "Empty role should not succeed"
        assert report_empty["percentage"] < 50.0, \
            f"Empty role should score < 50%, got {report_empty['percentage']:.1f}%"

        print(f"[PE4] Empty role test passed!")

    def test_solution_role_passes(self, hammer_bin, pe4_dir, pe4_build, pe4_vms):
        """Solution should score >= 80%."""
        spec_path = pe4_dir / "spec.yaml"
        solution_role = pe4_dir / "roles" / "pxl_exam_role"

        print(f"\n{'='*60}")
        print(f"[PE4] SCENARIO 2: Solution Role (expecting success)")
        print(f"{'='*60}")

        solution_repo = pe4_build.parent / "solution_repo_pe4"
        solution_repo.mkdir(exist_ok=True)

        # Create playbook that uses the role
        (solution_repo / "playbook.yml").write_text(
            "---\n"
            "- name: Run exam role\n"
            "  hosts: all\n"
            "  become: true\n"
            "  roles:\n"
            "    - pxl_exam_role\n"
        )

        # Copy solution role
        shutil.copytree(solution_role, solution_repo / "roles" / "pxl_exam_role")

        results_solution = pe4_build.parent / "results_solution_pe4"

        cmd_solution = _build_cmd(hammer_bin, [
            "grade",
            "--spec", str(spec_path),
            "--student-repo", str(solution_repo),
            "--out", str(results_solution),
            "--grading-bundle", str(pe4_vms),
            "--skip-build",
            "--verbose"
        ])

        print("[PE4] Running grading with solution role...")
        result_solution = subprocess.run(cmd_solution, capture_output=True, text=True)

        # Check report.json
        report_solution_path = results_solution / "results" / "report.json"
        assert report_solution_path.exists(), "Solution role report.json not found"

        with open(report_solution_path) as f:
            report_solution = json.load(f)

        print(f"[PE4] Solution role score: {report_solution['percentage']:.1f}%")

        if result_solution.returncode != 0:
            print(f"[PE4] STDOUT: {result_solution.stdout}")
            print(f"[PE4] STDERR: {result_solution.stderr}")
            _print_failed_tests(report_solution)

        # Allow minor flakiness - solution should score at least 80%
        assert report_solution["percentage"] >= 80.0, \
            f"Solution should score >= 80%, got {report_solution['percentage']:.1f}%"

        print(f"\n[PE4] Solution role test passed!")
