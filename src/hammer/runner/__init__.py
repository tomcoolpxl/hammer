"""HAMMER Runner - Grading execution module.

Orchestrates the grading pipeline: Converge -> Snapshot -> Verify.
"""

import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from hammer.spec import HammerSpec, load_spec_from_file
from hammer.plan import ExecutionPlan, build_execution_plan
from hammer.builder import build_assignment
from hammer.builder.network import NetworkPlan, generate_network_plan
from hammer.runner.results import (
    GradeReport,
    PhaseResult,
    ConvergeResult,
    TestResult,
    calculate_phase_score,
    calculate_total_score,
)
from hammer.runner.ansible import run_playbook, check_idempotence
from hammer.runner.pytest_runner import run_phase_tests
from hammer.runner.snapshot import write_snapshot_playbook


__all__ = ["grade_assignment", "GradeReport"]


def grade_assignment(
    spec: HammerSpec,
    student_repo: Path,
    output_dir: Path,
    phases: Optional[List[str]] = None,
    grading_bundle: Optional[Path] = None,
    skip_build: bool = False,
    skip_vm_setup: bool = False,
    verbose: bool = False,
) -> GradeReport:
    """
    Execute the full grading pipeline.

    Args:
        spec: The HAMMER spec
        student_repo: Path to student's playbook/roles
        output_dir: Directory for grading artifacts and results
        phases: Phases to run (default: all)
        grading_bundle: Path to existing grading bundle with running VMs
        skip_build: Skip regenerating grading bundle
        skip_vm_setup: Assume VMs are already running
        verbose: Enable verbose output

    Returns:
        GradeReport with all results
    """
    if phases is None:
        phases = ["baseline", "mutation", "idempotence"]

    # Create output directory structure
    output_dir.mkdir(parents=True, exist_ok=True)
    work_dir = output_dir / "work"
    results_dir = output_dir / "results"
    work_dir.mkdir(exist_ok=True)
    results_dir.mkdir(exist_ok=True)

    # Build execution plan
    plan = build_execution_plan(spec)
    network = generate_network_plan(spec)

    # Determine grading directory
    if grading_bundle:
        # Use existing grading bundle (e.g., with running VMs)
        grading_dir = Path(grading_bundle)
        if not grading_dir.exists():
            raise ValueError(f"Grading bundle not found at {grading_dir}")
    elif not skip_build:
        # Generate new grading bundle
        bundle_dir = work_dir / "bundle"
        build_assignment(spec, bundle_dir)
        grading_dir = bundle_dir / "grading_bundle"
    else:
        grading_dir = work_dir / "bundle" / "grading_bundle"
        if not grading_dir.exists():
            raise ValueError(f"Grading bundle not found at {grading_dir}")

    # Copy student playbook and roles to grading bundle
    _setup_student_files(student_repo, grading_dir, spec)

    # Initialize report
    report = GradeReport(
        assignment_id=spec.assignment_id,
        spec_version=spec.spec_version,
        timestamp=datetime.utcnow().isoformat(),
    )

    # Run each phase
    for phase in phases:
        phase_results_dir = results_dir / phase
        phase_results_dir.mkdir(exist_ok=True)

        if verbose:
            print(f"\n{'='*60}")
            print(f"Running phase: {phase}")
            print(f"{'='*60}")

        phase_result = _run_phase(
            spec=spec,
            plan=plan,
            network=network,
            phase=phase,
            grading_dir=grading_dir,
            results_dir=phase_results_dir,
            verbose=verbose,
        )

        report.phases[phase] = phase_result

    # Calculate total scores
    total_earned, total_max, percentage = calculate_total_score(report.phases)
    report.total_score = total_earned
    report.max_score = total_max
    report.percentage = percentage

    # Check for any failures
    report.success = all(
        p.converge.success for p in report.phases.values()
    )

    # Write report
    _write_report(report, results_dir)

    return report


def _setup_student_files(
    student_repo: Path,
    grading_dir: Path,
    spec: HammerSpec,
) -> None:
    """
    Copy student playbook and roles to grading directory.

    Args:
        student_repo: Path to student's submission
        grading_dir: Grading bundle directory
        spec: The HAMMER spec
    """
    # Copy playbook
    playbook_name = spec.entrypoints.playbook_path
    src_playbook = student_repo / playbook_name
    dst_playbook = grading_dir / playbook_name

    if src_playbook.exists():
        shutil.copy2(src_playbook, dst_playbook)

    # Copy roles directory if it exists
    src_roles = student_repo / "roles"
    dst_roles = grading_dir / "roles"

    if src_roles.exists():
        if dst_roles.exists():
            shutil.rmtree(dst_roles)
        shutil.copytree(src_roles, dst_roles)

    # Copy templates directory if it exists
    src_templates = student_repo / "templates"
    dst_templates = grading_dir / "templates"

    if src_templates.exists():
        if dst_templates.exists():
            shutil.rmtree(dst_templates)
        shutil.copytree(src_templates, dst_templates)

    # Copy any required files
    if spec.entrypoints.required_files:
        for req_file in spec.entrypoints.required_files:
            src = student_repo / req_file
            dst = grading_dir / req_file
            if src.exists() and src != src_playbook:
                dst.parent.mkdir(parents=True, exist_ok=True)
                if src.is_dir():
                    if dst.exists():
                        shutil.rmtree(dst)
                    shutil.copytree(src, dst)
                else:
                    shutil.copy2(src, dst)


