"""Ansible execution wrapper for HAMMER.

Provides programmatic Ansible playbook execution using ansible-runner.
"""

import json
import os
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional

import ansible_runner
import yaml

from hammer.runner.results import ConvergeResult


def run_playbook(
    playbook_path: Path,
    inventory_path: Path,
    working_dir: Path,
    extra_vars: Optional[Dict[str, Any]] = None,
    extra_vars_file: Optional[Path] = None,
    env_vars: Optional[Dict[str, str]] = None,
    quiet: bool = False,
) -> tuple[ConvergeResult, str]:
    """
    Run an Ansible playbook using ansible-runner.

    Args:
        playbook_path: Path to the playbook file
        inventory_path: Path to the inventory file
        working_dir: Working directory for execution
        extra_vars: Dictionary of extra variables
        extra_vars_file: Path to extra vars YAML file
        env_vars: Environment variables for the run
        quiet: Suppress output

    Returns:
        Tuple of (ConvergeResult, stdout_log)
    """
    # Build command line arguments
    cmdline = [
        "-i", str(inventory_path),
    ]

    if extra_vars:
        cmdline.extend(["-e", json.dumps(extra_vars)])

    if extra_vars_file and extra_vars_file.exists():
        cmdline.extend(["-e", f"@{extra_vars_file}"])

    # Set up environment
    envvars = dict(os.environ)
    envvars["ANSIBLE_HOST_KEY_CHECKING"] = "False"
    envvars["ANSIBLE_RETRY_FILES_ENABLED"] = "False"
    if env_vars:
        envvars.update(env_vars)

    # Create a temporary directory for ansible-runner artifacts
    with tempfile.TemporaryDirectory() as artifact_dir:
        # Run the playbook
        runner = ansible_runner.run(
            private_data_dir=str(working_dir),
            playbook=str(playbook_path),
            cmdline=" ".join(cmdline),
            envvars=envvars,
            quiet=quiet,
            artifact_dir=artifact_dir,
        )

        # Parse the results
        result = parse_runner_result(runner)

        # Capture stdout
        stdout = runner.stdout.read() if runner.stdout else ""

        return result, stdout


def parse_runner_result(runner: ansible_runner.Runner) -> ConvergeResult:
    """
    Parse ansible-runner result into ConvergeResult.

    Args:
        runner: The ansible-runner Runner object

    Returns:
        ConvergeResult with parsed stats
    """
    # Check for overall success
    success = runner.status == "successful"
    error_message = None

    if runner.status == "failed":
        error_message = "Playbook execution failed"
    elif runner.status == "timeout":
        error_message = "Playbook execution timed out"

    # Parse play recap from stats
    stats = runner.stats or {}
    play_recap: Dict[str, Dict[str, int]] = {}

    # Aggregate stats across all hosts
    totals = {
        "ok": 0,
        "changed": 0,
        "failed": 0,
        "unreachable": 0,
        "skipped": 0,
        "rescued": 0,
        "ignored": 0,
    }

    for host, host_stats in stats.items():
        play_recap[host] = {
            "ok": host_stats.get("ok", 0),
            "changed": host_stats.get("changed", 0),
            "failures": host_stats.get("failures", 0),
            "unreachable": host_stats.get("unreachable", 0),
            "skipped": host_stats.get("skipped", 0),
            "rescued": host_stats.get("rescued", 0),
            "ignored": host_stats.get("ignored", 0),
        }
        totals["ok"] += host_stats.get("ok", 0)
        totals["changed"] += host_stats.get("changed", 0)
        totals["failed"] += host_stats.get("failures", 0)
        totals["unreachable"] += host_stats.get("unreachable", 0)
        totals["skipped"] += host_stats.get("skipped", 0)
        totals["rescued"] += host_stats.get("rescued", 0)
        totals["ignored"] += host_stats.get("ignored", 0)

    return ConvergeResult(
        ok=totals["ok"],
        changed=totals["changed"],
        failed=totals["failed"],
        unreachable=totals["unreachable"],
        skipped=totals["skipped"],
        rescued=totals["rescued"],
        ignored=totals["ignored"],
        play_recap=play_recap,
        success=success,
        error_message=error_message,
    )


def check_idempotence(result: ConvergeResult) -> tuple[bool, str]:
    """
    Check if a converge result indicates idempotence.

    An idempotent run should have changed=0 and no failures.

    Args:
        result: The converge result to check

    Returns:
        Tuple of (is_idempotent, message)
    """
    if not result.success:
        return False, f"Playbook failed: {result.error_message}"

    if result.failed > 0:
        return False, f"Playbook had {result.failed} failed tasks"

    if result.unreachable > 0:
        return False, f"Playbook had {result.unreachable} unreachable hosts"

    if result.changed > 0:
        return False, f"Playbook had {result.changed} changed tasks (expected 0 for idempotence)"

    return True, "Playbook is idempotent"
