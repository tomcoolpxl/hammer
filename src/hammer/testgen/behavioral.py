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
    GroupCheck,
    FileCheck,
    FirewallCheck,
    HttpEndpointCheck,
    HandlerPlan,
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


def generate_group_tests(contract: PhaseContractPlan) -> List[Dict[str, Any]]:
    """Generate test data for group checks."""
    tests = []

    for group in contract.groups:
        tests.append({
            "name": group.name,
            "exists": group.exists,
            "gid": group.gid,
            "hosts": group.host_targets,
            "weight": group.weight,
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
            mode_str = item.get("mode")
            if mode_str:
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


def _interpolate_vars(s: str, resolved_vars: Dict[str, Any]) -> str:
    """Interpolate {{ var }} placeholders in a string."""
    if not s:
        return s
    
    result = s
    for name, val in resolved_vars.items():
        placeholder = "{{" + f" {name} " + "}}"
        placeholder_no_space = "{{" + name + "}}"
        result = result.replace(placeholder, str(val))
        result = result.replace(placeholder_no_space, str(val))
    
    return result


def generate_http_endpoint_tests(
    contract: PhaseContractPlan,
    resolved_vars: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """Generate test data for HTTP endpoint checks."""
    tests = []

    for http in contract.http_endpoints:
        url = _interpolate_vars(http.url, resolved_vars)
        tests.append({
            "url": url,
            "method": http.method,
            "expected_status": http.expected_status,
            "response_contains": http.response_contains,
            "response_regex": http.response_regex,
            "timeout_seconds": http.timeout_seconds,
            "hosts": http.host_targets,
            "safe_name": _make_safe_name(url),
            "weight": http.weight,
        })

    return tests


def generate_external_http_tests(
    contract: PhaseContractPlan,
    resolved_vars: Dict[str, Any],
) -> Dict[str, List[Dict[str, Any]]]:
    """Generate test data for external HTTP checks."""
    host_tests = []
    vm_tests = []

    for ext in contract.external_http:
        url = _interpolate_vars(ext.url, resolved_vars)
        test_data = {
            "url": url,
            "method": ext.method,
            "expected_status": ext.expected_status,
            "response_contains": ext.response_contains,
            "response_regex": ext.response_regex,
            "timeout_seconds": ext.timeout_seconds,
            "safe_name": _make_safe_name(url),
            "weight": ext.weight,
        }

        if ext.from_host:
            host_tests.append(test_data)
        elif ext.from_node_targets:
            test_data["hosts"] = ext.from_node_targets
            vm_tests.append(test_data)

    return {"host_tests": host_tests, "vm_tests": vm_tests}


def generate_handler_tests(contract: PhaseContractPlan) -> List[Dict[str, Any]]:
    """Generate test data for handler execution checks."""
    tests = []

    for handler in contract.handlers:
        # Get the expected runs for this phase
        phase_expectation = handler.expectations.get(contract.phase)
        if not phase_expectation:
            continue

        tests.append({
            "name": handler.handler_name,
            "service": handler.service,
            "action": handler.action,
            "hosts": handler.host_targets,
            "expected_runs": phase_expectation.expected_runs,
            "weight": handler.weight,
        })

    return tests


def generate_output_tests(contract: PhaseContractPlan) -> List[Dict[str, Any]]:
    """Generate test data for Ansible output pattern checks."""
    tests = []

    for idx, check in enumerate(contract.output_checks):
        # Create a safe name from description or pattern
        if check.description:
            safe_name = _make_safe_name(check.description)
        else:
            safe_name = _make_safe_name(check.pattern[:30])

        # Ensure uniqueness
        safe_name = f"{safe_name}_{idx}"

        tests.append({
            "pattern": check.pattern,
            "match_type": check.match_type,
            "expected": check.expected,
            "description": check.description or check.pattern,
            "safe_name": safe_name,
            "weight": check.weight,
        })

    return tests
