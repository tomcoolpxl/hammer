"""Root HammerSpec model and loader."""

from typing import Any, List, Optional, Literal
from pathlib import Path

import yaml
from pydantic import BaseModel, Field, model_validator

from hammer.spec.primitives import NonEmptyStr, FeatureFlags
from hammer.spec.topology import Topology
from hammer.spec.entrypoints import Entrypoints
from hammer.spec.variables import VariableContract, PrecedenceScenario
from hammer.spec.contracts import (
    NodeSelector,
    PortRefVar,
    BehavioralContracts,
)
from hammer.spec.overlays import (
    TriggerVariableChanged,
    HandlerContract,
    IdempotencePolicy,
    VaultSpec,
    PhaseOverlays,
)
from hammer.validators import SafeIdentifier


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

        # Phase overlay sanity
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
        def check_port_ref(port_ref, context: str) -> None:
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
            for fw in self.behavioral_contracts.firewall or []:
                for port_spec in fw.open_ports:
                    check_port_ref(port_spec.port, "Firewall contract")

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
    """Load and validate a Hammer spec from a YAML file."""
    with open(path, "r") as f:
        data = yaml.safe_load(f)
    return HammerSpec.model_validate(data)
