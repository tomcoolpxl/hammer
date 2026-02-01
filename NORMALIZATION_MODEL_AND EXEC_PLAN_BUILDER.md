Below is a production-grade phase normalization layer design with concrete Python models and a deterministic execution plan builder. This is the missing bridge between “validated spec” and “runner actions + test generation”.

Design goals:

* Convert abstract DSL into concrete, phase-resolved data.
* Resolve variable values per phase.
* Resolve precedence scenarios into concrete verification expectations.
* Precompute handler expectations.
* Produce a deterministic execution plan that runner and test generator consume.
* Avoid runtime interpretation of spec logic.

Assumes:

* You already loaded HammerSpec via the Pydantic model from the previous message.
* Python 3.10+
* No dynamic imports or reflection.

---

## Conceptual model

We generate three layers:

1. PhaseVariablePlan
   Resolved variables and overlays per phase.

2. PhaseContractPlan
   All contracts (behavioral, bindings, handlers, reachability) mapped to concrete host targets.

3. ExecutionPlan
   Ordered list of converge, snapshot, verify actions with metadata.

---

## Phase normalization models

```python
from typing import Dict, List, Any, Literal, Optional
from dataclasses import dataclass

PhaseName = Literal["baseline", "mutation", "idempotence"]


# -------------------------
# Variable resolution
# -------------------------

@dataclass(frozen=True)
class ResolvedVariable:
    name: str
    value: Any
    source: str  # group_vars, host_vars, inventory_vars, extra_vars, default


@dataclass
class PhaseVariablePlan:
    phase: PhaseName
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

@dataclass
class BindingCheck:
    variable: str
    binding_index: int
    binding_type: str
    binding_target: dict
    expected_value: Any
    weight: float


# -------------------------
# Behavioral contract plan
# -------------------------

@dataclass
class PackageCheck:
    host_targets: List[str]
    name: str
    state: str
    weight: float


@dataclass
class ServiceCheck:
    host_targets: List[str]
    name: str
    enabled: bool
    running: bool
    weight: float


@dataclass
class FirewallCheck:
    host_targets: List[str]
    ports: List[dict]
    weight: float


@dataclass
class FileCheck:
    host_targets: List[str]
    items: List[dict]
    weight: float


@dataclass
class ReachabilityCheck:
    from_host: str
    to_host: str
    protocol: str
    port: Any
    expectation: str
    weight: float


# -------------------------
# Handler plan
# -------------------------

@dataclass
class HandlerPhaseExpectation:
    phase: PhaseName
    expected_runs: str


@dataclass
class HandlerPlan:
    handler_name: str
    host_targets: List[str]
    service: str
    action: str
    expectations: Dict[PhaseName, HandlerPhaseExpectation]
    weight: float


# -------------------------
# Phase contract plan
# -------------------------

@dataclass
class PhaseContractPlan:
    phase: PhaseName
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

@dataclass
class ExecutionStep:
    name: str
    phase: PhaseName
    kind: Literal["converge", "snapshot", "verify"]
    description: str


@dataclass
class ExecutionPlan:
    variables: Dict[PhaseName, PhaseVariablePlan]
    contracts: Dict[PhaseName, PhaseContractPlan]
    steps: List[ExecutionStep]
```

---

## Utility helpers

These resolve node selectors and overlay precedence.

```python
def resolve_node_selector(selector, topology):
    nodes = topology.nodes

    if selector.host:
        return [selector.host]

    # group selector
    result = []
    for n in nodes:
        if selector.group in n.groups:
            result.append(n.name)

    return result


def merge_overlay_maps(*maps):
    merged = {}
    for m in maps:
        if m:
            merged.update(m)
    return merged
```

---

## Phase variable resolution

Overlay precedence (grading):

1. defaults.student
2. inventory_vars
3. group_vars
4. host_vars
5. extra_vars

This is grading-time precedence only.

```python
def build_phase_variable_plan(spec, phase_name: PhaseName):

    phase_overlay = getattr(spec.phase_overlays, phase_name, None)

    inventory_vars = phase_overlay.inventory_vars if phase_overlay else {}
    group_vars = phase_overlay.group_vars if phase_overlay else {}
    host_vars = phase_overlay.host_vars if phase_overlay else {}
    extra_vars = phase_overlay.extra_vars if phase_overlay else {}

    resolved = {}

    for var in spec.variable_contracts:
        value = var.defaults.student
        source = "default"

        if inventory_vars and var.name in inventory_vars:
            value = inventory_vars[var.name]
            source = "inventory_vars"

        # group vars override inventory
        for gv in (group_vars or {}).values():
            if var.name in gv:
                value = gv[var.name]
                source = "group_vars"

        # host vars override group
        for hv in (host_vars or {}).values():
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
        inventory_vars=inventory_vars or {},
        group_vars=group_vars or {},
        host_vars=host_vars or {},
        extra_vars=extra_vars or {},
    )
```

---

## Binding normalization

Convert variable contracts into concrete binding checks for the phase.

```python
def build_binding_checks(spec, phase_vars: PhaseVariablePlan):

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
```

---

## Behavioral contract normalization

```python
def build_behavioral_checks(spec, topology):

    packages = []
    services = []
    firewall = []
    files = []
    reachability = []

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
```

---

## Handler normalization

```python
def build_handler_plans(spec, topology):

    plans = []

    if not spec.handler_contracts:
        return plans

    for hc in spec.handler_contracts:

        targets = resolve_node_selector(hc.node_selector, topology)

        expectations = {
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
```

---

## Phase contract plan builder

```python
def build_phase_contract_plan(spec, topology, phase_name: PhaseName, phase_vars):

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
```

---

## Execution plan builder

This is the top-level function the generator and runner consume.

```python
def build_execution_plan(spec):

    topology = spec.topology

    phases = ["baseline", "mutation", "idempotence"]

    variable_plans = {}
    contract_plans = {}

    for phase in phases:

        # Idempotence uses mutation overlays by definition
        overlay_phase = phase
        if phase == "idempotence":
            overlay_phase = "mutation"

        phase_vars = build_phase_variable_plan(spec, overlay_phase)

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
```

---

## What you now have

With this layer implemented:

* The runner never reads the raw spec.
* Tests never parse DSL directly.
* All values are phase-resolved and deterministic.
* Handler expectations are explicit per phase.
* Overlay logic is centralized and testable.

This is the point where you can:

* Unit test normalization without any Ansible.
* Generate pytest tests from PhaseContractPlan.
* Generate snapshot playbooks from PhaseVariablePlan.
* Drive the runner from ExecutionPlan.steps.

---

## Critical design advantage

By separating:

Spec → Normalized Plan → Runner/Test Generation

You eliminate a large class of logic duplication bugs and make the system evolvable.

---

## Next recommended component

The next hard part is:

* Pytest generation layer:

  * convert BindingCheck, PackageCheck, ServiceCheck, ReachabilityCheck into concrete pytest + testinfra code
  * generate stable test IDs
  * produce JUnit-friendly output

If you want to continue, say:

Generate pytest/testinfra generator layer.
