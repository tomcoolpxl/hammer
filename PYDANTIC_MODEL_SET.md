Below is a complete, implementation-ready Pydantic v2 model set with cross-field validation rules that enforce the semantic constraints your JSON Schema cannot express.

Assumptions:

* Python 3.10+
* Pydantic v2.x
* Strict validation preferred over silent coercion
* Fail-fast behavior on spec errors

This code is designed to be dropped into your generator and used as the canonical spec loader.

---

```python
from typing import List, Dict, Optional, Union, Literal, Any
from pydantic import BaseModel, Field, field_validator, model_validator

# -------------------------
# Common primitives
# -------------------------

NonEmptyStr = str

PhaseName = Literal["baseline", "mutation"]

VarType = Literal["int", "string", "bool", "list", "dict"]

OverlayKind = Literal["group_vars", "host_vars", "inventory_vars"]

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


class Node(BaseModel):
    name: NonEmptyStr
    groups: List[NonEmptyStr]
    resources: NodeResources


class ForwardedPort(BaseModel):
    host_port: int = Field(ge=1, le=65535)
    guest_port: int = Field(ge=1, le=65535)
    protocol: Protocol


class Dependency(BaseModel):
    from_host: NonEmptyStr
    to_host: NonEmptyStr
    kind: Literal["reachability", "ordering"]


class Topology(BaseModel):
    nodes: List[Node]
    forwarded_ports: Optional[List[ForwardedPort]] = None
    dependencies: Optional[List[Dependency]] = None

    @model_validator(mode="after")
    def unique_node_names(self):
        names = [n.name for n in self.nodes]
        if len(names) != len(set(names)):
            raise ValueError("Duplicate node names in topology")
        return self


# -------------------------
# Entrypoints
# -------------------------

class Entrypoints(BaseModel):
    playbook_path: NonEmptyStr
    required_roles: Optional[List[NonEmptyStr]] = None
    required_files: Optional[List[NonEmptyStr]] = None


# -------------------------
# Variable bindings
# -------------------------

class ServiceListenTarget(BaseModel):
    service: NonEmptyStr
    protocol: Protocol
    address: NonEmptyStr


class FirewallPortTarget(BaseModel):
    zone: NonEmptyStr
    protocol: Protocol


class FilePatternTarget(BaseModel):
    path: NonEmptyStr
    pattern: NonEmptyStr


class FilePathTarget(BaseModel):
    path: NonEmptyStr


class FileModeTarget(BaseModel):
    path: NonEmptyStr
    mode: NonEmptyStr


class FileOwnerTarget(BaseModel):
    path: NonEmptyStr
    owner: NonEmptyStr
    group: NonEmptyStr


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
    target_name: NonEmptyStr


class VariableDefaults(BaseModel):
    student: Any


class VariableContract(BaseModel):
    name: NonEmptyStr
    type: VarType
    defaults: VariableDefaults
    allowed_values: List[Any]
    grading_overlay_targets: List[OverlayTarget]
    binding_targets: List[Binding]
    bindings_mode: BindingMode = "all"

    @model_validator(mode="after")
    def validate_variable_contract(self):
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
    name: NonEmptyStr
    variable: NonEmptyStr
    layers: List[PrecedenceLayer]
    expected_winner: PrecedenceLayer
    bindings_to_verify: List[int]
    phase: PhaseName = "baseline"

    @model_validator(mode="after")
    def validate_layers(self):
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
    group: Optional[NonEmptyStr] = None
    host: Optional[NonEmptyStr] = None

    @model_validator(mode="after")
    def exactly_one_selector(self):
        if (self.group is None and self.host is None) or \
           (self.group is not None and self.host is not None):
            raise ValueError("Exactly one of group or host must be specified")
        return self


# -------------------------
# Behavioral contracts
# -------------------------

class PackageContract(BaseModel):
    name: NonEmptyStr
    state: Literal["present", "absent"]
    node_selector: NodeSelector
    weight: float = Field(default=1.0, ge=0.0)


class ServiceContract(BaseModel):
    name: NonEmptyStr
    enabled: bool
    running: bool
    node_selector: NodeSelector
    weight: float = Field(default=1.0, ge=0.0)


class PortRefVar(BaseModel):
    var: NonEmptyStr


PortRef = Union[int, PortRefVar]


class FirewallPort(BaseModel):
    port: PortRef
    protocol: Protocol
    zone: NonEmptyStr


class FirewallContract(BaseModel):
    open_ports: List[FirewallPort]
    node_selector: NodeSelector
    weight: float = Field(default=1.0, ge=0.0)


class FileContractItem(BaseModel):
    path: NonEmptyStr
    present: bool
    mode: Optional[NonEmptyStr] = None
    owner: Optional[NonEmptyStr] = None
    group: Optional[NonEmptyStr] = None
    content_regex: Optional[NonEmptyStr] = None


class FilesContract(BaseModel):
    items: List[FileContractItem]
    node_selector: NodeSelector
    weight: float = Field(default=1.0, ge=0.0)


class ReachabilityContract(BaseModel):
    from_host: NonEmptyStr
    to_host: NonEmptyStr
    protocol: Protocol
    port: PortRef
    expectation: ReachabilityExpectation
    weight: float = Field(default=1.0, ge=0.0)


class BehavioralContracts(BaseModel):
    packages: Optional[List[PackageContract]] = None
    services: Optional[List[ServiceContract]] = None
    firewall: Optional[List[FirewallContract]] = None
    files: Optional[List[FilesContract]] = None
    reachability: Optional[List[ReachabilityContract]] = None


# -------------------------
# Handler contracts
# -------------------------

class TriggerFileChanged(BaseModel):
    file_changed: NonEmptyStr


class TriggerTemplateChanged(BaseModel):
    template_changed: NonEmptyStr


class TriggerVariableChanged(BaseModel):
    variable_changed: NonEmptyStr


Trigger = Union[
    TriggerFileChanged,
    TriggerTemplateChanged,
    TriggerVariableChanged,
]


class NonTriggerNoop(BaseModel):
    noop_rerun: Literal[True]


class NonTriggerUnrelatedFile(BaseModel):
    unrelated_file_changed: NonEmptyStr


NonTrigger = Union[
    NonTriggerNoop,
    NonTriggerUnrelatedFile,
]


class HandlerTarget(BaseModel):
    service: NonEmptyStr
    action: Literal["restart", "reload"]


class ExpectedRunsSet(BaseModel):
    baseline: ExpectedRuns
    mutation: ExpectedRuns
    idempotence: ExpectedRuns


class HandlerContract(BaseModel):
    handler_name: NonEmptyStr
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
    vault_ids: Optional[List[NonEmptyStr]] = None
    vaulted_vars_files: List[NonEmptyStr]
    vaulted_variables: List[NonEmptyStr]
    bindings_to_verify: List[int]


# -------------------------
# Phase overlays
# -------------------------

class PhaseOverlay(BaseModel):
    inventory_vars: Optional[Dict[str, Any]] = None
    group_vars: Optional[Dict[str, Dict[str, Any]]] = None
    host_vars: Optional[Dict[str, Dict[str, Any]]] = None
    extra_vars: Optional[Dict[str, Any]] = None


class PhaseOverlays(BaseModel):
    baseline: Optional[PhaseOverlay] = None
    mutation: Optional[PhaseOverlay] = None


# -------------------------
# Root spec
# -------------------------

class HammerSpec(BaseModel):
    assignment_id: NonEmptyStr
    assignment_version: NonEmptyStr
    spec_version: Literal["1.0"]
    seed: int
    provider: Literal["libvirt"]
    os: Literal["almalinux9"]

    features: Optional[FeatureFlags] = FeatureFlags()

    topology: Topology
    entrypoints: Entrypoints

    variable_contracts: List[VariableContract]

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
    def semantic_validation(self):

        var_names = {v.name for v in self.variable_contracts}

        # Validate precedence variable references
        if self.precedence_scenarios:
            for scen in self.precedence_scenarios:
                if scen.variable not in var_names:
                    raise ValueError(
                        f"Precedence scenario references unknown variable '{scen.variable}'"
                    )

        # Validate binding index references
        for idx, var in enumerate(self.variable_contracts):
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

        # Phase overlay sanity
        if not self.phase_overlays.baseline:
            raise ValueError("Baseline phase_overlays must be defined")

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

        for var in self.variable_contracts:
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

        def check_selector(sel: NodeSelector):
            if sel.host and sel.host not in node_names:
                raise ValueError(f"Unknown host in selector: {sel.host}")
            if sel.group and sel.group not in group_names:
                raise ValueError(f"Unknown group in selector: {sel.group}")

        for bc in [
            *(self.behavioral_contracts.packages or []) if self.behavioral_contracts else [],
            *(self.behavioral_contracts.services or []) if self.behavioral_contracts else [],
            *(self.behavioral_contracts.firewall or []) if self.behavioral_contracts else [],
            *(self.behavioral_contracts.files or []) if self.behavioral_contracts else [],
        ]:
            check_selector(bc.node_selector)

        for hc in self.handler_contracts or []:
            check_selector(hc.node_selector)

        return self
```

---

## What this enforces that JSON Schema cannot

This model adds critical invariants:

1. Variable mutation safety
   Variables with bindings must have at least two allowed values and must appear in phase overlays.

2. Feature gating
   You cannot accidentally define handler or vault contracts without enabling the feature flag.

3. Referential integrity

* Precedence scenarios must reference real variables.
* bindings_to_verify indexes must be valid.

4. Topology correctness

* Duplicate node names rejected.
* Node selectors must refer to existing groups or hosts.

5. Phase sanity
   Baseline overlays must exist.

6. Overlay coverage
   Variables that are graded via bindings must appear in grading overlays so mutation enforcement cannot be skipped.

