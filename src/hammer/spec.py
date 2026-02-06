from typing import List, Dict, Optional, Union, Literal, Any
from pathlib import Path
import yaml
from pydantic import BaseModel, Field, model_validator

from hammer.validators import (
    SafeIdentifier,
    SafeDomain,
    SafePath,
    SafeRelativePath,
    SafePattern,
    SafeUrl,
    SafeZone,
)

# -------------------------
# Common primitives
# -------------------------

NonEmptyStr = str  # Kept for fields where strict validation is not needed

PhaseName = Literal["baseline", "mutation"]

ExecutionPhaseName = Literal["baseline", "mutation", "idempotence"]

VarType = Literal["int", "string", "bool", "list", "dict"]

OverlayKind = Literal["group_vars", "host_vars", "inventory_vars", "extra_vars"]

BindingMode = Literal["all", "any"]

PrecedenceLayer = Literal[
    "role_default",
    "role_vars",
    "play_vars",
    "vars_files",
    "inventory_vars",
    "group_vars",
    "host_vars",
    "extra_vars",
]

ExpectedRuns = Literal["zero", "at_least_once", "exactly_once"]

ReachabilityExpectation = Literal["reachable", "not_reachable"]

Protocol = Literal["tcp", "udp"]


# -------------------------
# Feature flags
# -------------------------

class FeatureFlags(BaseModel):
    vault: bool = False
    selinux: bool = False
    handlers: bool = True
    reachability: bool = False


# -------------------------
# Topology
# -------------------------

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
    domain: Optional[SafeDomain] = None  # Optional domain suffix for FQDNs
    nodes: List[Node]
    forwarded_ports: Optional[List[ForwardedPort]] = None  # Topology-wide ports (legacy)
    dependencies: Optional[List[Dependency]] = None

    @model_validator(mode="after")
    def unique_node_names(self) -> "Topology":
        names = [n.name for n in self.nodes]
        if len(names) != len(set(names)):
            raise ValueError("Duplicate node names in topology")
        return self


# -------------------------
# Entrypoints
# -------------------------

class ProvidedFile(BaseModel):
    """A file provided by the assignment to students."""
    source: SafeRelativePath  # Path relative to spec file
    destination: SafeRelativePath  # Path in student bundle


class Entrypoints(BaseModel):
    playbook_path: SafeRelativePath
    required_roles: Optional[List[SafeIdentifier]] = None
    required_files: Optional[List[SafeRelativePath]] = None
    provided_files: Optional[List[ProvidedFile]] = None  # Files given to students


# -------------------------
# Variable bindings
# -------------------------

class ServiceListenTarget(BaseModel):
    service: SafeIdentifier
    protocol: Protocol
    address: NonEmptyStr


class FirewallPortTarget(BaseModel):
    zone: SafeZone
    protocol: Protocol


class FilePatternTarget(BaseModel):
    path: SafePath
    pattern: SafePattern


class FilePathTarget(BaseModel):
    path: SafePath


class FileModeTarget(BaseModel):
    path: SafePath
    mode: NonEmptyStr


class FileOwnerTarget(BaseModel):
    path: SafePath
    owner: SafeIdentifier
    group: SafeIdentifier


BindingTarget = Union[
    ServiceListenTarget,
    FirewallPortTarget,
    FilePatternTarget,
    FilePathTarget,
    FileModeTarget,
    FileOwnerTarget,
]


class Binding(BaseModel):
    type: Literal[
        "service_listen_port",
        "firewall_port_open",
        "template_contains",
        "file_contains",
        "file_exists",
        "file_mode",
        "file_owner",
    ]
    target: BindingTarget
    weight: float = Field(default=1.0, ge=0.0)


class OverlayTarget(BaseModel):
    overlay_kind: OverlayKind
    target_name: SafeIdentifier


class VariableDefaults(BaseModel):
    student: Any


class VariableContract(BaseModel):
    name: SafeIdentifier
    type: VarType
    defaults: VariableDefaults
    allowed_values: List[Any]
    grading_overlay_targets: List[OverlayTarget]
    binding_targets: List[Binding]
    bindings_mode: BindingMode = "all"

    @model_validator(mode="after")
    def validate_variable_contract(self) -> "VariableContract":
        if self.binding_targets and len(self.allowed_values) < 2:
            raise ValueError(
                f"Variable '{self.name}' has bindings but less than 2 allowed_values"
            )

        if not self.grading_overlay_targets:
            raise ValueError(
                f"Variable '{self.name}' must declare at least one grading_overlay_target"
            )

        return self


