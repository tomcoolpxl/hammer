from typing import Dict, List, Any, Literal, Tuple
from pydantic import BaseModel

from hammer.spec import (
    HammerSpec,
    NodeSelector,
    Topology,
)

ExecutionPhaseName = Literal["baseline", "mutation", "idempotence"]

# -------------------------
# Variable resolution
# -------------------------

class ResolvedVariable(BaseModel):
    name: str
    value: Any
    source: str  # group_vars, host_vars, inventory_vars, extra_vars, default


class PhaseVariablePlan(BaseModel):
    phase: ExecutionPhaseName
    # variable name -> resolved value
    resolved: Dict[str, ResolvedVariable]
    # raw overlay maps used by runner
    inventory_vars: Dict[str, Any]
    group_vars: Dict[str, Dict[str, Any]]
    host_vars: Dict[str, Dict[str, Any]]
    extra_vars: Dict[str, Any]


# -------------------------
# Binding plan
# -------------------------

class BindingCheck(BaseModel):
    variable: str
    binding_index: int
    binding_type: str
    binding_target: Dict[str, Any]
    expected_value: Any
    weight: float


# -------------------------
# Behavioral contract plan
# -------------------------

class PackageCheck(BaseModel):
    host_targets: List[str]
    name: str
    state: str
    weight: float


class PipPackageCheck(BaseModel):
    host_targets: List[str]
    name: str
    state: str
    python: str  # Python executable path
    weight: float


class ServiceCheck(BaseModel):
    host_targets: List[str]
    name: str
    enabled: bool
    running: bool
    weight: float


class UserCheck(BaseModel):
    host_targets: List[str]
    name: str
    exists: bool
    uid: int | None
    gid: int | None
    home: str | None
    shell: str | None
    groups: List[str] | None
    weight: float


class GroupCheck(BaseModel):
    host_targets: List[str]
    name: str
    exists: bool
    gid: int | None
    weight: float


class FirewallCheck(BaseModel):
    host_targets: List[str]
    ports: List[Dict[str, Any]]
    firewall_type: str = "firewalld"  # firewalld or iptables
    weight: float


class FileCheck(BaseModel):
    host_targets: List[str]
    items: List[Dict[str, Any]]
    weight: float


class ReachabilityCheck(BaseModel):
    from_host: str
    to_host: str
    protocol: str
    port: Any
    expectation: str
    weight: float


class HttpEndpointCheck(BaseModel):
    host_targets: List[str]  # Nodes to run the test from
    url: str
    method: str
    expected_status: int
    response_contains: str | None
    response_regex: str | None
    timeout_seconds: int
    weight: float


class ExternalHttpCheck(BaseModel):
    """HTTP check from external perspective (host or cross-VM)."""
    url: str
    method: str
    expected_status: int
    response_contains: str | None
    response_regex: str | None
    timeout_seconds: int
    from_host: bool  # If True, run from grading host
    from_node_targets: List[str] | None  # If from_host=False, list of VMs to run from
    weight: float


class OutputCheck(BaseModel):
    """Check for patterns in Ansible output."""
    pattern: str
    match_type: str  # "contains" or "regex"
    expected: bool  # True = should match, False = should NOT match
    description: str | None
    weight: float


# -------------------------
# Handler plan
# -------------------------

class HandlerPhaseExpectation(BaseModel):
    phase: ExecutionPhaseName
    expected_runs: str


class HandlerPlan(BaseModel):
    handler_name: str
    host_targets: List[str]
    service: str
    action: str
    expectations: Dict[ExecutionPhaseName, HandlerPhaseExpectation]
    weight: float


# -------------------------
# Phase contract plan
# -------------------------

class PhaseContractPlan(BaseModel):
    phase: ExecutionPhaseName
    bindings: List[BindingCheck]
    packages: List[PackageCheck]
    pip_packages: List[PipPackageCheck]
    services: List[ServiceCheck]
    users: List[UserCheck]
    groups: List[GroupCheck]
    firewall: List[FirewallCheck]
    files: List[FileCheck]
    reachability: List[ReachabilityCheck]
    http_endpoints: List[HttpEndpointCheck]
    external_http: List[ExternalHttpCheck]
    output_checks: List[OutputCheck]
    handlers: List[HandlerPlan]


# -------------------------
# Execution steps
# -------------------------

