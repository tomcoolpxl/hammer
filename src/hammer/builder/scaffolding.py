"""Scaffolding generation for HAMMER assignments.

Creates directory structure and README files.
"""

from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from hammer.spec import HammerSpec
from hammer.builder.network import NetworkPlan


TEMPLATES_DIR = Path(__file__).parent / "templates"


def _get_env() -> Environment:
    """Get Jinja2 environment with templates."""
    return Environment(
        loader=FileSystemLoader(TEMPLATES_DIR),
        keep_trailing_newline=True,
    )


def render_readme(spec: HammerSpec, network: NetworkPlan) -> str:
    """
    Render the student README.md file.

    Args:
        spec: The HAMMER spec
        network: The resolved network plan

    Returns:
        Rendered README content
    """
    env = _get_env()
    template = env.get_template("README.md.j2")

    return template.render(
        assignment_id=spec.assignment_id,
        assignment_version=spec.assignment_version,
        nodes=spec.topology.nodes,
        network=network,
        playbook_path=spec.entrypoints.playbook_path,
    )


def create_student_bundle_structure(output_dir: Path) -> None:
    """
    Create the student bundle directory structure.

    Args:
        output_dir: Root directory for student bundle
    """
    dirs = [
        output_dir,
        output_dir / "inventory",
        output_dir / "group_vars",
        output_dir / "host_vars",
        output_dir / "roles",
    ]

    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)


def create_grading_bundle_structure(output_dir: Path) -> None:
    """
    Create the grading bundle directory structure.

    Args:
        output_dir: Root directory for grading bundle
    """
    dirs = [
        output_dir,
        output_dir / "inventory",
        output_dir / "group_vars",
        output_dir / "host_vars",
        output_dir / "overlays",
        output_dir / "overlays" / "baseline",
        output_dir / "overlays" / "baseline" / "group_vars",
        output_dir / "overlays" / "baseline" / "host_vars",
        output_dir / "overlays" / "mutation",
        output_dir / "overlays" / "mutation" / "group_vars",
        output_dir / "overlays" / "mutation" / "host_vars",
    ]

    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
