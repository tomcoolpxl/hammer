"""Reachability test generation for HAMMER.

Generates tests that verify network connectivity between hosts.
"""

from typing import Any, Dict, List

from hammer.plan import PhaseContractPlan


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


def generate_reachability_tests(
    contract: PhaseContractPlan,
    resolved_vars: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """
    Generate test data for reachability checks.

    Args:
        contract: The phase contract plan
        resolved_vars: Resolved variable values for port references
    """
    tests = []

    for reach in contract.reachability:
        port_val = _resolve_port(reach.port, resolved_vars)

        tests.append({
            "from_host": reach.from_host,
            "to_host": reach.to_host,
            "protocol": reach.protocol,
            "port": port_val,
            "expectation": reach.expectation,
            "weight": reach.weight,
        })

    return tests
