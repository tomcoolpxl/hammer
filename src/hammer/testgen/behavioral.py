"""Behavioral test generation for HAMMER.

Generates tests for packages, services, files, and firewall.
"""

import re
from typing import Any, Dict, List

from hammer.plan import (
    PhaseContractPlan,
    PackageCheck,
    PipPackageCheck,
    ServiceCheck,
    UserCheck,
    FileCheck,
    FirewallCheck,
    HttpEndpointCheck,
)


def _make_safe_name(s: str) -> str:
    """Convert a string to a valid Python identifier."""
    safe = re.sub(r"[^a-zA-Z0-9]", "_", s)
    safe = re.sub(r"^[0-9]+", "", safe)
    safe = re.sub(r"_+", "_", safe)
    return safe.strip("_").lower()


def generate_package_tests(contract: PhaseContractPlan) -> List[Dict[str, Any]]:
    """Generate test data for package checks."""
    tests = []

    for pkg in contract.packages:
        tests.append({
            "name": pkg.name,
            "state": pkg.state,
            "hosts": pkg.host_targets,
            "weight": pkg.weight,
        })

    return tests


def generate_pip_package_tests(contract: PhaseContractPlan) -> List[Dict[str, Any]]:
    """Generate test data for pip package checks."""
    tests = []

    for pkg in contract.pip_packages:
        tests.append({
            "name": pkg.name,
            "state": pkg.state,
            "python": pkg.python,
            "hosts": pkg.host_targets,
            "weight": pkg.weight,
        })

    return tests


def generate_service_tests(contract: PhaseContractPlan) -> List[Dict[str, Any]]:
    """Generate test data for service checks."""
    tests = []

    for svc in contract.services:
        tests.append({
            "name": svc.name,
            "enabled": svc.enabled,
            "running": svc.running,
            "hosts": svc.host_targets,
            "weight": svc.weight,
        })

    return tests


def generate_user_tests(contract: PhaseContractPlan) -> List[Dict[str, Any]]:
    """Generate test data for user checks."""
    tests = []

    for user in contract.users:
        tests.append({
            "name": user.name,
            "exists": user.exists,
            "uid": user.uid,
            "gid": user.gid,
            "home": user.home,
            "shell": user.shell,
            "groups": user.groups,
            "hosts": user.host_targets,
            "weight": user.weight,
        })

    return tests


def generate_file_tests(contract: PhaseContractPlan) -> List[Dict[str, Any]]:
    """Generate test data for file checks."""
    tests = []

    for fc in contract.files:
        file_items = []
        for item in fc.items:
            # Convert mode string to octal integer for Python comparison
            mode = None
            if item.get("mode"):
                mode_str = item["mode"]
                # Handle both "0644" and "644" formats
                if mode_str.startswith("0o"):
                    mode = int(mode_str, 8)
                elif mode_str.startswith("0"):
                    mode = int(mode_str, 8)
                else:
                    mode = int(mode_str, 8)

            file_items.append({
                "path": item["path"],
                "safe_name": _make_safe_name(item["path"]),
                "present": item["present"],
                "is_directory": item.get("is_directory", False),
                "mode": mode,
                "owner": item.get("owner"),
                "group": item.get("group"),
                "content_regex": item.get("content_regex"),
            })

        tests.append({
            "hosts": fc.host_targets,
            "file_items": file_items,
            "weight": fc.weight,
        })

    return tests


def _resolve_port(port_val: Any, resolved_vars: Dict[str, Any]) -> Any:
    """Resolve a port value, handling variable references."""
    # Check if it's a PortRefVar (has a 'var' attribute)
    if hasattr(port_val, "var"):
        var_name = port_val.var
        return resolved_vars.get(var_name, port_val)

    # Check if it's a dict with 'var' key
    if isinstance(port_val, dict) and "var" in port_val:
        var_name = port_val["var"]
        return resolved_vars.get(var_name, port_val)

    # Already an int or other value
    return port_val


def generate_firewall_tests(
    contract: PhaseContractPlan,
    resolved_vars: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """
    Generate test data for firewall checks.

    Args:
        contract: The phase contract plan
        resolved_vars: Resolved variable values for port references
    """
    tests = []

    for fw in contract.firewall:
        ports = []
        for port_spec in fw.ports:
            port_val = port_spec.get("port")
            port_val = _resolve_port(port_val, resolved_vars)

            ports.append({
                "port": port_val,
                "protocol": port_spec.get("protocol", "tcp"),
                "zone": port_spec.get("zone", "public"),
            })

        tests.append({
            "hosts": fw.host_targets,
            "ports": ports,
            "firewall_type": fw.firewall_type,
            "weight": fw.weight,
        })

    return tests


def generate_http_endpoint_tests(contract: PhaseContractPlan) -> List[Dict[str, Any]]:
    """Generate test data for HTTP endpoint checks."""
    tests = []

    for http in contract.http_endpoints:
        tests.append({
            "url": http.url,
            "method": http.method,
            "expected_status": http.expected_status,
            "response_contains": http.response_contains,
            "response_regex": http.response_regex,
            "timeout_seconds": http.timeout_seconds,
            "hosts": http.host_targets,
            "safe_name": _make_safe_name(http.url),
            "weight": http.weight,
        })

    return tests
