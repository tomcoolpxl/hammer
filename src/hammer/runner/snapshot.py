"""Snapshot extraction for HAMMER grading.

Generates and runs playbooks to collect system state.
"""

from pathlib import Path
from typing import Any, Dict, List, Set

from jinja2 import Environment, FileSystemLoader

from hammer.spec import HammerSpec
from hammer.plan import ExecutionPlan


TEMPLATES_DIR = Path(__file__).parent / "templates"


def _get_env() -> Environment:
    """Get Jinja2 environment with templates."""
    return Environment(
        loader=FileSystemLoader(TEMPLATES_DIR),
        keep_trailing_newline=True,
    )


def get_files_to_check(spec: HammerSpec, plan: ExecutionPlan) -> List[str]:
    """
    Extract list of files that need to be checked from spec.

    Args:
        spec: The HAMMER spec
        plan: The execution plan

    Returns:
        List of file paths to check
    """
    files: Set[str] = set()

    # Get files from behavioral contracts
    if spec.behavioral_contracts and spec.behavioral_contracts.files:
        for fc in spec.behavioral_contracts.files:
            for item in fc.items:
                files.add(item.path)

    # Get files from binding targets
    for var in spec.variable_contracts:
        for binding in var.binding_targets:
            target = binding.target
            if hasattr(target, "path"):
                files.add(target.path)

    return sorted(files)


def render_snapshot_playbook(
    spec: HammerSpec,
    plan: ExecutionPlan,
    phase: str,
    snapshot_dir: Path,
) -> str:
    """
    Render a snapshot extraction playbook.

    Args:
        spec: The HAMMER spec
        plan: The execution plan
        phase: The phase name
        snapshot_dir: Directory to store snapshots

    Returns:
        Rendered playbook YAML as string
    """
    env = _get_env()
    template = env.get_template("snapshot_playbook.yml.j2")

    files_to_check = get_files_to_check(spec, plan)

    return template.render(
        assignment_id=spec.assignment_id,
        phase=phase,
        files_to_check=files_to_check,
        snapshot_dir=str(snapshot_dir),
    )


def write_snapshot_playbook(
    spec: HammerSpec,
    plan: ExecutionPlan,
    phase: str,
    output_dir: Path,
) -> Path:
    """
    Write a snapshot playbook to disk.

    Args:
        spec: The HAMMER spec
        plan: The execution plan
        phase: The phase name
        output_dir: Directory to write playbook

    Returns:
        Path to the written playbook
    """
    snapshot_dir = output_dir / "snapshots" / phase
    snapshot_dir.mkdir(parents=True, exist_ok=True)

    content = render_snapshot_playbook(spec, plan, phase, snapshot_dir)

    playbook_path = output_dir / f"snapshot_{phase}.yml"
    playbook_path.write_text(content)

    return playbook_path
