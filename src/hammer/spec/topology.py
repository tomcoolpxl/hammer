"""Topology models for HAMMER spec."""

from typing import List, Optional, Literal

from pydantic import BaseModel, Field, model_validator

from hammer.validators import SafeIdentifier, SafeDomain
from hammer.spec.primitives import Protocol


class NodeResources(BaseModel):
    cpu: int = Field(ge=1, le=64)
    ram_mb: int = Field(ge=256, le=262144)


class ForwardedPort(BaseModel):
    host_port: int = Field(ge=1, le=65535)
    guest_port: int = Field(ge=1, le=65535)
    protocol: Protocol


class Node(BaseModel):
    name: SafeIdentifier
    groups: List[SafeIdentifier]
    resources: NodeResources
    forwarded_ports: Optional[List[ForwardedPort]] = None


class Dependency(BaseModel):
    from_host: SafeIdentifier
    to_host: SafeIdentifier
    kind: Literal["reachability", "ordering"]


class Topology(BaseModel):
    domain: Optional[SafeDomain] = None
    nodes: List[Node]
    forwarded_ports: Optional[List[ForwardedPort]] = None
    dependencies: Optional[List[Dependency]] = None

    @model_validator(mode="after")
    def unique_node_names(self) -> "Topology":
        names = [n.name for n in self.nodes]
        if len(names) != len(set(names)):
            raise ValueError("Duplicate node names in topology")
        return self
