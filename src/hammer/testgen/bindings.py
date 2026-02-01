"""Binding test generation for HAMMER.

Generates tests that verify variable bindings are correctly applied.
"""

import re
from typing import Any, Dict, List

from hammer.plan import BindingCheck, PhaseContractPlan
from hammer.spec import HammerSpec


def _make_safe_name(s: str) -> str:
    """Convert a string to a valid Python identifier."""
    # Replace non-alphanumeric chars with underscores
    safe = re.sub(r"[^a-zA-Z0-9]", "_", s)
    # Remove leading digits
    safe = re.sub(r"^[0-9]+", "", safe)
    # Collapse multiple underscores
    safe = re.sub(r"_+", "_", safe)
    return safe.strip("_").lower()


def generate_binding_tests(
    spec: HammerSpec,
    contract: PhaseContractPlan,
    phase: str,
) -> List[Dict[str, Any]]:
    """
    Generate test data for binding checks.

    Args:
        spec: The HAMMER spec
        contract: The phase contract plan
        phase: The phase name (baseline, mutation, idempotence)

    Returns:
        List of test data dictionaries for template rendering
    """
    tests = []

    # Group bindings by variable and host
    for binding in contract.bindings:
        binding_type = binding.binding_type
        target = binding.binding_target
        expected = binding.expected_value

        # Determine which hosts this binding applies to
        # For now, we'll apply to hosts from the variable contract's overlay targets
        # This is a simplification - in reality we'd need to resolve node selectors
        hosts = _get_hosts_for_binding(spec, binding)

        for host in hosts:
            test_data = {
                "test_name": _make_safe_name(
                    f"{binding.variable}_{binding_type}_{host}"
                ),
                "host": host,
                "binding_type": binding_type,
                "variable": binding.variable,
                "expected_value": expected,
                "weight": binding.weight,
            }

            # Add type-specific fields
            if binding_type == "service_listen_port":
                test_data["service"] = target.get("service", "")
                test_data["protocol"] = target.get("protocol", "tcp")
                test_data["address"] = target.get("address", "0.0.0.0")
                test_data["description"] = (
                    f"Verify {target.get('service')} listens on port {expected}"
                )

            elif binding_type == "firewall_port_open":
                test_data["zone"] = target.get("zone", "public")
                test_data["protocol"] = target.get("protocol", "tcp")
                test_data["description"] = (
                    f"Verify firewall allows port {expected}/{target.get('protocol', 'tcp')}"
                )

            elif binding_type in ("template_contains", "file_contains"):
                test_data["path"] = target.get("path", "")
                # Replace {{ value }} placeholder with actual value
                pattern = target.get("pattern", "")
                test_data["expected_pattern"] = pattern.replace(
                    "{{ value }}", str(expected)
                )
                test_data["description"] = (
                    f"Verify file {target.get('path')} contains expected content"
                )

            elif binding_type == "file_exists":
                test_data["path"] = target.get("path", "")
                test_data["description"] = f"Verify file {target.get('path')} exists"

            elif binding_type == "file_mode":
                test_data["path"] = target.get("path", "")
                test_data["mode"] = target.get("mode", "")
                test_data["description"] = (
                    f"Verify file {target.get('path')} has correct mode"
                )

            elif binding_type == "file_owner":
                test_data["path"] = target.get("path", "")
                test_data["owner"] = target.get("owner", "")
                test_data["group"] = target.get("group", "")
                test_data["description"] = (
                    f"Verify file {target.get('path')} has correct ownership"
                )

            tests.append(test_data)

    return tests


def _get_hosts_for_binding(spec: HammerSpec, binding: BindingCheck) -> List[str]:
    """
    Determine which hosts a binding applies to.

    For now, we find the variable contract and use its overlay targets
    to determine applicable hosts/groups.
    """
    # Find the variable contract
    var_contract = None
    for vc in spec.variable_contracts:
        if vc.name == binding.variable:
            var_contract = vc
            break

    if not var_contract:
        return []

    hosts = set()

    # Look at grading overlay targets to determine hosts
    for target in var_contract.grading_overlay_targets:
        if target.overlay_kind == "host_vars":
            # Direct host reference
            hosts.add(target.target_name)
        elif target.overlay_kind == "group_vars":
            # Find all hosts in this group
            for node in spec.topology.nodes:
                if target.target_name in node.groups:
                    hosts.add(node.name)
        elif target.overlay_kind in ("extra_vars", "inventory_vars"):
            # Applies to all hosts
            for node in spec.topology.nodes:
                hosts.add(node.name)

    # If no hosts determined, default to first host with matching group
    if not hosts:
        hosts.add(spec.topology.nodes[0].name)

    return sorted(hosts)
