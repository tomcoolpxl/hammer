"""Binding test generation for HAMMER.

Generates tests that verify variable bindings are correctly applied.
"""

from typing import Any, Dict, List

from hammer.plan import BindingCheck, PhaseContractPlan
from hammer.spec import HammerSpec
from hammer.testgen.utils import make_safe_name


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

    # Return early if no variable contracts
    if not spec.variable_contracts:
        return tests

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
                "test_name": make_safe_name(
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

    This uses the most specific scope from the variable's overlay targets.
    We prioritize in order: host_vars > group_vars > inventory_vars/extra_vars.

    The idea is that bindings should only be tested on hosts where the
    playbook actually uses the variable, which is typically determined
    by the group scope, not by extra_vars which just override values.
    """
    # Return early if no variable contracts
    if not spec.variable_contracts:
        return []

    # Find the variable contract
    var_contract = None
    for vc in spec.variable_contracts:
        if vc.name == binding.variable:
            var_contract = vc
            break

    if not var_contract:
        return []

    # Collect hosts by specificity level
    host_vars_hosts = set()
    group_vars_hosts = set()
    global_hosts = set()

    for target in var_contract.grading_overlay_targets:
        if target.overlay_kind == "host_vars":
            # Direct host reference - most specific
            host_vars_hosts.add(target.target_name)
        elif target.overlay_kind == "group_vars":
            # Find all hosts in this group
            for node in spec.topology.nodes:
                if target.target_name in node.groups:
                    group_vars_hosts.add(node.name)
        elif target.overlay_kind in ("extra_vars", "inventory_vars"):
            # Global scope - collect but use as fallback only
            for node in spec.topology.nodes:
                global_hosts.add(node.name)

    # Return the most specific scope that has hosts
    if host_vars_hosts:
        return sorted(host_vars_hosts)
    elif group_vars_hosts:
        return sorted(group_vars_hosts)
    elif global_hosts:
        return sorted(global_hosts)
    else:
        # Default to first host if nothing else found
        return [spec.topology.nodes[0].name]
