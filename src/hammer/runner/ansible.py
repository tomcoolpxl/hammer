"""Ansible execution wrapper for HAMMER.

Provides programmatic Ansible playbook execution.
"""

import json
import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any, Dict, Optional

from hammer.runner.results import ConvergeResult


def find_ansible_playbook() -> str:
    """Find the ansible-playbook executable."""
    import sys
    
    # Check current python's bin dir (useful when running in a venv)
    venv_bin = Path(sys.executable).parent / "ansible-playbook"
    
    # Check common locations
    locations = [
        str(venv_bin) if venv_bin.exists() else None,
        shutil.which("ansible-playbook"),
        os.path.expanduser("~/.local/bin/ansible-playbook"),
        "/usr/bin/ansible-playbook",
        "/usr/local/bin/ansible-playbook",
    ]

    for loc in locations:
        if loc and os.path.exists(loc):
            return loc

    raise FileNotFoundError("ansible-playbook not found in PATH or common locations")


def run_playbook(
    playbook_path: Path,
    inventory_path: Path,
    working_dir: Path,
    extra_vars: Optional[Dict[str, Any]] = None,
    extra_vars_file: Optional[Path] = None,
    vault_password_file: Optional[Path] = None,
    env_vars: Optional[Dict[str, str]] = None,
    quiet: bool = False,
    timeout: int = 600,
) -> tuple[ConvergeResult, str]:
    """
    Run an Ansible playbook using subprocess.

    Args:
        playbook_path: Path to the playbook file
        inventory_path: Path to the inventory file
        working_dir: Working directory for execution
        extra_vars: Dictionary of extra variables
        extra_vars_file: Path to extra vars YAML file
        vault_password_file: Path to vault password file
        env_vars: Environment variables for the run
        quiet: Suppress output
        timeout: Timeout in seconds

    Returns:
        Tuple of (ConvergeResult, stdout_log)
    """
    try:
        ansible_playbook = find_ansible_playbook()
    except FileNotFoundError as e:
        return ConvergeResult(success=False, error_message=str(e)), str(e)

    # Build command
    cmd = [
        ansible_playbook,
        str(playbook_path),
        "-i", str(inventory_path),
    ]

    if extra_vars:
        cmd.extend(["-e", json.dumps(extra_vars)])

    if extra_vars_file and extra_vars_file.exists():
        cmd.extend(["-e", f"@{extra_vars_file}"])

    if vault_password_file and vault_password_file.exists():
        cmd.extend(["--vault-password-file", str(vault_password_file)])

    # Set up environment
    envvars = dict(os.environ)
    envvars["ANSIBLE_HOST_KEY_CHECKING"] = "False"
    envvars["ANSIBLE_RETRY_FILES_ENABLED"] = "False"
    envvars["ANSIBLE_FORCE_COLOR"] = "False"

    # Ensure ~/.local/bin is in PATH
    local_bin = os.path.expanduser("~/.local/bin")
    if local_bin not in envvars.get("PATH", ""):
        envvars["PATH"] = f"{local_bin}:{envvars.get('PATH', '')}"

    if env_vars:
        envvars.update(env_vars)

    # Run the playbook
    try:
        result = subprocess.run(
            cmd,
            cwd=str(working_dir),
            env=envvars,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        stdout = result.stdout + result.stderr
        success = result.returncode == 0
        error_message = None if success else f"Exit code: {result.returncode}"

    except subprocess.TimeoutExpired as e:
        stdout = (e.stdout or b"").decode() + (e.stderr or b"").decode()
        success = False
        error_message = f"Playbook timed out after {timeout} seconds"

    except Exception as e:
        stdout = str(e)
        success = False
        error_message = str(e)

    # Parse play recap from stdout
    converge_result = parse_play_recap(stdout, success, error_message)

    return converge_result, stdout


def parse_play_recap(
    stdout: str,
    success: bool,
    error_message: Optional[str],
) -> ConvergeResult:
    """
    Parse play recap from ansible-playbook stdout.

    Args:
        stdout: The stdout from ansible-playbook
        success: Whether the playbook succeeded
        error_message: Error message if failed

    Returns:
        ConvergeResult with parsed stats
    """
    # Parse PLAY RECAP section
    # Format: hostname : ok=N changed=N unreachable=N failed=N skipped=N rescued=N ignored=N
    recap_pattern = re.compile(
        r"^(\S+)\s+:\s+"
        r"ok=(\d+)\s+"
        r"changed=(\d+)\s+"
        r"unreachable=(\d+)\s+"
        r"failed=(\d+)"
        r"(?:\s+skipped=(\d+))?"
        r"(?:\s+rescued=(\d+))?"
        r"(?:\s+ignored=(\d+))?",
        re.MULTILINE,
    )

    play_recap: Dict[str, Dict[str, int]] = {}
    totals = {
        "ok": 0,
        "changed": 0,
        "failed": 0,
        "unreachable": 0,
        "skipped": 0,
        "rescued": 0,
        "ignored": 0,
    }

    for match in recap_pattern.finditer(stdout):
        host = match.group(1)
        ok = int(match.group(2))
        changed = int(match.group(3))
        unreachable = int(match.group(4))
        failed = int(match.group(5))
        skipped = int(match.group(6) or 0)
        rescued = int(match.group(7) or 0)
        ignored = int(match.group(8) or 0)

        play_recap[host] = {
            "ok": ok,
            "changed": changed,
            "unreachable": unreachable,
            "failures": failed,
            "skipped": skipped,
            "rescued": rescued,
            "ignored": ignored,
        }

        totals["ok"] += ok
        totals["changed"] += changed
        totals["unreachable"] += unreachable
        totals["failed"] += failed
        totals["skipped"] += skipped
        totals["rescued"] += rescued
        totals["ignored"] += ignored

    # Parse handler runs
    # Format: RUNNING HANDLER [handler name] ***
    handlers_run = parse_handler_runs(stdout)

    return ConvergeResult(
        ok=totals["ok"],
        changed=totals["changed"],
        failed=totals["failed"],
        unreachable=totals["unreachable"],
        skipped=totals["skipped"],
        rescued=totals["rescued"],
        ignored=totals["ignored"],
        play_recap=play_recap,
        handlers_run=handlers_run,
        success=success,
        error_message=error_message,
    )


def parse_handler_runs(stdout: str) -> Dict[str, int]:
    """
    Parse handler execution from ansible-playbook stdout.

    Args:
        stdout: The stdout from ansible-playbook

    Returns:
        Dict mapping handler names to run counts
    """
    # Match RUNNING HANDLER lines
    # Format: RUNNING HANDLER [role_name : handler_name] ***
    # or: RUNNING HANDLER [handler_name] ***
    # Note: [^\]\n]+ excludes ] and newlines to prevent matching across lines
    handler_pattern = re.compile(
        r"RUNNING HANDLER \[([^\]\n]+)\]",
        re.MULTILINE,
    )

    handlers_run: Dict[str, int] = {}
    for match in handler_pattern.finditer(stdout):
        handler_full = match.group(1)
        # Strip role prefix if present (e.g., "nginx : restart nginx" -> "restart nginx")
        if " : " in handler_full:
            handler_name = handler_full.split(" : ", 1)[1].strip()
        else:
            handler_name = handler_full.strip()
        handlers_run[handler_name] = handlers_run.get(handler_name, 0) + 1

    return handlers_run


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