# -------------------------
# Precedence scenarios
# -------------------------

class PrecedenceScenario(BaseModel):
    name: SafeIdentifier
    variable: SafeIdentifier
    layers: List[PrecedenceLayer]
    expected_winner: PrecedenceLayer
    bindings_to_verify: List[int]
    phase: PhaseName = "baseline"

    @model_validator(mode="after")
    def validate_layers(self) -> "PrecedenceScenario":
        if len(self.layers) < 2:
            raise ValueError("Precedence scenario must contain at least two layers")

        if self.expected_winner not in self.layers:
            raise ValueError(
                "expected_winner must be present in layers list"
            )

        return self


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
# Behavioral contracts
# -------------------------

class PackageContract(BaseModel):
    name: SafeIdentifier
    state: Literal["present", "absent"]
    node_selector: NodeSelector
    phases: Optional[List[ExecutionPhaseName]] = None  # None = all phases
    weight: float = Field(default=1.0, ge=0.0)


class PipPackageContract(BaseModel):
    """Contract for verifying pip packages are installed."""
    name: NonEmptyStr  # pip names can have dots, etc.
    state: Literal["present", "absent"] = "present"
    python: Optional[SafePath] = None  # Python executable, defaults to system python3
    node_selector: NodeSelector
    phases: Optional[List[ExecutionPhaseName]] = None  # None = all phases
    weight: float = Field(default=1.0, ge=0.0)


class ServiceContract(BaseModel):
    name: SafeIdentifier
    enabled: bool
    running: bool
    node_selector: NodeSelector
    phases: Optional[List[ExecutionPhaseName]] = None  # None = all phases
    weight: float = Field(default=1.0, ge=0.0)


class UserContract(BaseModel):
    """Contract for verifying system users exist with specified properties."""
    name: SafeIdentifier
    exists: bool = True
    uid: Optional[int] = None
    gid: Optional[int] = None
    home: Optional[SafePath] = None
    shell: Optional[SafePath] = None
    groups: Optional[List[SafeIdentifier]] = None  # Supplementary groups
    node_selector: NodeSelector
    phases: Optional[List[ExecutionPhaseName]] = None  # None = all phases
    weight: float = Field(default=1.0, ge=0.0)


class GroupContract(BaseModel):
    """Contract for verifying system groups exist with specified properties."""
    name: SafeIdentifier
    exists: bool = True
    gid: Optional[int] = None
    node_selector: NodeSelector
    phases: Optional[List[ExecutionPhaseName]] = None  # None = all phases
    weight: float = Field(default=1.0, ge=0.0)


class PortRefVar(BaseModel):
    var: SafeIdentifier


PortRef = Union[int, PortRefVar]


class FirewallPort(BaseModel):
    port: PortRef
    protocol: Protocol
    zone: SafeZone


FirewallType = Literal["firewalld", "iptables"]


class FirewallContract(BaseModel):
    open_ports: List[FirewallPort]
    node_selector: NodeSelector
    firewall_type: FirewallType = "firewalld"  # firewalld or iptables
    phases: Optional[List[ExecutionPhaseName]] = None  # None = all phases
    weight: float = Field(default=1.0, ge=0.0)


class FileContractItem(BaseModel):
    path: SafePath
    present: bool
    is_directory: bool = False  # True if path should be a directory
    mode: Optional[NonEmptyStr] = None
    owner: Optional[SafeIdentifier] = None
    group: Optional[SafeIdentifier] = None
    content_regex: Optional[SafePattern] = None  # Only for files, not directories


class FilesContract(BaseModel):
    items: List[FileContractItem]
    node_selector: NodeSelector
    phases: Optional[List[ExecutionPhaseName]] = None  # None = all phases
    weight: float = Field(default=1.0, ge=0.0)


class ReachabilityContract(BaseModel):
    from_host: SafeIdentifier
    to_host: SafeIdentifier
    protocol: Protocol
    port: PortRef
    expectation: ReachabilityExpectation
    phases: Optional[List[ExecutionPhaseName]] = None  # None = all phases
    weight: float = Field(default=1.0, ge=0.0)