class ExecutionStep(BaseModel):
    name: str
    phase: ExecutionPhaseName
    kind: Literal["converge", "snapshot", "verify"]
    description: str


class ExecutionPlan(BaseModel):
    variables: Dict[ExecutionPhaseName, PhaseVariablePlan]
    contracts: Dict[ExecutionPhaseName, PhaseContractPlan]
    steps: List[ExecutionStep]


# -------------------------
# Utility Helpers
# -------------------------

def resolve_node_selector(selector: NodeSelector, topology: Topology) -> List[str]:
    if selector.host:
        return [selector.host]

    # group selector
    if selector.group:
        result = []
        for n in topology.nodes:
            if selector.group in n.groups:
                result.append(n.name)
        return result
    
    return []


# -------------------------
# Logic Implementation
# -------------------------

def build_phase_variable_plan(spec: HammerSpec, phase_name: ExecutionPhaseName) -> PhaseVariablePlan:

    # Map execution phase to spec overlay phase (idempotence -> mutation)
    spec_phase_name = phase_name
    if phase_name == "idempotence":
        spec_phase_name = "mutation"

    # We use getattr with string because spec_phase_name is guaranteed to be baseline or mutation
    phase_overlay = getattr(spec.phase_overlays, spec_phase_name, None)

    inventory_vars = phase_overlay.inventory_vars if phase_overlay and phase_overlay.inventory_vars else {}
    group_vars = phase_overlay.group_vars if phase_overlay and phase_overlay.group_vars else {}
    host_vars = phase_overlay.host_vars if phase_overlay and phase_overlay.host_vars else {}
    extra_vars = phase_overlay.extra_vars if phase_overlay and phase_overlay.extra_vars else {}

    resolved = {}

    for var in (spec.variable_contracts or []):
        value = var.defaults.student
        source = "default"

        if inventory_vars and var.name in inventory_vars:
            value = inventory_vars[var.name]
            source = "inventory_vars"

        # group vars override inventory
        if group_vars:
            for group_name in sorted(group_vars.keys()):
                gv = group_vars[group_name]
                if var.name in gv:
                    value = gv[var.name]
                    source = "group_vars"

        # host vars override group
        if host_vars:
            for host_name in sorted(host_vars.keys()):
                hv = host_vars[host_name]
                if var.name in hv:
                    value = hv[var.name]
                    source = "host_vars"

        # extra vars override all
        if extra_vars and var.name in extra_vars:
            value = extra_vars[var.name]
            source = "extra_vars"

        resolved[var.name] = ResolvedVariable(
            name=var.name,
            value=value,
            source=source
        )

    return PhaseVariablePlan(
        phase=phase_name,
        resolved=resolved,
        inventory_vars=inventory_vars,
        group_vars=group_vars,
        host_vars=host_vars,
        extra_vars=extra_vars,
    )


def build_binding_checks(spec: HammerSpec, phase_vars: PhaseVariablePlan) -> List[BindingCheck]:

    checks = []

    if not spec.variable_contracts:
        return checks

    for var in spec.variable_contracts:
        resolved_var = phase_vars.resolved[var.name]

        for idx, binding in enumerate(var.binding_targets):

            checks.append(
                BindingCheck(
                    variable=var.name,
                    binding_index=idx,
                    binding_type=binding.type,
                    binding_target=binding.target.model_dump(),
                    expected_value=resolved_var.value,
                    weight=binding.weight,
                )
            )

    return checks


class BehavioralChecks(BaseModel):
    """Container for all behavioral checks."""
    packages: List[PackageCheck]
    pip_packages: List[PipPackageCheck]
    services: List[ServiceCheck]
    users: List[UserCheck]
    groups: List[GroupCheck]
    firewall: List[FirewallCheck]
    files: List[FileCheck]
    reachability: List[ReachabilityCheck]
    http_endpoints: List[HttpEndpointCheck]
    external_http: List[ExternalHttpCheck]
    output_checks: List[OutputCheck]


def _applies_to_phase(contract_phases: List[str] | None, current_phase: str) -> bool:
    """Check if contract applies to current phase. None means all phases."""
    return contract_phases is None or current_phase in contract_phases


