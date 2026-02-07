"""Prerequisite checks for HAMMER commands.

Verifies that required external tools are available before running commands.
"""

import shutil
import subprocess
from typing import List


def check_prerequisites(command: str) -> List[str]:
    """Check that required tools are available for a HAMMER command.

    Args:
        command: The HAMMER subcommand ('validate', 'init', 'build', 'grade').

    Returns:
        List of missing tool messages. Empty list means all prerequisites met.
    """
    missing = []

    if command in ("build", "grade"):
        if not shutil.which("ansible-playbook"):
            missing.append(
                "ansible-playbook not found. "
                "Install Ansible: pip install ansible"
            )

    if command == "grade":
        if not shutil.which("vagrant"):
            missing.append(
                "vagrant not found. "
                "Install Vagrant: https://developer.hashicorp.com/vagrant/downloads"
            )
        else:
            # Check for libvirt plugin
            try:
                result = subprocess.run(
                    ["vagrant", "plugin", "list"],
                    capture_output=True, text=True, timeout=10,
                )
                if "vagrant-libvirt" not in result.stdout:
                    missing.append(
                        "vagrant-libvirt plugin not installed. "
                        "Install it: vagrant plugin install vagrant-libvirt"
                    )
            except (subprocess.TimeoutExpired, OSError):
                pass  # Can't check, don't block

    return missing