class HttpEndpointContract(BaseModel):
    """Contract for verifying HTTP endpoints return expected responses."""
    url: NonEmptyStr  # URL to test, can include {{ variable }} references (validated after interpolation)
    method: Literal["GET", "POST", "PUT", "DELETE", "HEAD"] = "GET"
    expected_status: int = Field(default=200, ge=100, le=599)
    response_contains: Optional[SafePattern] = None  # Substring to find in response
    response_regex: Optional[SafePattern] = None  # Regex pattern to match
    timeout_seconds: int = Field(default=5, ge=1, le=60)
    node_selector: NodeSelector  # Which node to run the test from
    phases: Optional[List[ExecutionPhaseName]] = None  # None = all phases
    weight: float = Field(default=1.0, ge=0.0)


class ExternalHttpContract(BaseModel):
    """Contract for verifying HTTP endpoints from external perspective (host or cross-VM).

    Use this when testing web accessibility from outside the target node:
    - from_host=True: Test from grading host (e.g., via port forwarding)
    - from_node: Test from another VM in the topology
    """
    url: NonEmptyStr  # URL to test (use localhost:port for host, or VM hostname for cross-VM)
    method: Literal["GET", "POST", "PUT", "DELETE", "HEAD"] = "GET"
    expected_status: int = Field(default=200, ge=100, le=599)
    response_contains: Optional[SafePattern] = None
    response_regex: Optional[SafePattern] = None
    timeout_seconds: int = Field(default=10, ge=1, le=60)
    from_host: bool = False  # If True, test from grading host machine
    from_node: Optional[NodeSelector] = None  # If from_host=False, test from this VM
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
    """Contract for verifying Ansible output contains expected patterns.

    Use this to check debug messages, registered variable output, or other
    Ansible playbook output patterns.
    """
    pattern: SafePattern  # String or regex pattern to match
    match_type: Literal["contains", "regex"] = "contains"
    expected: bool = True  # True = should match, False = should NOT match
    description: Optional[NonEmptyStr] = None  # Human-readable description
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


# -------------------------
# Handler contracts
# -------------------------

class TriggerFileChanged(BaseModel):
    file_changed: SafePath


class TriggerTemplateChanged(BaseModel):
    template_changed: SafePath


class TriggerVariableChanged(BaseModel):
    variable_changed: SafeIdentifier


Trigger = Union[
    TriggerFileChanged,
    TriggerTemplateChanged,
    TriggerVariableChanged,
]


class NonTriggerNoop(BaseModel):
    noop_rerun: Literal[True]


class NonTriggerUnrelatedFile(BaseModel):
    unrelated_file_changed: SafePath


NonTrigger = Union[
    NonTriggerNoop,
    NonTriggerUnrelatedFile,
]


class HandlerTarget(BaseModel):
    service: SafeIdentifier
    action: Literal["restart", "reload"]


class ExpectedRunsSet(BaseModel):
    baseline: ExpectedRuns
    mutation: ExpectedRuns
    idempotence: ExpectedRuns


class HandlerContract(BaseModel):
    handler_name: NonEmptyStr  # Handler names can contain spaces (e.g., "restart nginx")
    node_selector: NodeSelector
    handler_target: HandlerTarget
    trigger_conditions: List[Trigger]
    non_trigger_conditions: List[NonTrigger]
    expected_runs: ExpectedRunsSet
    weight: float = Field(default=2.0, ge=0.0)


# -------------------------
# Idempotence
# -------------------------

class IdempotenceEnforcement(BaseModel):
    require_changed_zero: bool = True
    require_no_handlers: bool = True


class IdempotencePolicy(BaseModel):
    required: bool = True
    allowed_changes: Optional[List[NonEmptyStr]] = None
    enforcement: Optional[IdempotenceEnforcement] = None


# -------------------------
# Vault
# -------------------------

class VaultSpec(BaseModel):
    vault_password: NonEmptyStr  # The vault password for decryption
    vault_ids: Optional[List[NonEmptyStr]] = None
    vaulted_vars_files: List[NonEmptyStr]
    vaulted_variables: List[NonEmptyStr]
    bindings_to_verify: List[int]


# -------------------------
# Failure policy
# -------------------------

class FailurePolicy(BaseModel):
    """Policy for handling expected failures during converge.

    Use this when certain task failures are expected behavior (e.g., testing
    error handling, intentional failure scenarios).
    """
    allow_failures: bool = False  # If True, don't fail phase on task failures
    max_failures: Optional[int] = None  # Maximum allowed failures (None = unlimited when allow_failures=True)
    expected_patterns: Optional[List[NonEmptyStr]] = None  # Regex patterns that failures should match
    # If expected_patterns is set, only failures matching these patterns are allowed


# -------------------------
# Reboot configuration
# -------------------------

