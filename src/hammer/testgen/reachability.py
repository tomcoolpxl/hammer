"""Reachability test generation for HAMMER.

Generates tests that verify network connectivity between hosts.
"""

from typing import Any, Dict, List

from hammer.plan import PhaseContractPlan
from hammer.testgen.utils import resolve_port


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
        port_val = resolve_port(reach.port, resolved_vars)

        tests.append({
            "from_host": reach.from_host,
            "to_host": reach.to_host,
            "protocol": reach.protocol,
            "port": port_val,
            "expectation": reach.expectation,
            "weight": reach.weight,
        })

    return tests
