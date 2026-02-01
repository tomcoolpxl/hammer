"""Network plan generation for HAMMER assignments.

Provides deterministic IP address assignment based on spec seed.
"""

import hashlib
from typing import Dict

from pydantic import BaseModel

from hammer.spec import HammerSpec


class NetworkPlan(BaseModel):
    """Resolved network configuration for an assignment."""

    cidr: str  # e.g., "192.168.42.0/24"
    gateway: str  # e.g., "192.168.42.1"
    netmask: str  # e.g., "255.255.255.0"
    node_ip_map: Dict[str, str]  # node_name -> IP address


def generate_network_plan(spec: HammerSpec) -> NetworkPlan:
    """
    Generate a deterministic network plan from the spec seed.

    Algorithm:
    1. Hash the seed to get a subnet octet (1-254)
    2. Use 192.168.x.0/24 as the network
    3. Assign IPs starting from .10 in node definition order
    """
    # Hash the seed to get a deterministic subnet octet
    seed_bytes = str(spec.seed).encode("utf-8")
    hash_digest = hashlib.sha256(seed_bytes).digest()

    # Use first byte of hash to select subnet (1-254, avoiding 0 and 255)
    subnet_octet = (hash_digest[0] % 254) + 1

    cidr = f"192.168.{subnet_octet}.0/24"
    gateway = f"192.168.{subnet_octet}.1"
    netmask = "255.255.255.0"

    # Assign IPs to nodes starting at .10
    node_ip_map: Dict[str, str] = {}
    for idx, node in enumerate(spec.topology.nodes):
        ip_suffix = 10 + idx
        node_ip_map[node.name] = f"192.168.{subnet_octet}.{ip_suffix}"

    return NetworkPlan(
        cidr=cidr,
        gateway=gateway,
        netmask=netmask,
        node_ip_map=node_ip_map,
    )