class RebootConfig(BaseModel):
    """Configuration for rebooting nodes after converge, before tests."""
    enabled: bool = False
    nodes: Optional[List[SafeIdentifier]] = None  # None = all nodes
    timeout: int = Field(default=120, ge=30, le=600)
    poll_interval: int = Field(default=5, ge=1, le=30)


# -------------------------
# Phase overlays
# -------------------------

class PhaseOverlay(BaseModel):
    inventory_vars: Optional[Dict[str, Any]] = None
    group_vars: Optional[Dict[str, Dict[str, Any]]] = None
    host_vars: Optional[Dict[str, Dict[str, Any]]] = None
    extra_vars: Optional[Dict[str, Any]] = None
    reboot: Optional[RebootConfig] = None
    failure_policy: Optional[FailurePolicy] = None


class PhaseOverlays(BaseModel):
    baseline: Optional[PhaseOverlay] = None
    mutation: Optional[PhaseOverlay] = None


# -------------------------
# Root spec
# -------------------------

class HammerSpec(BaseModel):
    assignment_id: SafeIdentifier
    assignment_version: NonEmptyStr
    spec_version: Literal["1.0"]
    seed: int
    provider: Literal["libvirt"]
    os: Literal["almalinux9"]

    features: FeatureFlags = Field(default_factory=FeatureFlags)

    topology: Topology
    entrypoints: Entrypoints

    variable_contracts: Optional[List[VariableContract]] = None

    precedence_scenarios: Optional[List[PrecedenceScenario]] = None

    behavioral_contracts: Optional[BehavioralContracts] = None

    handler_contracts: Optional[List[HandlerContract]] = None

    idempotence: IdempotencePolicy

    vault: Optional[VaultSpec] = None

    phase_overlays: PhaseOverlays

    # -------------------------
    # Cross-field validation
    # -------------------------

    @model_validator(mode="after")
    def semantic_validation(self) -> "HammerSpec":

        var_names = {v.name for v in (self.variable_contracts or [])}

        # Validate precedence variable references
        if self.precedence_scenarios:
            for scen in self.precedence_scenarios:
                if scen.variable not in var_names:
                    raise ValueError(
                        f"Precedence scenario references unknown variable '{scen.variable}'"
                    )

        # Validate binding index references
        for idx, var in enumerate(self.variable_contracts or []):
            for scen in self.precedence_scenarios or []:
                if scen.variable == var.name:
                    for b in scen.bindings_to_verify:
                        if b < 0 or b >= len(var.binding_targets):
                            raise ValueError(
                                f"bindings_to_verify index {b} out of range for variable '{var.name}'"
                            )

        # Feature gating
        if self.handler_contracts and not self.features.handlers:
            raise ValueError("Handler contracts present but features.handlers is false")

        if self.vault and not self.features.vault:
            raise ValueError("Vault spec present but features.vault is false")

        if self.behavioral_contracts and self.behavioral_contracts.reachability:
            if not self.features.reachability:
                raise ValueError(
                    "Reachability contracts present but features.reachability is false"
                )

        # Phase overlay sanity - only require baseline if we have variable_contracts
        if self.variable_contracts and not self.phase_overlays.baseline:
            raise ValueError("Baseline phase_overlays must be defined when variable_contracts exist")

        # Variable overlay coverage
        overlay_vars = set()
        for phase in [self.phase_overlays.baseline, self.phase_overlays.mutation]:
            if phase:
                for src in [phase.inventory_vars, phase.extra_vars]:
                    if src:
                        overlay_vars |= set(src.keys())
                if phase.group_vars:
                    for gvars in phase.group_vars.values():
                        overlay_vars |= set(gvars.keys())
                if phase.host_vars:
                    for hvars in phase.host_vars.values():
                        overlay_vars |= set(hvars.keys())

        for var in (self.variable_contracts or []):
            if var.name not in overlay_vars:
                # Allowed: variable only uses student defaults in baseline,
                # but mutation requires change when bindings exist.
                if len(var.binding_targets) > 0:
                    raise ValueError(
                        f"Variable '{var.name}' has bindings but is never set in phase_overlays"
                    )

        # Node existence validation
        node_names = {n.name for n in self.topology.nodes}
        group_names = set()
        for n in self.topology.nodes:
            for g in n.groups:
                group_names.add(g)

        def check_selector(sel: NodeSelector) -> None:
            if sel.host and sel.host not in node_names:
                raise ValueError(f"Unknown host in selector: {sel.host}")
            if sel.group and sel.group not in group_names:
                raise ValueError(f"Unknown group in selector: {sel.group}")

        all_bcs: List[Any] = []
        if self.behavioral_contracts:
            all_bcs.extend(self.behavioral_contracts.packages or [])
            all_bcs.extend(self.behavioral_contracts.pip_packages or [])
            all_bcs.extend(self.behavioral_contracts.services or [])
            all_bcs.extend(self.behavioral_contracts.users or [])
            all_bcs.extend(self.behavioral_contracts.groups or [])
            all_bcs.extend(self.behavioral_contracts.firewall or [])
            all_bcs.extend(self.behavioral_contracts.files or [])
            all_bcs.extend(self.behavioral_contracts.http_endpoints or [])
        
        for bc in all_bcs:
            check_selector(bc.node_selector)

        # Validate external_http from_node references
        if self.behavioral_contracts and self.behavioral_contracts.external_http:
            for ext in self.behavioral_contracts.external_http:
                if ext.from_node:
                    check_selector(ext.from_node)

        for hc in self.handler_contracts or []:
            check_selector(hc.node_selector)

        # Validate reboot node references
        for phase_name in ["baseline", "mutation"]:
            phase_overlay = getattr(self.phase_overlays, phase_name, None)
            if phase_overlay and phase_overlay.reboot and phase_overlay.reboot.nodes:
                for node in phase_overlay.reboot.nodes:
                    if node not in node_names:
                        raise ValueError(
                            f"Reboot config in {phase_name} references unknown node '{node}'"
                        )

        # Validate overlay target references
        for var in (self.variable_contracts or []):
            for target in var.grading_overlay_targets:
                if target.overlay_kind == "group_vars":
                    if target.target_name not in group_names and target.target_name != "all":
                        raise ValueError(
                            f"Variable '{var.name}' overlay targets unknown group '{target.target_name}'"
                        )
                elif target.overlay_kind == "host_vars":
                    if target.target_name not in node_names:
                        raise ValueError(
                            f"Variable '{var.name}' overlay targets unknown host '{target.target_name}'"
                        )

        # Validate PortRefVar references in behavioral contracts
        def check_port_ref(port_ref: PortRef, context: str) -> None:
            if isinstance(port_ref, PortRefVar):
                if port_ref.var not in var_names:
                    raise ValueError(
                        f"{context}: references undefined variable '{port_ref.var}'"
                    )
            elif isinstance(port_ref, dict) and "var" in port_ref:
                if port_ref["var"] not in var_names:
                    raise ValueError(
                        f"{context}: references undefined variable '{port_ref['var']}'"
                    )

        if self.behavioral_contracts:
            # Check firewall port references
            for fw in self.behavioral_contracts.firewall or []:
                for port_spec in fw.open_ports:
                    check_port_ref(port_spec.port, "Firewall contract")

            # Check reachability port and host references
            for reach in self.behavioral_contracts.reachability or []:
                check_port_ref(reach.port, "Reachability contract")
                if reach.from_host not in node_names:
                    raise ValueError(
                        f"Reachability contract references unknown from_host '{reach.from_host}'"
                    )
                if reach.to_host not in node_names:
                    raise ValueError(
                        f"Reachability contract references unknown to_host '{reach.to_host}'"
                    )

        # Validate topology dependency references
        if self.topology.dependencies:
            for dep in self.topology.dependencies:
                if dep.from_host not in node_names:
                    raise ValueError(
                        f"Dependency references unknown from_host '{dep.from_host}'"
                    )
                if dep.to_host not in node_names:
                    raise ValueError(
                        f"Dependency references unknown to_host '{dep.to_host}'"
                    )

        # Validate handler trigger variable references
        for hc in self.handler_contracts or []:
            for trigger in hc.trigger_conditions:
                if isinstance(trigger, TriggerVariableChanged):
                    if trigger.variable_changed not in var_names:
                        raise ValueError(
                            f"Handler '{hc.handler_name}' trigger references "
                            f"undefined variable '{trigger.variable_changed}'"
                        )
                elif hasattr(trigger, "variable_changed"):
                    if trigger.variable_changed not in var_names:
                        raise ValueError(
                            f"Handler '{hc.handler_name}' trigger references "
                            f"undefined variable '{trigger.variable_changed}'"
                        )

        return self

def load_spec_from_file(path: Path) -> HammerSpec:
    """
    Load and validate a Hammer spec from a YAML file.
    """
    with open(path, "r") as f:
        data = yaml.safe_load(f)
    return HammerSpec.model_validate(data)
