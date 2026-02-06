"""Shared utility functions for HAMMER."""

from pathlib import Path


def validate_path_within(user_path: Path, base_dir: Path) -> Path:
    """Validate that a path resolves within the given base directory.

    Args:
        user_path: The user-supplied path (relative to base_dir).
        base_dir: The base directory that user_path must stay within.

    Returns:
        The resolved absolute path.

    Raises:
        ValueError: If the resolved path escapes base_dir.
    """
    resolved = (base_dir / user_path).resolve()
    base_resolved = base_dir.resolve()
    if not resolved.is_relative_to(base_resolved):
        raise ValueError(f"Path traversal detected: {user_path} resolves outside {base_dir}")
    return resolved
