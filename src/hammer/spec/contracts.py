"""Behavioral contract models for HAMMER spec."""

from typing import List, Optional, Union, Literal

from pydantic import BaseModel, Field, model_validator

from hammer.validators import SafeIdentifier, SafePath, SafePattern, SafeZone
from hammer.spec.primitives import (
    NonEmptyStr,
    ExecutionPhaseName,
    ReachabilityExpectation,
    Protocol,
)


# -------------------------
# Node selector
# -------------------------

class NodeSelector(BaseModel):
    group: Optional[SafeIdentifier] = None
    host: Optional[SafeIdentifier] = None

    @model_validator(mode="after")
    def exactly_one_selector(self) -> "NodeSelector":
        if (self.group is None and self.host is None) or \
           (self.group is not None and self.host is not None):
            raise ValueError("Exactly one of group or host must be specified")
        return self


# -------------------------
# Port references
# -------------------------

class PortRefVar(BaseModel):
    var: SafeIdentifier


PortRef = Union[int, PortRefVar]


# -------------------------
# Behavioral contracts
# -------------------------

class PackageContract(BaseModel):
    name: SafeIdentifier
    state: Literal["present", "absent"]
    node_selector: NodeSelector
    phases: Optional[List[ExecutionPhaseName]] = None
    weight: float = Field(default=1.0, ge=0.0)


class PipPackageContract(BaseModel):
    """Contract for verifying pip packages are installed."""
    name: NonEmptyStr  # pip names can have dots, etc.
    state: Literal["present", "absent"] = "present"
    python: Optional[SafePath] = None
    node_selector: NodeSelector
    phases: Optional[List[ExecutionPhaseName]] = None
    weight: float = Field(default=1.0, ge=0.0)


class ServiceContract(BaseModel):
    name: SafeIdentifier
    enabled: bool
    running: bool
    node_selector: NodeSelector
    phases: Optional[List[ExecutionPhaseName]] = None
    weight: float = Field(default=1.0, ge=0.0)


class UserContract(BaseModel):
    """Contract for verifying system users exist with specified properties."""
    name: SafeIdentifier
    exists: bool = True
    uid: Optional[int] = None
    gid: Optional[int] = None
    home: Optional[SafePath] = None
    shell: Optional[SafePath] = None
    groups: Optional[List[SafeIdentifier]] = None
    node_selector: NodeSelector
    phases: Optional[List[ExecutionPhaseName]] = None
    weight: float = Field(default=1.0, ge=0.0)


class GroupContract(BaseModel):
    """Contract for verifying system groups exist with specified properties."""
    name: SafeIdentifier
    exists: bool = True
    gid: Optional[int] = None
    node_selector: NodeSelector
    phases: Optional[List[ExecutionPhaseName]] = None
    weight: float = Field(default=1.0, ge=0.0)


class FirewallPort(BaseModel):
    port: PortRef
    protocol: Protocol
    zone: SafeZone


FirewallType = Literal["firewalld", "iptables"]


class FirewallContract(BaseModel):
    open_ports: List[FirewallPort]
    node_selector: NodeSelector
    firewall_type: FirewallType = "firewalld"
    phases: Optional[List[ExecutionPhaseName]] = None
    weight: float = Field(default=1.0, ge=0.0)


class FileContractItem(BaseModel):
    path: SafePath
    present: bool
    is_directory: bool = False
    mode: Optional[NonEmptyStr] = None
    owner: Optional[SafeIdentifier] = None
    group: Optional[SafeIdentifier] = None
    content_regex: Optional[SafePattern] = None


class FilesContract(BaseModel):
    items: List[FileContractItem]
    node_selector: NodeSelector
    phases: Optional[List[ExecutionPhaseName]] = None
    weight: float = Field(default=1.0, ge=0.0)


class ReachabilityContract(BaseModel):
    from_host: SafeIdentifier
    to_host: SafeIdentifier
    protocol: Protocol
    port: PortRef
    expectation: ReachabilityExpectation
    phases: Optional[List[ExecutionPhaseName]] = None
    weight: float = Field(default=1.0, ge=0.0)


class HttpEndpointContract(BaseModel):
    """Contract for verifying HTTP endpoints return expected responses."""
    url: NonEmptyStr
    method: Literal["GET", "POST", "PUT", "DELETE", "HEAD"] = "GET"
    expected_status: int = Field(default=200, ge=100, le=599)
    response_contains: Optional[SafePattern] = None
    response_regex: Optional[SafePattern] = None
    timeout_seconds: int = Field(default=5, ge=1, le=60)
    node_selector: NodeSelector
    phases: Optional[List[ExecutionPhaseName]] = None
    weight: float = Field(default=1.0, ge=0.0)


class ExternalHttpContract(BaseModel):
    """Contract for verifying HTTP endpoints from external perspective."""
    url: NonEmptyStr
    method: Literal["GET", "POST", "PUT", "DELETE", "HEAD"] = "GET"
    expected_status: int = Field(default=200, ge=100, le=599)
    response_contains: Optional[SafePattern] = None
    response_regex: Optional[SafePattern] = None
    timeout_seconds: int = Field(default=10, ge=1, le=60)
    from_host: bool = False
    from_node: Optional[NodeSelector] = None
    phases: Optional[List[ExecutionPhaseName]] = None
    weight: float = Field(default=1.0, ge=0.0)

    @model_validator(mode="after")
    def validate_source(self) -> "ExternalHttpContract":
        if self.from_host and self.from_node:
            raise ValueError("Cannot specify both from_host=True and from_node")
        if not self.from_host and not self.from_node:
            raise ValueError("Must specify either from_host=True or from_node")
        return self


class OutputContract(BaseModel):
    """Contract for verifying Ansible output contains expected patterns."""
    pattern: SafePattern
    match_type: Literal["contains", "regex"] = "contains"
    expected: bool = True
    description: Optional[NonEmptyStr] = None
    phases: Optional[List[ExecutionPhaseName]] = None
    weight: float = Field(default=1.0, ge=0.0)


class BehavioralContracts(BaseModel):
    packages: Optional[List[PackageContract]] = None
    pip_packages: Optional[List[PipPackageContract]] = None
    services: Optional[List[ServiceContract]] = None
    users: Optional[List[UserContract]] = None
    groups: Optional[List[GroupContract]] = None
    firewall: Optional[List[FirewallContract]] = None
    files: Optional[List[FilesContract]] = None
    reachability: Optional[List[ReachabilityContract]] = None
    http_endpoints: Optional[List[HttpEndpointContract]] = None
    external_http: Optional[List[ExternalHttpContract]] = None
    output_checks: Optional[List[OutputContract]] = None
