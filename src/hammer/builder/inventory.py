"""Inventory generation for HAMMER assignments.

Generates student and grading inventory files with group/host vars.
"""

from pathlib import Path
from typing import Any, Dict, List

import yaml
from jinja2 import Environment, FileSystemLoader

from hammer.spec import HammerSpec, Node
from hammer.plan import ExecutionPlan
from hammer.builder.network import NetworkPlan
from hammer.constants import OVERLAY_PHASES


TEMPLATES_DIR = Path(__file__).parent / "templates"


def _get_env() -> Environment:
    """Get Jinja2 environment with templates."""
    return Environment(
        loader=FileSystemLoader(TEMPLATES_DIR),
        keep_trailing_newline=True,
    )


def _group_nodes_by_group(nodes: List[Node]) -> Dict[str, List[Node]]:
    """Group nodes by their group memberships."""
    groups: Dict[str, List[Node]] = {}
    for node in nodes:
        for group in node.groups:
            if group not in groups:
                groups[group] = []
            groups[group].append(node)
    return groups


def render_student_inventory(spec: HammerSpec, network: NetworkPlan) -> str:
    """
    Render the student inventory YAML file.

    Args:
        spec: The HAMMER spec
        network: The resolved network plan

    Returns:
        Rendered inventory YAML as a string
    """
    env = _get_env()
    template = env.get_template("student_inventory.yml.j2")

    groups = _group_nodes_by_group(spec.topology.nodes)

    return template.render(
        assignment_id=spec.assignment_id,
        groups=groups,
        network=network,
        domain=spec.topology.domain,
    )


def write_student_group_vars(
    spec: HammerSpec,
    plan: ExecutionPlan,
    output_dir: Path,
) -> None:
    """
    Write student group_vars files.

    Uses baseline phase variables as student defaults.

    Args:
        spec: The HAMMER spec
        plan: The execution plan with resolved variables
        output_dir: Directory to write group_vars/ into
    """
    group_vars_dir = output_dir / "group_vars"
    group_vars_dir.mkdir(parents=True, exist_ok=True)

    # Get baseline variables for student defaults
    baseline_vars = plan.variables["baseline"]

    # Write defaults for each variable contract as group_vars/all.yml
    all_vars: Dict[str, Any] = {}
    for var in (spec.variable_contracts or []):
        all_vars[var.name] = var.defaults.student

    if all_vars:
        with open(group_vars_dir / "all.yml", "w") as f:
            yaml.dump(all_vars, f, default_flow_style=False)

    # Write group-specific vars from baseline overlay
    if baseline_vars.group_vars:
        for group_name, group_data in baseline_vars.group_vars.items():
            if group_data:
                with open(group_vars_dir / f"{group_name}.yml", "w") as f:
                    yaml.dump(group_data, f, default_flow_style=False)


def write_student_host_vars(
    spec: HammerSpec,
    network: NetworkPlan,
    output_dir: Path,
) -> None:
    """
    Write student host_vars files.

    Args:
        spec: The HAMMER spec
        network: The resolved network plan
        output_dir: Directory to write host_vars/ into
    """
    host_vars_dir = output_dir / "host_vars"
    host_vars_dir.mkdir(parents=True, exist_ok=True)

    domain = spec.topology.domain

    # Write host-specific network info
    for node in spec.topology.nodes:
        host_data = {
            "ansible_host": network.node_ip_map[node.name],
        }
        # Use FQDN for filename if domain is set (to match inventory)
        if domain:
            filename = f"{node.name}.{domain}.yml"
        else:
            filename = f"{node.name}.yml"
        with open(host_vars_dir / filename, "w") as f:
            yaml.dump(host_data, f, default_flow_style=False)


def render_ansible_cfg(
    inventory_path: str = "inventory/hosts.yml",
    roles_path: str | None = None,
) -> str:
    """
    Render ansible.cfg file.

    Args:
        inventory_path: Path to inventory file
        roles_path: Optional roles path

    Returns:
        Rendered ansible.cfg content
    """
    env = _get_env()
    template = env.get_template("ansible.cfg.j2")
    return template.render(
        inventory_path=inventory_path,
        roles_path=roles_path,
    )