def build_behavioral_checks(spec: HammerSpec, topology: Topology, phase: ExecutionPhaseName) -> BehavioralChecks:

    packages: List[PackageCheck] = []
    pip_packages: List[PipPackageCheck] = []
    services: List[ServiceCheck] = []
    users: List[UserCheck] = []
    groups: List[GroupCheck] = []
    firewall: List[FirewallCheck] = []
    files: List[FileCheck] = []
    reachability: List[ReachabilityCheck] = []
    http_endpoints: List[HttpEndpointCheck] = []
    external_http: List[ExternalHttpCheck] = []
    output_checks: List[OutputCheck] = []

    bc = spec.behavioral_contracts
    if not bc:
        return BehavioralChecks(
            packages=packages,
            pip_packages=pip_packages,
            services=services,
            users=users,
            groups=groups,
            firewall=firewall,
            files=files,
            reachability=reachability,
            http_endpoints=http_endpoints,
            external_http=external_http,
            output_checks=output_checks,
        )

    if bc.packages:
        for p in bc.packages:
            if not _applies_to_phase(p.phases, phase):
                continue
            packages.append(
                PackageCheck(
                    host_targets=resolve_node_selector(p.node_selector, topology),
                    name=p.name,
                    state=p.state,
                    weight=p.weight,
                )
            )

    if bc.pip_packages:
        for p in bc.pip_packages:
            if not _applies_to_phase(p.phases, phase):
                continue
            pip_packages.append(
                PipPackageCheck(
                    host_targets=resolve_node_selector(p.node_selector, topology),
                    name=p.name,
                    state=p.state,
                    python=p.python or "/usr/bin/python3",
                    weight=p.weight,
                )
            )

    if bc.services:
        for s in bc.services:
            if not _applies_to_phase(s.phases, phase):
                continue
            services.append(
                ServiceCheck(
                    host_targets=resolve_node_selector(s.node_selector, topology),
                    name=s.name,
                    enabled=s.enabled,
                    running=s.running,
                    weight=s.weight,
                )
            )

    if bc.users:
        for u in bc.users:
            if not _applies_to_phase(u.phases, phase):
                continue
            users.append(
                UserCheck(
                    host_targets=resolve_node_selector(u.node_selector, topology),
                    name=u.name,
                    exists=u.exists,
                    uid=u.uid,
                    gid=u.gid,
                    home=u.home,
                    shell=u.shell,
                    groups=u.groups,
                    weight=u.weight,
                )
            )

    if bc.groups:
        for g in bc.groups:
            if not _applies_to_phase(g.phases, phase):
                continue
            groups.append(
                GroupCheck(
                    host_targets=resolve_node_selector(g.node_selector, topology),
                    name=g.name,
                    exists=g.exists,
                    gid=g.gid,
                    weight=g.weight,
                )
            )

    if bc.firewall:
        for f in bc.firewall:
            if not _applies_to_phase(f.phases, phase):
                continue
            firewall.append(
                FirewallCheck(
                    host_targets=resolve_node_selector(f.node_selector, topology),
                    ports=[port.model_dump() for port in f.open_ports],
                    firewall_type=f.firewall_type,
                    weight=f.weight,
                )
            )

    if bc.files:
        for fc in bc.files:
            if not _applies_to_phase(fc.phases, phase):
                continue
            files.append(
                FileCheck(
                    host_targets=resolve_node_selector(fc.node_selector, topology),
                    items=[item.model_dump() for item in fc.items],
                    weight=fc.weight,
                )
            )

    if bc.reachability:
        for r in bc.reachability:
            if not _applies_to_phase(r.phases, phase):
                continue
            reachability.append(
                ReachabilityCheck(
                    from_host=r.from_host,
                    to_host=r.to_host,
                    protocol=r.protocol,
                    port=r.port,
                    expectation=r.expectation,
                    weight=r.weight,
                )
            )

    if bc.http_endpoints:
        for h in bc.http_endpoints:
            if not _applies_to_phase(h.phases, phase):
                continue
            http_endpoints.append(
                HttpEndpointCheck(
                    host_targets=resolve_node_selector(h.node_selector, topology),
                    url=h.url,
                    method=h.method,
                    expected_status=h.expected_status,
                    response_contains=h.response_contains,
                    response_regex=h.response_regex,
                    timeout_seconds=h.timeout_seconds,
                    weight=h.weight,
                )
            )

    if bc.external_http:
        for ext in bc.external_http:
            if not _applies_to_phase(ext.phases, phase):
                continue
            external_http.append(
                ExternalHttpCheck(
                    url=ext.url,
                    method=ext.method,
                    expected_status=ext.expected_status,
                    response_contains=ext.response_contains,
                    response_regex=ext.response_regex,
                    timeout_seconds=ext.timeout_seconds,
                    from_host=ext.from_host,
                    from_node_targets=resolve_node_selector(ext.from_node, topology) if ext.from_node else None,
                    weight=ext.weight,
                )
            )

    if bc.output_checks:
        for out in bc.output_checks:
            if not _applies_to_phase(out.phases, phase):
                continue
            output_checks.append(
                OutputCheck(
                    pattern=out.pattern,
                    match_type=out.match_type,
                    expected=out.expected,
                    description=out.description,
                    weight=out.weight,
                )
            )

    return BehavioralChecks(
        packages=packages,
        pip_packages=pip_packages,
        services=services,
        users=users,
        groups=groups,
        firewall=firewall,
        files=files,
        reachability=reachability,
        http_endpoints=http_endpoints,
        external_http=external_http,
        output_checks=output_checks,
    )