def _run_phase(
    spec: HammerSpec,
    plan: ExecutionPlan,
    network: NetworkPlan,
    phase: str,
    grading_dir: Path,
    results_dir: Path,
    verbose: bool = False,
) -> PhaseResult:
    """
    Run a single grading phase.

    Args:
        spec: The HAMMER spec
        plan: The execution plan
        network: The network plan
        phase: Phase name
        grading_dir: Grading bundle directory
        results_dir: Directory for phase results
        verbose: Enable verbose output

    Returns:
        PhaseResult for this phase
    """
    # Get phase-specific overlay
    # For idempotence, use mutation overlay
    overlay_phase = "mutation" if phase == "idempotence" else phase
    overlay_dir = grading_dir / "overlays" / overlay_phase
    extra_vars_file = overlay_dir / "extra_vars.yml"

    # Apply overlay group_vars by copying to main group_vars
    overlay_group_vars = overlay_dir / "group_vars"
    main_group_vars = grading_dir / "group_vars"

    if overlay_group_vars.exists():
        # Copy overlay group_vars to main group_vars
        for gv_file in overlay_group_vars.glob("*.yml"):
            dst = main_group_vars / gv_file.name
            shutil.copy2(gv_file, dst)

    # Paths
    playbook_path = grading_dir / spec.entrypoints.playbook_path
    inventory_path = grading_dir / "inventory" / "hosts.yml"
    tests_dir = grading_dir / "tests"

    # Step 1: Converge
    if verbose:
        print(f"\n[{phase}] Running converge...")

    converge_result, converge_log = run_playbook(
        playbook_path=playbook_path,
        inventory_path=inventory_path,
        working_dir=grading_dir,
        extra_vars_file=extra_vars_file if extra_vars_file.exists() else None,
        quiet=not verbose,
    )

    # Save converge log
    (results_dir / "converge.log").write_text(converge_log)
    (results_dir / "converge_result.json").write_text(
        converge_result.model_dump_json(indent=2)
    )

    if verbose:
        print(f"[{phase}] Converge: ok={converge_result.ok}, "
              f"changed={converge_result.changed}, failed={converge_result.failed}")

    # Special handling for idempotence phase
    if phase == "idempotence":
        is_idempotent, idempotence_msg = check_idempotence(converge_result)
        if verbose:
            print(f"[{phase}] Idempotence check: {idempotence_msg}")

    # Step 2: Run tests
    if verbose:
        print(f"\n[{phase}] Running verification tests...")

    # Determine which phase's tests to run
    # For idempotence, we run the same tests as mutation phase
    test_phase = "mutation" if phase == "idempotence" else phase

    test_result, test_log = run_phase_tests(
        tests_dir=tests_dir,
        phase=test_phase,
        working_dir=results_dir,
        verbose=verbose,
    )

    # Save test results
    (results_dir / "test.log").write_text(test_log)
    (results_dir / "test_result.json").write_text(
        test_result.model_dump_json(indent=2)
    )

    if verbose:
        print(f"[{phase}] Tests: passed={test_result.passed}, "
              f"failed={test_result.failed}, skipped={test_result.skipped}")

    # Calculate phase score
    earned, max_score = calculate_phase_score(test_result)

    return PhaseResult(
        phase=phase,
        converge=converge_result,
        tests=test_result,
        score=earned,
        max_score=max_score,
    )


def _write_report(report: GradeReport, results_dir: Path) -> None:
    """
    Write grading report to disk.

    Args:
        report: The grade report
        results_dir: Directory to write report
    """
    # Write JSON report
    report_json = results_dir / "report.json"
    report_json.write_text(report.model_dump_json(indent=2))

    # Write human-readable summary
    summary_lines = [
        f"HAMMER Grading Report",
        f"=====================",
        f"Assignment: {report.assignment_id}",
        f"Timestamp: {report.timestamp}",
        f"",
        f"Results by Phase:",
        f"-----------------",
    ]

    for phase_name, phase_result in report.phases.items():
        summary_lines.append(f"\n{phase_name.upper()}:")
        summary_lines.append(f"  Converge: {'PASS' if phase_result.converge.success else 'FAIL'}")
        summary_lines.append(f"    ok={phase_result.converge.ok}, "
                           f"changed={phase_result.converge.changed}, "
                           f"failed={phase_result.converge.failed}")
        summary_lines.append(f"  Tests: {phase_result.tests.passed} passed, "
                           f"{phase_result.tests.failed} failed")
        summary_lines.append(f"  Score: {phase_result.score:.1f} / {phase_result.max_score:.1f}")

    summary_lines.extend([
        f"",
        f"Total Score: {report.total_score:.1f} / {report.max_score:.1f} ({report.percentage:.1f}%)",
        f"Overall: {'PASS' if report.success else 'FAIL'}",
    ])

    summary_txt = results_dir / "summary.txt"
    summary_txt.write_text("\n".join(summary_lines))
