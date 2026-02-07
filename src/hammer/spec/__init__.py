"""HAMMER Spec Models — re-exports all public names for backwards compatibility.

Usage: ``from hammer.spec import HammerSpec, Node, ...`` continues to work.
"""

# Primitives
from hammer.spec.primitives import (
    NonEmptyStr,
    PhaseName,
    ExecutionPhaseName,
    VarType,
    OverlayKind,
    BindingMode,
    PrecedenceLayer,
    ExpectedRuns,
    ReachabilityExpectation,
    Protocol,
    FeatureFlags,
)

# Topology
from hammer.spec.topology import (
    NodeResources,
    ForwardedPort,
    Node,
    Dependency,
    Topology,
)

# Entrypoints
from hammer.spec.entrypoints import (
    ProvidedFile,
    Entrypoints,
)

# Variables & bindings
from hammer.spec.variables import (
    ServiceListenTarget,
    FirewallPortTarget,
    FilePatternTarget,
    FilePathTarget,
    FileModeTarget,
    FileOwnerTarget,
    BindingTarget,
    Binding,
    OverlayTarget,
    VariableDefaults,
    VariableContract,
    PrecedenceScenario,
)

# Contracts
from hammer.spec.contracts import (
    NodeSelector,
    PortRefVar,
    PortRef,
    PackageContract,
    PipPackageContract,
    ServiceContract,
    UserContract,
    GroupContract,
    FirewallPort,
    FirewallType,
    FirewallContract,
    FileContractItem,
    FilesContract,
    ReachabilityContract,
    HttpEndpointContract,
    ExternalHttpContract,
    OutputContract,
    BehavioralContracts,
)

# Overlays, handlers, policies
from hammer.spec.overlays import (
    TriggerFileChanged,
    TriggerTemplateChanged,
    TriggerVariableChanged,
    Trigger,
    NonTriggerNoop,
    NonTriggerUnrelatedFile,
    NonTrigger,
    HandlerTarget,
    ExpectedRunsSet,
    HandlerContract,
    IdempotenceEnforcement,
    IdempotencePolicy,
    VaultSpec,
    FailurePolicy,
    RebootConfig,
    PhaseOverlay,
    PhaseOverlays,
)

# Root
from hammer.spec.root import (
    HammerSpec,
    load_spec_from_file,
)

__all__ = [
    # Primitives
    "NonEmptyStr", "PhaseName", "ExecutionPhaseName", "VarType",
    "OverlayKind", "BindingMode", "PrecedenceLayer", "ExpectedRuns",
    "ReachabilityExpectation", "Protocol", "FeatureFlags",
    # Topology
    "NodeResources", "ForwardedPort", "Node", "Dependency", "Topology",
    # Entrypoints
    "ProvidedFile", "Entrypoints",
    # Variables
    "ServiceListenTarget", "FirewallPortTarget", "FilePatternTarget",
    "FilePathTarget", "FileModeTarget", "FileOwnerTarget", "BindingTarget",
    "Binding", "OverlayTarget", "VariableDefaults", "VariableContract",
    "PrecedenceScenario",
    # Contracts
    "NodeSelector", "PortRefVar", "PortRef",
    "PackageContract", "PipPackageContract", "ServiceContract",
    "UserContract", "GroupContract", "FirewallPort", "FirewallType",
    "FirewallContract", "FileContractItem", "FilesContract",
    "ReachabilityContract", "HttpEndpointContract", "ExternalHttpContract",
    "OutputContract", "BehavioralContracts",
    # Overlays
    "TriggerFileChanged", "TriggerTemplateChanged", "TriggerVariableChanged",
    "Trigger", "NonTriggerNoop", "NonTriggerUnrelatedFile", "NonTrigger",
    "HandlerTarget", "ExpectedRunsSet", "HandlerContract",
    "IdempotenceEnforcement", "IdempotencePolicy", "VaultSpec",
    "FailurePolicy", "RebootConfig", "PhaseOverlay", "PhaseOverlays",
    # Root
    "HammerSpec", "load_spec_from_file",
]