def build_handler_plans(spec: HammerSpec, topology: Topology) -> List[HandlerPlan]:

    plans: List[HandlerPlan] = []

    if not spec.handler_contracts:
        return plans

    for hc in spec.handler_contracts:

        targets = resolve_node_selector(hc.node_selector, topology)

        expectations: Dict[ExecutionPhaseName, HandlerPhaseExpectation] = {
            "baseline": HandlerPhaseExpectation(
                phase="baseline",
                expected_runs=hc.expected_runs.baseline
            ),
            "mutation": HandlerPhaseExpectation(
                phase="mutation",
                expected_runs=hc.expected_runs.mutation
            ),
            "idempotence": HandlerPhaseExpectation(
                phase="idempotence",
                expected_runs=hc.expected_runs.idempotence
            ),
        }

        plans.append(
            HandlerPlan(
                handler_name=hc.handler_name,
                host_targets=targets,
                service=hc.handler_target.service,
                action=hc.handler_target.action,
                expectations=expectations,
                weight=hc.weight,
            )
        )

    return plans


def build_phase_contract_plan(spec: HammerSpec, topology: Topology, phase_name: ExecutionPhaseName, phase_vars: PhaseVariablePlan) -> PhaseContractPlan:

    bindings = build_binding_checks(spec, phase_vars)

    behavioral = build_behavioral_checks(spec, topology, phase_name)

    handlers = build_handler_plans(spec, topology)

    return PhaseContractPlan(
        phase=phase_name,
        bindings=bindings,
        packages=behavioral.packages,
        pip_packages=behavioral.pip_packages,
        services=behavioral.services,
        users=behavioral.users,
        groups=behavioral.groups,
        firewall=behavioral.firewall,
        files=behavioral.files,
        reachability=behavioral.reachability,
        http_endpoints=behavioral.http_endpoints,
        external_http=behavioral.external_http,
        output_checks=behavioral.output_checks,
        handlers=handlers,
    )


def build_execution_plan(spec: HammerSpec) -> ExecutionPlan:

    topology = spec.topology

    phases: List[ExecutionPhaseName] = ["baseline", "mutation", "idempotence"]

    variable_plans = {}
    contract_plans = {}

    for phase in phases:

        phase_vars = build_phase_variable_plan(spec, phase)

        variable_plans[phase] = phase_vars

        contract_plans[phase] = build_phase_contract_plan(
            spec,
            topology,
            phase,
            phase_vars
        )

    steps = []

    for phase in phases:

        steps.append(
            ExecutionStep(
                name=f"{phase}_converge",
                phase=phase,
                kind="converge",
                description=f"Run ansible converge for {phase}"
            )
        )

        steps.append(
            ExecutionStep(
                name=f"{phase}_snapshot",
                phase=phase,
                kind="snapshot",
                description=f"Export observed variable snapshots for {phase}"
            )
        )

        steps.append(
            ExecutionStep(
                name=f"{phase}_verify",
                phase=phase,
                kind="verify",
                description=f"Run pytest and runner verifications for {phase}"
            )
        )

    return ExecutionPlan(
        variables=variable_plans,
        contracts=contract_plans,
        steps=steps,
    )

