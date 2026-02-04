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
class TestPE3Grading:
    """End-to-end tests for PE3 grading pipeline."""

    def test_empty_playbook_fails(self, hammer_bin, pe3_dir, pe3_build, pe3_vms):
        """Empty playbook should score < 50%."""
        spec_path = pe3_dir / "spec.yaml"

        print(f"\n{'='*60}")
        print(f"[PE3] SCENARIO 1: Empty Playbook (expecting failure)")
        print(f"{'='*60}")

        empty_repo = pe3_build.parent / "empty_repo_pe3"
        empty_repo.mkdir(exist_ok=True)
        (empty_repo / "playbook.yml").write_text("- hosts: all\n  tasks: []\n")

        # Copy templates directory (required by spec)
        templates_dir = empty_repo / "templates"
        templates_dir.mkdir(exist_ok=True)
        shutil.copy2(pe3_dir / "landing-page.html.j2", templates_dir / "landing-page.html.j2")

        results_empty = pe3_build.parent / "results_empty_pe3"

        cmd_empty = _build_cmd(hammer_bin, [
            "grade",
            "--spec", str(spec_path),
            "--student-repo", str(empty_repo),
            "--out", str(results_empty),
            "--grading-bundle", str(pe3_vms),
            "--skip-build"
        ])

        print("[PE3] Running grading with empty playbook...")
        result_empty = subprocess.run(cmd_empty, capture_output=True, text=True)

        # Check report.json
        report_empty_path = results_empty / "results" / "report.json"
        assert report_empty_path.exists(), "Empty playbook report.json not found"

        with open(report_empty_path) as f:
            report_empty = json.load(f)

        print(f"[PE3] Empty playbook score: {report_empty['percentage']:.1f}%")

        assert report_empty["success"] is False, "Empty playbook should not succeed"
        assert report_empty["percentage"] < 50.0, \
            f"Empty playbook should score < 50%, got {report_empty['percentage']:.1f}%"

        print(f"[PE3] Empty playbook test passed!")

    def test_solution_playbook_passes(self, hammer_bin, pe3_dir, pe3_build, pe3_vms):
        """Solution should score >= 80%."""
        spec_path = pe3_dir / "spec.yaml"
        solution_playbook = pe3_dir / "playbook_solution.yml"

        print(f"\n{'='*60}")
        print(f"[PE3] SCENARIO 2: Solution Playbook (expecting success)")
        print(f"{'='*60}")

        solution_repo = pe3_build.parent / "solution_repo_pe3"
        solution_repo.mkdir(exist_ok=True)

        # Copy solution as playbook.yml
        shutil.copy2(solution_playbook, solution_repo / "playbook.yml")

        # Copy templates directory
        if (pe3_dir / "templates").exists():
            shutil.copytree(pe3_dir / "templates", solution_repo / "templates")
        else:
            # Fallback: create templates and copy landing-page.html.j2
            templates_dir = solution_repo / "templates"
            templates_dir.mkdir(exist_ok=True)
            shutil.copy2(pe3_dir / "landing-page.html.j2", templates_dir / "landing-page.html.j2")
            # Also copy mypage.conf.j2 if it exists in pe3_dir/templates
            mypage_conf = pe3_dir / "templates" / "mypage.conf.j2"
            if mypage_conf.exists():
                shutil.copy2(mypage_conf, templates_dir / "mypage.conf.j2")

        results_solution = pe3_build.parent / "results_solution_pe3"

        cmd_solution = _build_cmd(hammer_bin, [
            "grade",
            "--spec", str(spec_path),
            "--student-repo", str(solution_repo),
            "--out", str(results_solution),
            "--grading-bundle", str(pe3_vms),
            "--skip-build",
            "--verbose"
        ])

        print("[PE3] Running grading with solution playbook...")
        result_solution = subprocess.run(cmd_solution, capture_output=True, text=True)

        # Check report.json
        report_solution_path = results_solution / "results" / "report.json"
        assert report_solution_path.exists(), "Solution playbook report.json not found"

        with open(report_solution_path) as f:
            report_solution = json.load(f)

        print(f"[PE3] Solution playbook score: {report_solution['percentage']:.1f}%")

        if result_solution.returncode != 0:
            print(f"[PE3] STDOUT: {result_solution.stdout}")
            print(f"[PE3] STDERR: {result_solution.stderr}")
            _print_failed_tests(report_solution)

        # Allow minor flakiness - solution should score at least 80%
        assert report_solution["percentage"] >= 80.0, \
            f"Solution should score >= 80%, got {report_solution['percentage']:.1f}%"

        print(f"\n[PE3] Solution playbook test passed!")
