"""Lock artifact generation for HAMMER assignments.

Provides reproducibility through version pinning and checksums.
"""

import hashlib
import json
from typing import Dict, List, Optional

from pydantic import BaseModel

from hammer.spec import HammerSpec
from hammer.builder.network import NetworkPlan


class PinnedVersions(BaseModel):
    """Pinned versions for reproducibility."""

    almalinux_box: str  # e.g., "generic/alma9"
    ansible_core: Optional[str] = None  # e.g., "2.15.0"
    python_deps: Dict[str, str] = {}  # package -> version


class LockArtifact(BaseModel):
    """Lock file containing all reproducibility information."""

    spec_hash: str  # SHA256 of spec content
    seed: int  # Original seed from spec
    resolved_network: NetworkPlan
    pinned_versions: PinnedVersions
    checksums: Dict[str, str]  # file_path -> SHA256


def compute_spec_hash(spec: HammerSpec) -> str:
    """
    Compute SHA256 hash of the spec.

    Args:
        spec: The HAMMER spec

    Returns:
        Hex-encoded SHA256 hash
    """
    # Serialize spec to JSON for consistent hashing
    spec_json = spec.model_dump_json(indent=None)
    return hashlib.sha256(spec_json.encode("utf-8")).hexdigest()


def compute_file_checksum(content: str | bytes) -> str:
    """
    Compute SHA256 checksum of file content.

    Args:
        content: File content as string or bytes

    Returns:
        Hex-encoded SHA256 hash
    """
    if isinstance(content, str):
        content = content.encode("utf-8")
    return hashlib.sha256(content).hexdigest()


def create_lock_artifact(
    spec: HammerSpec,
    network: NetworkPlan,
    box_version: str,
    file_checksums: Dict[str, str],
) -> LockArtifact:
    """
    Create a lock artifact for the build.

    Args:
        spec: The HAMMER spec
        network: The resolved network plan
        box_version: Vagrant box version used
        file_checksums: Map of file paths to their checksums

    Returns:
        LockArtifact with all reproducibility info
    """
    spec_hash = compute_spec_hash(spec)

    pinned_versions = PinnedVersions(
        almalinux_box=box_version,
    )

    return LockArtifact(
        spec_hash=spec_hash,
        seed=spec.seed,
        resolved_network=network,
        pinned_versions=pinned_versions,
        checksums=file_checksums,
    )


def write_lock_artifact(lock: LockArtifact, output_path: str | object) -> None:
    """
    Write lock artifact to JSON file.

    Args:
        lock: The lock artifact
        output_path: Path to write lock.json
    """
    from pathlib import Path

    path = Path(output_path) if not isinstance(output_path, Path) else output_path

    with open(path, "w") as f:
        json.dump(lock.model_dump(), f, indent=2)