def write_grading_inventory(
    spec: HammerSpec,
    network: NetworkPlan,
    output_dir: Path,
) -> None:
    """
    Write grading inventory structure.

    Args:
        spec: The HAMMER spec
        network: The resolved network plan
        output_dir: Grading bundle directory
    """
    inventory_dir = output_dir / "inventory"
    inventory_dir.mkdir(parents=True, exist_ok=True)

    # Write main hosts.yml
    inventory_content = render_student_inventory(spec, network)
    with open(inventory_dir / "hosts.yml", "w") as f:
        f.write(inventory_content)


def write_grading_group_vars(
    spec: HammerSpec,
    plan: ExecutionPlan,
    output_dir: Path,
) -> None:
    """
    Write grading group_vars files (shared across phases).

    Args:
        spec: The HAMMER spec
        plan: The execution plan
        output_dir: Grading bundle directory
    """
    group_vars_dir = output_dir / "group_vars"
    group_vars_dir.mkdir(parents=True, exist_ok=True)

    # Write empty all.yml as placeholder
    with open(group_vars_dir / "all.yml", "w") as f:
        yaml.dump({}, f, default_flow_style=False)


def write_grading_host_vars(
    spec: HammerSpec,
    network: NetworkPlan,
    output_dir: Path,
) -> None:
    """
    Write grading host_vars files.

    Args:
        spec: The HAMMER spec
        network: The resolved network plan
        output_dir: Grading bundle directory
    """
    host_vars_dir = output_dir / "host_vars"
    host_vars_dir.mkdir(parents=True, exist_ok=True)

    domain = spec.topology.domain

    for node in spec.topology.nodes:
        host_data = {
            "ansible_host": network.node_ip_map[node.name],
            "ansible_user": "vagrant",
        }
        # Use FQDN for filename if domain is set (to match inventory)
        if domain:
            filename = f"{node.name}.{domain}.yml"
        else:
            filename = f"{node.name}.yml"
        with open(host_vars_dir / filename, "w") as f:
            yaml.dump(host_data, f, default_flow_style=False)


def write_grading_phase_overlays(
    spec: HammerSpec,
    plan: ExecutionPlan,
    output_dir: Path,
) -> None:
    """
    Write phase-specific overlay directories for grading.

    Creates overlays/baseline/ and overlays/mutation/ with:
    - group_vars/
    - extra_vars.yml

    Args:
        spec: The HAMMER spec
        plan: The execution plan with resolved variables
        output_dir: Grading bundle directory
    """
    overlays_dir = output_dir / "overlays"

    for phase_name in OVERLAY_PHASES:
        phase_dir = overlays_dir / phase_name
        phase_dir.mkdir(parents=True, exist_ok=True)

        phase_vars = plan.variables[phase_name]

        # Write group_vars for this phase
        phase_group_vars_dir = phase_dir / "group_vars"
        phase_group_vars_dir.mkdir(exist_ok=True)

        if phase_vars.group_vars:
            for group_name, group_data in phase_vars.group_vars.items():
                if group_data:
                    with open(phase_group_vars_dir / f"{group_name}.yml", "w") as f:
                        yaml.dump(group_data, f, default_flow_style=False)

        # Write all.yml placeholder if no group-specific vars
        if not phase_vars.group_vars:
            with open(phase_group_vars_dir / "all.yml", "w") as f:
                yaml.dump({}, f, default_flow_style=False)

        # Write host_vars for this phase
        phase_host_vars_dir = phase_dir / "host_vars"
        phase_host_vars_dir.mkdir(exist_ok=True)

        if phase_vars.host_vars:
            for host_name, host_data in phase_vars.host_vars.items():
                if host_data:
                    with open(phase_host_vars_dir / f"{host_name}.yml", "w") as f:
                        yaml.dump(host_data, f, default_flow_style=False)

        # Write extra_vars.yml
        extra_vars = phase_vars.extra_vars if phase_vars.extra_vars else {}
        with open(phase_dir / "extra_vars.yml", "w") as f:
            yaml.dump(extra_vars, f, default_flow_style=False)
