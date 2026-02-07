"""HAMMER Reboot Module.

Provides functionality to reboot nodes after converge and wait for SSH availability.
"""

import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

import yaml


@dataclass
class RebootResult:
    """Result of a reboot operation for a single node."""
    success: bool
    duration: float
    error: Optional[str] = None


def reboot_nodes(
    inventory_path: Path,
    nodes: Optional[List[str]],
    timeout: int = 120,
    poll_interval: int = 5,
) -> Dict[str, RebootResult]:
    """
    Reboot specified nodes and wait for SSH to come back.

    Args:
        inventory_path: Path to the Ansible inventory file
        nodes: List of node names to reboot, or None for all nodes
        timeout: Maximum seconds to wait for SSH per node
        poll_interval: Seconds between SSH availability checks

    Returns:
        Dict mapping node name to RebootResult
    """
    results = {}

    # Get node list from inventory if not specified
    if nodes is None:
        nodes = _get_all_nodes_from_inventory(inventory_path)

    for node in nodes:
        results[node] = _reboot_single_node(
            inventory_path, node, timeout, poll_interval
        )

    return results


def _reboot_single_node(
    inventory_path: Path,
    node: str,
    timeout: int,
    poll_interval: int,
) -> RebootResult:
    """
    Reboot a single node via Ansible and wait for it to come back.

    Args:
        inventory_path: Path to the Ansible inventory file
        node: Name of the node to reboot
        timeout: Maximum seconds to wait for SSH
        poll_interval: Seconds between SSH availability checks

    Returns:
        RebootResult with success status and timing info
    """
    start_time = time.time()

    # Send reboot command using Ansible's async mode
    # -B 1 = background with 1 second timeout (fire and forget)
    # -P 0 = don't poll for result
    try:
        subprocess.run(
            [
                "ansible", node,
                "-i", str(inventory_path),
                "-m", "shell",
                "-a", "sleep 2 && sudo reboot",
                "-B", "1",
                "-P", "0",
            ],
            timeout=30,
            capture_output=True,
        )
    except subprocess.TimeoutExpired:
        # Expected - connection may drop before command completes
        pass
    except Exception as e:
        return RebootResult(
            success=False,
            duration=time.time() - start_time,
            error=f"Failed to send reboot command: {e}",
        )

    # Phase 1: Wait for SSH to go DOWN (confirms reboot initiated)
    ssh_went_down = False
    for _ in range(30):
        if not _check_ssh_available(inventory_path, node):
            ssh_went_down = True
            break
        time.sleep(1)

    if not ssh_went_down:
        return RebootResult(
            success=False,
            duration=time.time() - start_time,
            error=f"SSH never went down on {node} - reboot may not have initiated",
        )

    # Phase 2: Wait for SSH to come back
    elapsed = time.time() - start_time
    while elapsed < timeout:
        if _check_ssh_available(inventory_path, node):
            return RebootResult(
                success=True,
                duration=time.time() - start_time,
            )
        time.sleep(poll_interval)
        elapsed = time.time() - start_time

    return RebootResult(
        success=False,
        duration=timeout,
        error=f"SSH did not become available within {timeout}s",
    )


def _check_ssh_available(inventory_path: Path, node: str) -> bool:
    """
    Check if SSH is available on a node using Ansible ping.

    Args:
        inventory_path: Path to the Ansible inventory file
        node: Name of the node to check

    Returns:
        True if node is reachable via SSH
    """
    try:
        result = subprocess.run(
            [
                "ansible", node,
                "-i", str(inventory_path),
                "-m", "ping",
            ],
            timeout=10,
            capture_output=True,
        )
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        return False
    except Exception:
        return False


def _get_all_nodes_from_inventory(inventory_path: Path) -> List[str]:
    """
    Get all node names from an Ansible inventory file.

    Args:
        inventory_path: Path to the Ansible inventory file (YAML format)

    Returns:
        List of node names
    """
    nodes = []

    try:
        with open(inventory_path, "r") as f:
            inventory = yaml.safe_load(f)

        if not inventory:
            return nodes

        # Handle YAML inventory format
        # Typical structure: all.hosts or all.children.<group>.hosts
        if "all" in inventory:
            all_section = inventory["all"]

            # Direct hosts under 'all'
            if "hosts" in all_section:
                nodes.extend(all_section["hosts"].keys())

            # Hosts in child groups
            if "children" in all_section:
                for group_name, group_data in all_section["children"].items():
                    if isinstance(group_data, dict) and "hosts" in group_data:
                        nodes.extend(group_data["hosts"].keys())

    except Exception:
        # If we can't parse the inventory, return empty list
        # The reboot will fail gracefully
        pass

    return list(set(nodes))  # Remove duplicates
