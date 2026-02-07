"""Handler, overlay, and policy models for HAMMER spec."""

from typing import Any, Dict, List, Optional, Union, Literal

from pydantic import BaseModel, Field

from hammer.validators import SafeIdentifier, SafePath
from hammer.spec.primitives import NonEmptyStr, ExpectedRuns
from hammer.spec.contracts import NodeSelector


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
    vault_password: NonEmptyStr
    vault_ids: Optional[List[NonEmptyStr]] = None
    vaulted_vars_files: List[NonEmptyStr]
    vaulted_variables: List[NonEmptyStr]
    bindings_to_verify: List[int]


# -------------------------
# Failure policy
# -------------------------

class FailurePolicy(BaseModel):
    """Policy for handling expected failures during converge."""
    allow_failures: bool = False
    max_failures: Optional[int] = None
    expected_patterns: Optional[List[NonEmptyStr]] = None


# -------------------------
# Reboot configuration
# -------------------------

class RebootConfig(BaseModel):
    """Configuration for rebooting nodes after converge, before tests."""
    enabled: bool = False
    nodes: Optional[List[SafeIdentifier]] = None
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
