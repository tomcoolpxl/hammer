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


class ServiceCheck(BaseModel):
    host_targets: List[str]
    name: str
    enabled: bool
    running: bool
    weight: float


class FirewallCheck(BaseModel):
    host_targets: List[str]
    ports: List[Dict[str, Any]]
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
    services: List[ServiceCheck]
    firewall: List[FirewallCheck]
    files: List[FileCheck]
    reachability: List[ReachabilityCheck]
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

    for var in spec.variable_contracts:
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


def build_behavioral_checks(spec: HammerSpec, topology: Topology) -> Tuple[List[PackageCheck], List[ServiceCheck], List[FirewallCheck], List[FileCheck], List[ReachabilityCheck]]:

    packages: List[PackageCheck] = []
    services: List[ServiceCheck] = []
    firewall: List[FirewallCheck] = []
    files: List[FileCheck] = []
    reachability: List[ReachabilityCheck] = []

    bc = spec.behavioral_contracts
    if not bc:
        return packages, services, firewall, files, reachability

    if bc.packages:
        for p in bc.packages:
            packages.append(
                PackageCheck(
                    host_targets=resolve_node_selector(p.node_selector, topology),
                    name=p.name,
                    state=p.state,
                    weight=p.weight,
                )
            )

    if bc.services:
        for s in bc.services:
            services.append(
                ServiceCheck(
                    host_targets=resolve_node_selector(s.node_selector, topology),
                    name=s.name,
                    enabled=s.enabled,
                    running=s.running,
                    weight=s.weight,
                )
            )

    if bc.firewall:
        for f in bc.firewall:
            firewall.append(
                FirewallCheck(
                    host_targets=resolve_node_selector(f.node_selector, topology),
                    ports=[port.model_dump() for port in f.open_ports],
                    weight=f.weight,
                )
            )

    if bc.files:
        for fc in bc.files:
            files.append(
                FileCheck(
                    host_targets=resolve_node_selector(fc.node_selector, topology),
                    items=[item.model_dump() for item in fc.items],
                    weight=fc.weight,
                )
            )

    if bc.reachability:
        for r in bc.reachability:
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

    return packages, services, firewall, files, reachability


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

    packages, services, firewall, files, reachability = \
        build_behavioral_checks(spec, topology)

    handlers = build_handler_plans(spec, topology)

    return PhaseContractPlan(
        phase=phase_name,
        bindings=bindings,
        packages=packages,
        services=services,
        firewall=firewall,
        files=files,
        reachability=reachability,
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

