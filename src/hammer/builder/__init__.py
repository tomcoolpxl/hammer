"""HAMMER Builder - Artifact generation for assignments.

This module orchestrates the generation of student and grading bundles
from a validated spec and execution plan.
"""

import shutil
from pathlib import Path
from typing import Dict, Optional

from hammer.spec import HammerSpec
from hammer.plan import ExecutionPlan, build_execution_plan
from hammer.builder.network import NetworkPlan, generate_network_plan
from hammer.builder.vagrantfile import render_vagrantfile
from hammer.builder.inventory import (
    render_student_inventory,
    render_ansible_cfg,
    write_student_group_vars,
    write_student_host_vars,
    write_grading_inventory,
    write_grading_group_vars,
    write_grading_host_vars,
    write_grading_phase_overlays,
)
from hammer.builder.lock import (
    LockArtifact,
    compute_file_checksum,
    create_lock_artifact,
    write_lock_artifact,
)
from hammer.builder.scaffolding import (
    render_readme,
    create_student_bundle_structure,
    create_grading_bundle_structure,
)
from hammer.testgen import generate_tests


__all__ = [
    "build_assignment",
    "init_assignment",
    "NetworkPlan",
    "LockArtifact",
]


def init_assignment(
    spec: HammerSpec,
    output_dir: Path,
    box_version: str = "generic/alma9",
) -> NetworkPlan:
    """
    Generate minimal infrastructure files for manual development.

    Creates only the Vagrantfile, inventory, ansible.cfg, and host_vars
    needed to `vagrant up` and iterate on a playbook before finalizing
    the full spec with contracts.

    Args:
        spec: Validated HAMMER spec
        output_dir: Directory to write files into
        box_version: Vagrant box to use (default: generic/alma9)

    Returns:
        NetworkPlan with resolved IPs for reference
    """
    network = generate_network_plan(spec)

    # Create minimal directory structure
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "inventory").mkdir(exist_ok=True)
    (output_dir / "host_vars").mkdir(exist_ok=True)
    (output_dir / "roles").mkdir(exist_ok=True)

    # Vagrantfile
    vagrantfile_content = render_vagrantfile(spec, network, box_version)
    with open(output_dir / "Vagrantfile", "w") as f:
        f.write(vagrantfile_content)

    # Inventory
    inventory_content = render_student_inventory(spec, network)
    with open(output_dir / "inventory" / "hosts.yml", "w") as f:
        f.write(inventory_content)

    # ansible.cfg
    ansible_cfg_content = render_ansible_cfg(
        inventory_path="inventory/hosts.yml",
        roles_path="roles",
    )
    with open(output_dir / "ansible.cfg", "w") as f:
        f.write(ansible_cfg_content)

    # Host vars (ansible_host IPs)
    write_student_host_vars(spec, network, output_dir)

    return network


def build_assignment(
    spec: HammerSpec,
    output_dir: Path,
    box_version: str = "generic/alma9",
    spec_dir: Optional[Path] = None,
) -> LockArtifact:
    """
    Build student and grading bundles from a spec.

    Creates:
    - student_bundle/ - Infrastructure for students
    - grading_bundle/ - Infrastructure + overlays for grading
    - lock.json - Reproducibility artifact

    Args:
        spec: Validated HAMMER spec
        output_dir: Root directory for output
        box_version: Vagrant box to use (default: generic/alma9)
        spec_dir: Directory containing the spec file (for provided_files resolution)

    Returns:
        LockArtifact containing checksums and versions
    """
    # Generate execution plan
    plan = build_execution_plan(spec)

    # Generate network plan
    network = generate_network_plan(spec)

    # Track checksums for lock artifact
    checksums: Dict[str, str] = {}

    # Create output directories
    output_dir.mkdir(parents=True, exist_ok=True)
    student_dir = output_dir / "student_bundle"
    grading_dir = output_dir / "grading_bundle"

    # Build student bundle
    _build_student_bundle(spec, plan, network, student_dir, box_version, checksums, spec_dir)

    # Build grading bundle
    _build_grading_bundle(spec, plan, network, grading_dir, box_version, checksums)

    # Create lock artifact
    lock = create_lock_artifact(spec, network, box_version, checksums)

    # Write lock.json
    lock_path = output_dir / "lock.json"
    write_lock_artifact(lock, lock_path)

    return lock


