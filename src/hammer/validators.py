"""Input validation types for HAMMER.

Provides Pydantic-compatible validated string types to prevent
injection attacks in generated code and shell commands.
"""

import re
from typing import Annotated

from pydantic import AfterValidator


def _check_identifier(v: str) -> str:
    """Validate that a string is a safe identifier (node names, groups, services, etc.)."""
    if not v:
        raise ValueError("Identifier must not be empty")
    if not re.match(r'^[a-zA-Z][a-zA-Z0-9_-]{0,63}$', v):
        raise ValueError(
            f"Invalid identifier: {v!r}. "
            "Must start with a letter and contain only letters, digits, underscores, or hyphens (max 64 chars)."
        )
    return v


def _check_domain(v: str) -> str:
    """Validate that a string is a safe domain name."""
    if not v:
        raise ValueError("Domain must not be empty")
    if not re.match(r'^[a-zA-Z0-9]([a-zA-Z0-9.-]*[a-zA-Z0-9])?$', v):
        raise ValueError(f"Invalid domain: {v!r}")
    if len(v) > 253:
        raise ValueError(f"Domain too long: {len(v)} chars (max 253)")
    return v


def _check_safe_path(v: str) -> str:
    """Validate that a path is safe (no traversal, no shell metacharacters)."""
    if not v:
        raise ValueError("Path must not be empty")
    if '..' in v.split('/'):
        raise ValueError(f"Path traversal not allowed: {v!r}")
    if v.startswith('/') and not v.startswith('/etc/') and not v.startswith('/opt/') \
       and not v.startswith('/usr/') and not v.startswith('/var/') \
       and not v.startswith('/tmp/') and not v.startswith('/home/') \
       and not v.startswith('/srv/'):
        raise ValueError(f"Absolute path outside allowed prefixes: {v!r}")
    if re.search(r'[;&|$`\\]', v):
        raise ValueError(f"Unsafe characters in path: {v!r}")
    return v


def _check_relative_path(v: str) -> str:
    """Validate that a path is a safe relative path (for playbooks, provided_files)."""
    if not v:
        raise ValueError("Path must not be empty")
    if '..' in v.split('/'):
        raise ValueError(f"Path traversal not allowed: {v!r}")
    if v.startswith('/'):
        raise ValueError(f"Expected relative path, got absolute: {v!r}")
    if re.search(r'[;&|$`\\]', v):
        raise ValueError(f"Unsafe characters in path: {v!r}")
    return v


def _check_safe_pattern(v: str) -> str:
    """Validate that a pattern string is safe for embedding in generated Python code."""
    if not v:
        raise ValueError("Pattern must not be empty")
    # Disallow unescaped quotes that could break out of string literals
    if '\x00' in v:
        raise ValueError("Null bytes not allowed in patterns")
    return v


def _check_safe_url(v: str) -> str:
    """Validate that a URL is safe for embedding in generated code."""
    if not v:
        raise ValueError("URL must not be empty")
    # Allow http/https URLs and template variable references
    if not re.match(r'^https?://[^\s;&|`]+$', v):
        raise ValueError(f"Invalid URL: {v!r}")
    return v


def _check_safe_zone(v: str) -> str:
    """Validate firewall zone name."""
    if not v:
        raise ValueError("Zone must not be empty")
    if not re.match(r'^[a-zA-Z][a-zA-Z0-9_-]{0,63}$', v):
        raise ValueError(f"Invalid zone name: {v!r}")
    return v


SafeIdentifier = Annotated[str, AfterValidator(_check_identifier)]
SafeDomain = Annotated[str, AfterValidator(_check_domain)]
SafePath = Annotated[str, AfterValidator(_check_safe_path)]
SafeRelativePath = Annotated[str, AfterValidator(_check_relative_path)]
SafePattern = Annotated[str, AfterValidator(_check_safe_pattern)]
SafeUrl = Annotated[str, AfterValidator(_check_safe_url)]
SafeZone = Annotated[str, AfterValidator(_check_safe_zone)]
