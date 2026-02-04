import pytest
import json
import subprocess
import shutil
from pathlib import Path

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
        empty_repo = pe1_build.parent / "empty_repo"
        empty_repo.mkdir(exist_ok=True)
        (empty_repo / "playbook.yml").write_text("- hosts: all
  tasks: []
")
        
        results_empty = pe1_build.parent / "results_empty"
        
        # We use --skip-build and --grading-bundle to use the already up VMs
        cmd_empty = []
        if " " in hammer_bin:
            cmd_empty = hammer_bin.split()
        else:
            cmd_empty = [hammer_bin]
            
        cmd_empty += [
            "grade",
            "--spec", str(spec_path),
            "--student-repo", str(empty_repo),
            "--out", str(results_empty),
            "--grading-bundle", str(pe1_vms),
            "--skip-build"
        ]
        
        print("
Running grading with empty playbook (expecting failure)...")
        # Should exit with non-zero because some tests will fail
        result_empty = subprocess.run(cmd_empty, capture_output=True, text=True)
        
        # Check report.json for scenario 1
        report_empty_path = results_empty / "results" / "report.json"
        assert report_empty_path.exists()
        
        with open(report_empty_path) as f:
            report_empty = json.load(f)
            
        assert report_empty["success"] is False
        assert report_empty["percentage"] < 100.0
        
        # ---------------------------------------------------------
        # SCENARIO 2: Solution Playbook (PASS)
        # ---------------------------------------------------------
        solution_repo = pe1_build.parent / "solution_repo"
        solution_repo.mkdir(exist_ok=True)
        
        # Copy solution as playbook.yml
        shutil.copy2(solution_playbook, solution_repo / "playbook.yml")
        
        # Copy other required files (files/, templates/)
        if (pe1_dir / "files").exists():
            shutil.copytree(pe1_dir / "files", solution_repo / "files")
        if (pe1_dir / "templates").exists():
            shutil.copytree(pe1_dir / "templates", solution_repo / "templates")
            
        results_solution = pe1_build.parent / "results_solution"
        
        cmd_solution = []
        if " " in hammer_bin:
            cmd_solution = hammer_bin.split()
        else:
            cmd_solution = [hammer_bin]
            
        cmd_solution += [
            "grade",
            "--spec", str(spec_path),
            "--student-repo", str(solution_repo),
            "--out", str(results_solution),
            "--grading-bundle", str(pe1_vms),
            "--skip-build",
            "--verbose"
        ]
        
        print("Running grading with solution playbook (expecting success)...")
        result_solution = subprocess.run(cmd_solution, capture_output=True, text=True)
        
        if result_solution.returncode != 0:
            print(f"STDOUT: {result_solution.stdout}")
            print(f"STDERR: {result_solution.stderr}")
            
        assert result_solution.returncode == 0
        
        # Check report.json for scenario 2
        report_solution_path = results_solution / "results" / "report.json"
        assert report_solution_path.exists()
        
        with open(report_solution_path) as f:
            report_solution = json.load(f)
            
        assert report_solution["success"] is True
        assert report_solution["percentage"] == 100.0
        assert "baseline" in report_solution["phases"]
        assert "mutation" in report_solution["phases"]
        assert "idempotence" in report_solution["phases"]
