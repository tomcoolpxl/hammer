"""Shared utilities for HAMMER test generation."""

import re
from typing import Any, Dict


def make_safe_name(s: str) -> str:
    """Convert a string to a valid Python identifier."""
    safe = re.sub(r"[^a-zA-Z0-9]", "_", s)
    safe = re.sub(r"^[0-9]+", "", safe)
    safe = re.sub(r"_+", "_", safe)
    return safe.strip("_").lower()


def resolve_port(port_val: Any, resolved_vars: Dict[str, Any]) -> Any:
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
