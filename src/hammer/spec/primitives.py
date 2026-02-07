"""Common type aliases and primitives for HAMMER spec models."""

from typing import Literal

from pydantic import BaseModel

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


class FeatureFlags(BaseModel):
    vault: bool = False
    selinux: bool = False
    handlers: bool = True
    reachability: bool = False
