"""Pytest execution for HAMMER grading.

Runs generated tests and parses results.
"""

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from hammer.runner.results import TestResult, TestCaseResult
from hammer.constants import ALL_PHASES


def run_phase_tests(
    tests_dir: Path,
    phase: str,
    working_dir: Path,
    timeout: int = int(os.environ.get("HAMMER_PYTEST_TIMEOUT", "300")),
    verbose: bool = False,
) -> tuple[TestResult, str]:
    """
    Run pytest tests for a specific phase.

    Args:
        tests_dir: Directory containing test files
        phase: Phase name (baseline, mutation, idempotence)
        working_dir: Working directory for execution
        timeout: Timeout in seconds
        verbose: Enable verbose output

    Returns:
        Tuple of (TestResult, stdout)
    """
    phase_tests_dir = tests_dir / phase

    if not phase_tests_dir.exists():
        return TestResult(), f"No tests found for phase {phase}"

    # Build pytest command
    report_file = working_dir / f"pytest_{phase}_report.json"

    cmd = [
        sys.executable, "-m", "pytest",
        str(phase_tests_dir),
        f"-m", phase,
        "--json-report",
        f"--json-report-file={report_file}",
        "-v" if verbose else "-q",
        "--tb=short",
    ]

    # Run pytest
    try:
        result = subprocess.run(
            cmd,
            cwd=str(tests_dir.parent),  # Run from grading bundle root
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        stdout = result.stdout + result.stderr
    except subprocess.TimeoutExpired:
        return TestResult(
            errors=1,
        ), f"Tests timed out after {timeout} seconds"

    # Parse results
    if report_file.exists():
        test_result = parse_pytest_json(report_file)
    else:
        # Fallback: parse from exit code
        test_result = TestResult(
            passed=0 if result.returncode != 0 else 1,
            failed=1 if result.returncode != 0 else 0,
        )

    return test_result, stdout


def parse_pytest_json(report_file: Path) -> TestResult:
    """
    Parse pytest-json-report output.

    Args:
        report_file: Path to the JSON report file

    Returns:
        TestResult with parsed data
    """
    with open(report_file) as f:
        data = json.load(f)

    summary = data.get("summary", {})
    tests = data.get("tests", [])

    details: List[TestCaseResult] = []
    total_weight = 0.0
    earned_weight = 0.0

    for test in tests:
        # Extract test name
        nodeid = test.get("nodeid", "")
        name = nodeid.split("::")[-1] if "::" in nodeid else nodeid

        outcome = test.get("outcome", "unknown")
        duration = test.get("duration", 0.0)

        # Extract failure message if present
        message = None
        if outcome == "failed":
            call_info = test.get("call", {})
            crash = call_info.get("crash", {})
            message = crash.get("message", "")
            if not message:
                longrepr = call_info.get("longrepr", "")
                if longrepr:
                    message = str(longrepr)[:200]

        # Extract weight from metadata if present, fallback to 1.0
        metadata = test.get("metadata", {})
        weight = float(metadata.get("weight", 1.0))
        total_weight += weight

        if outcome == "passed":
            earned_weight += weight

        details.append(TestCaseResult(
            name=name,
            outcome=outcome,
            weight=weight,
            duration=duration,
            message=message,
        ))

    return TestResult(
        passed=summary.get("passed", 0),
        failed=summary.get("failed", 0),
        skipped=summary.get("skipped", 0),
        errors=summary.get("error", 0),
        total_weight=total_weight,
        earned_weight=earned_weight,
        details=details,
    )


def run_all_phase_tests(
    tests_dir: Path,
    working_dir: Path,
    phases: Optional[List[str]] = None,
    timeout: int = int(os.environ.get("HAMMER_PYTEST_TIMEOUT", "300")),
    verbose: bool = False,
) -> Dict[str, tuple[TestResult, str]]:
    """
    Run tests for all specified phases.

    Args:
        tests_dir: Directory containing test files
        working_dir: Working directory for execution
        phases: List of phases to run (default: all)
        timeout: Timeout per phase in seconds
        verbose: Enable verbose output

    Returns:
        Dict mapping phase name to (TestResult, stdout)
    """
    if phases is None:
        phases = list(ALL_PHASES)

    results = {}
    for phase in phases:
        result, stdout = run_phase_tests(
            tests_dir, phase, working_dir, timeout, verbose
        )
        results[phase] = (result, stdout)

    return results
