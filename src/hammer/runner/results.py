"""Result models for HAMMER grading.

Provides structured representations of grading results.
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ConvergeResult(BaseModel):
    """Result of an Ansible converge run."""

    ok: int = 0
    changed: int = 0
    failed: int = 0
    unreachable: int = 0
    skipped: int = 0
    rescued: int = 0
    ignored: int = 0
    play_recap: Dict[str, Dict[str, int]] = Field(default_factory=dict)
    handlers_run: Dict[str, int] = Field(default_factory=dict)  # handler_name -> run count
    success: bool = True
    error_message: Optional[str] = None


class TestCaseResult(BaseModel):
    """Result of a single test case."""

    name: str
    outcome: str  # "passed", "failed", "skipped", "error"
    weight: float = 1.0
    duration: float = 0.0
    message: Optional[str] = None


class TestResult(BaseModel):
    """Aggregated test results for a phase."""

    passed: int = 0
    failed: int = 0
    skipped: int = 0
    errors: int = 0
    total_weight: float = 0.0
    earned_weight: float = 0.0
    details: List[TestCaseResult] = Field(default_factory=list)


class PhaseResult(BaseModel):
    """Complete result for a single phase."""

    phase: str
    converge: ConvergeResult
    tests: TestResult
    score: float = 0.0
    max_score: float = 0.0


class GradeReport(BaseModel):
    """Complete grading report."""

    assignment_id: str
    spec_version: str
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    phases: Dict[str, PhaseResult] = Field(default_factory=dict)
    total_score: float = 0.0
    max_score: float = 0.0
    percentage: float = 0.0
    success: bool = True
    error_message: Optional[str] = None


def calculate_phase_score(tests: TestResult) -> tuple[float, float]:
    """
    Calculate score for a phase based on test results.

    Returns:
        Tuple of (earned_score, max_score)
    """
    if tests.total_weight == 0:
        return 0.0, 0.0

    return tests.earned_weight, tests.total_weight


def calculate_total_score(phases: Dict[str, PhaseResult]) -> tuple[float, float, float]:
    """
    Calculate total score across all phases.

    Returns:
        Tuple of (total_earned, total_max, percentage)
    """
    total_earned = sum(p.score for p in phases.values())
    total_max = sum(p.max_score for p in phases.values())

    if total_max == 0:
        return 0.0, 0.0, 0.0

    percentage = (total_earned / total_max) * 100
    return total_earned, total_max, percentage


def write_handler_runs(
    grading_dir: Path,
    phase: str,
    converge_result: ConvergeResult,
) -> Path:
    """
    Write handler execution data to a file for test verification.

    Args:
        grading_dir: The grading bundle directory
        phase: The phase name (baseline, mutation, idempotence)
        converge_result: The converge result containing handler runs

    Returns:
        Path to the written handler runs file
    """
    handler_runs_dir = grading_dir / ".handler_runs"
    handler_runs_dir.mkdir(parents=True, exist_ok=True)

    handler_file = handler_runs_dir / f"{phase}.json"
    handler_file.write_text(json.dumps(converge_result.handlers_run, indent=2))

    return handler_file