def _build_student_bundle(
    spec: HammerSpec,
    plan: ExecutionPlan,
    network: NetworkPlan,
    output_dir: Path,
    box_version: str,
    checksums: Dict[str, str],
    spec_dir: Optional[Path] = None,
) -> None:
    """Build the student bundle."""
    create_student_bundle_structure(output_dir)

    # Vagrantfile
    vagrantfile_content = render_vagrantfile(spec, network, box_version)
    vagrantfile_path = output_dir / "Vagrantfile"
    with open(vagrantfile_path, "w") as f:
        f.write(vagrantfile_content)
    checksums["student_bundle/Vagrantfile"] = compute_file_checksum(vagrantfile_content)

    # Inventory
    inventory_content = render_student_inventory(spec, network)
    inventory_path = output_dir / "inventory" / "hosts.yml"
    with open(inventory_path, "w") as f:
        f.write(inventory_content)
    checksums["student_bundle/inventory/hosts.yml"] = compute_file_checksum(
        inventory_content
    )

    # ansible.cfg
    ansible_cfg_content = render_ansible_cfg(
        inventory_path="inventory/hosts.yml",
        roles_path="roles",
    )
    ansible_cfg_path = output_dir / "ansible.cfg"
    with open(ansible_cfg_path, "w") as f:
        f.write(ansible_cfg_content)
    checksums["student_bundle/ansible.cfg"] = compute_file_checksum(ansible_cfg_content)

    # Group vars
    write_student_group_vars(spec, plan, output_dir)

    # Host vars
    write_student_host_vars(spec, network, output_dir)

    # README
    readme_content = render_readme(spec, network)
    readme_path = output_dir / "README.md"
    with open(readme_path, "w") as f:
        f.write(readme_content)
    checksums["student_bundle/README.md"] = compute_file_checksum(readme_content)

    # Copy provided_files if specified
    if spec.entrypoints.provided_files and spec_dir:
        _copy_provided_files(spec, spec_dir, output_dir, checksums)


def _copy_provided_files(
    spec: HammerSpec,
    spec_dir: Path,
    output_dir: Path,
    checksums: Dict[str, str],
) -> None:
    """Copy provided_files from spec directory to student bundle."""
    from hammer.utils import validate_path_within

    for pf in spec.entrypoints.provided_files:
        src = validate_path_within(Path(pf.source), spec_dir)
        dst = validate_path_within(Path(pf.destination), output_dir)

        if not src.exists():
            raise FileNotFoundError(
                f"Provided file not found: {src} (source: {pf.source})"
            )

        # Create parent directories
        dst.parent.mkdir(parents=True, exist_ok=True)

        # Copy file or directory
        if src.is_dir():
            if dst.exists():
                shutil.rmtree(dst)
            shutil.copytree(src, dst)
        else:
            shutil.copy2(src, dst)
            # Add checksum for file
            with open(src, "r") as f:
                content = f.read()
            checksums[f"student_bundle/{pf.destination}"] = compute_file_checksum(content)


def _build_grading_bundle(
    spec: HammerSpec,
    plan: ExecutionPlan,
    network: NetworkPlan,
    output_dir: Path,
    box_version: str,
    checksums: Dict[str, str],
) -> None:
    """Build the grading bundle."""
    create_grading_bundle_structure(output_dir)

    # Vagrantfile (same as student)
    vagrantfile_content = render_vagrantfile(spec, network, box_version)
    vagrantfile_path = output_dir / "Vagrantfile"
    with open(vagrantfile_path, "w") as f:
        f.write(vagrantfile_content)
    checksums["grading_bundle/Vagrantfile"] = compute_file_checksum(vagrantfile_content)

    # Inventory
    write_grading_inventory(spec, network, output_dir)

    # ansible.cfg
    ansible_cfg_content = render_ansible_cfg(
        inventory_path="inventory/hosts.yml",
    )
    ansible_cfg_path = output_dir / "ansible.cfg"
    with open(ansible_cfg_path, "w") as f:
        f.write(ansible_cfg_content)
    checksums["grading_bundle/ansible.cfg"] = compute_file_checksum(ansible_cfg_content)

    # Group vars (base)
    write_grading_group_vars(spec, plan, output_dir)

    # Host vars
    write_grading_host_vars(spec, network, output_dir)

    # Phase overlays
    write_grading_phase_overlays(spec, plan, output_dir)

    # Vault password file (if vault is configured)
    if spec.vault:
        import os
        vault_pass_path = output_dir / ".vault_pass"
        fd = os.open(str(vault_pass_path), os.O_CREAT | os.O_WRONLY | os.O_EXCL, 0o600)
        try:
            os.write(fd, spec.vault.vault_password.encode())
        finally:
            os.close(fd)
        checksums["grading_bundle/.vault_pass"] = compute_file_checksum(spec.vault.vault_password)

    # Generate tests
    generate_tests(spec, plan, network, output_dir)
