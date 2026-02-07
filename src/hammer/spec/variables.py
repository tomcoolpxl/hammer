"""Variable contract and binding models for HAMMER spec."""

from typing import Any, List, Optional, Union, Literal

from pydantic import BaseModel, Field, model_validator

from hammer.validators import SafeIdentifier, SafePath, SafePattern, SafeZone
from hammer.spec.primitives import (
    NonEmptyStr,
    PhaseName,
    VarType,
    OverlayKind,
    BindingMode,
    PrecedenceLayer,
    Protocol,
)


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
