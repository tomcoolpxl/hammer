"""Regression tests for edge cases in spec validation.

These tests ensure robust handling of invalid or edge-case specifications.
"""

import sys
from pathlib import Path
import pytest
import yaml
from pydantic import ValidationError

PROJECT_ROOT = Path(__file__).parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from hammer.spec import load_spec_from_file, HammerSpec

FIXTURES_DIR = PROJECT_ROOT / "tests" / "fixtures"


def load_base_spec() -> dict:
    """Load the valid full spec as a base for modifications."""
    with open(FIXTURES_DIR / "valid_full.yaml", "r") as f:
        return yaml.safe_load(f)


class TestMissingVariables:
    """Tests for missing or undefined variable references."""

    def test_port_ref_var_references_undefined_variable(self):
        """PortRefVar in behavioral contracts must reference a defined variable."""
        data = load_base_spec()

        # Reference a variable that doesn't exist in variable_contracts
        data["behavioral_contracts"]["firewall"][0]["open_ports"][0]["port"] = {
            "var": "undefined_port_var"
        }

        with pytest.raises(ValidationError) as exc_info:
            HammerSpec.model_validate(data)

        assert "undefined_port_var" in str(exc_info.value)

    def test_reachability_port_ref_undefined(self):
        """Reachability port reference must use a defined variable."""
        data = load_base_spec()

        data["behavioral_contracts"]["reachability"][0]["port"] = {
            "var": "nonexistent_var"
        }

        with pytest.raises(ValidationError) as exc_info:
            HammerSpec.model_validate(data)

        assert "nonexistent_var" in str(exc_info.value)

    def test_handler_variable_changed_undefined(self):
        """Handler trigger condition referencing undefined variable."""
        data = load_base_spec()

        data["handler_contracts"][0]["trigger_conditions"] = [
            {"variable_changed": "undefined_variable"}
        ]

        with pytest.raises(ValidationError) as exc_info:
            HammerSpec.model_validate(data)

        assert "undefined_variable" in str(exc_info.value)


class TestInvalidBindingTargets:
    """Tests for invalid binding target configurations."""

    def test_overlay_target_nonexistent_group(self):
        """Overlay target referencing a non-existent group."""
        data = load_base_spec()

        data["variable_contracts"][0]["grading_overlay_targets"] = [
            {"overlay_kind": "group_vars", "target_name": "nonexistent_group"}
        ]

        with pytest.raises(ValidationError) as exc_info:
            HammerSpec.model_validate(data)

        assert "nonexistent_group" in str(exc_info.value)

    def test_overlay_target_nonexistent_host(self):
        """Overlay target referencing a non-existent host."""
        data = load_base_spec()

        data["variable_contracts"][0]["grading_overlay_targets"] = [
            {"overlay_kind": "host_vars", "target_name": "nonexistent_host"}
        ]

        with pytest.raises(ValidationError) as exc_info:
            HammerSpec.model_validate(data)

        assert "nonexistent_host" in str(exc_info.value)

    def test_node_selector_nonexistent_group(self):
        """Node selector referencing a non-existent group."""
        data = load_base_spec()

        data["behavioral_contracts"]["packages"][0]["node_selector"] = {
            "group": "phantom_group"
        }

        with pytest.raises(ValidationError) as exc_info:
            HammerSpec.model_validate(data)

        assert "Unknown group in selector: phantom_group" in str(exc_info.value)

    def test_node_selector_nonexistent_host(self):
        """Node selector referencing a non-existent host."""
        data = load_base_spec()

        data["behavioral_contracts"]["services"][0]["node_selector"] = {
            "host": "phantom_host"
        }

        with pytest.raises(ValidationError) as exc_info:
            HammerSpec.model_validate(data)

        assert "Unknown host in selector: phantom_host" in str(exc_info.value)


class TestReachabilityValidation:
    """Tests for reachability contract validation."""

    def test_reachability_from_host_nonexistent(self):
        """Reachability from_host must exist in topology."""
        data = load_base_spec()

        data["behavioral_contracts"]["reachability"][0]["from_host"] = "ghost_host"

        with pytest.raises(ValidationError) as exc_info:
            HammerSpec.model_validate(data)

        assert "ghost_host" in str(exc_info.value)

    def test_reachability_to_host_nonexistent(self):
        """Reachability to_host must exist in topology."""
        data = load_base_spec()

        data["behavioral_contracts"]["reachability"][0]["to_host"] = "missing_host"

        with pytest.raises(ValidationError) as exc_info:
            HammerSpec.model_validate(data)

        assert "missing_host" in str(exc_info.value)


class TestDependencyValidation:
    """Tests for topology dependency validation."""

    def test_dependency_from_host_nonexistent(self):
        """Dependency from_host must exist in topology."""
        data = load_base_spec()

        data["topology"]["dependencies"][0]["from_host"] = "fake_host"

        with pytest.raises(ValidationError) as exc_info:
            HammerSpec.model_validate(data)

        assert "fake_host" in str(exc_info.value)

    def test_dependency_to_host_nonexistent(self):
        """Dependency to_host must exist in topology."""
        data = load_base_spec()

        data["topology"]["dependencies"][0]["to_host"] = "imaginary_host"

        with pytest.raises(ValidationError) as exc_info:
            HammerSpec.model_validate(data)

        assert "imaginary_host" in str(exc_info.value)


class TestHandlerContracts:
    """Tests for handler contract validation."""

    def test_handler_node_selector_invalid_group(self):
        """Handler node selector must reference valid group."""
        data = load_base_spec()

        data["handler_contracts"][0]["node_selector"] = {"group": "bad_group"}

        with pytest.raises(ValidationError) as exc_info:
            HammerSpec.model_validate(data)

        assert "Unknown group in selector: bad_group" in str(exc_info.value)

    def test_handler_without_feature_enabled(self):
        """Handler contracts require features.handlers=true."""
        data = load_base_spec()
        data["features"]["handlers"] = False

        with pytest.raises(ValidationError) as exc_info:
            HammerSpec.model_validate(data)

        assert "Handler contracts present but features.handlers is false" in str(exc_info.value)


class TestPrecedenceScenarios:
    """Tests for precedence scenario validation."""

    def test_precedence_unknown_variable(self):
        """Precedence scenario must reference a defined variable."""
        data = load_base_spec()

        data["precedence_scenarios"][0]["variable"] = "mystery_var"

        with pytest.raises(ValidationError) as exc_info:
            HammerSpec.model_validate(data)

        assert "unknown variable 'mystery_var'" in str(exc_info.value)

    def test_precedence_binding_index_out_of_range(self):
        """Precedence binding index must be valid for the variable."""
        data = load_base_spec()

        # http_port has 3 bindings (index 0, 1, 2)
        data["precedence_scenarios"][0]["bindings_to_verify"] = [0, 1, 99]

        with pytest.raises(ValidationError) as exc_info:
            HammerSpec.model_validate(data)

        assert "index 99 out of range" in str(exc_info.value)

    def test_precedence_expected_winner_not_in_layers(self):
        """Expected winner must be in the layers list."""
        data = load_base_spec()

        data["precedence_scenarios"][0]["layers"] = ["group_vars", "host_vars"]
        data["precedence_scenarios"][0]["expected_winner"] = "extra_vars"

        with pytest.raises(ValidationError) as exc_info:
            HammerSpec.model_validate(data)

        assert "expected_winner must be present in layers list" in str(exc_info.value)


class TestPhaseOverlays:
    """Tests for phase overlay validation."""

    def test_missing_baseline_overlay(self):
        """Baseline phase_overlays must be defined."""
        data = load_base_spec()
        data["phase_overlays"]["baseline"] = None

        with pytest.raises(ValidationError) as exc_info:
            HammerSpec.model_validate(data)

        assert "Baseline phase_overlays must be defined" in str(exc_info.value)

    def test_variable_with_bindings_not_in_overlays(self):
        """Variables with bindings must appear in phase_overlays."""
        data = load_base_spec()

        # Remove http_port from all overlays
        data["phase_overlays"]["baseline"]["group_vars"]["web"].pop("http_port", None)
        data["phase_overlays"]["mutation"]["group_vars"]["web"].pop("http_port", None)
        data["phase_overlays"]["mutation"]["extra_vars"].pop("http_port", None)

        with pytest.raises(ValidationError) as exc_info:
            HammerSpec.model_validate(data)

        assert "Variable 'http_port' has bindings but is never set in phase_overlays" in str(exc_info.value)


class TestTopologyValidation:
    """Tests for topology validation."""

    def test_duplicate_node_names(self):
        """Duplicate node names are rejected."""
        data = load_base_spec()
        data["topology"]["nodes"].append(data["topology"]["nodes"][0].copy())

        with pytest.raises(ValidationError) as exc_info:
            HammerSpec.model_validate(data)

        assert "Duplicate node names" in str(exc_info.value)

    def test_empty_node_list(self):
        """At least one node must be defined."""
        data = load_base_spec()
        data["topology"]["nodes"] = []

        with pytest.raises(ValidationError) as exc_info:
            HammerSpec.model_validate(data)

        # Pydantic will require at least one item or there will be issues
        # with other validations that depend on nodes existing


class TestVariableContractValidation:
    """Tests for variable contract validation."""

    def test_binding_targets_need_two_allowed_values(self):
        """Variables with bindings need at least 2 allowed values for mutation testing."""
        data = load_base_spec()

        data["variable_contracts"][0]["allowed_values"] = [8080]  # Only one value

        with pytest.raises(ValidationError) as exc_info:
            HammerSpec.model_validate(data)

        assert "has bindings but less than 2 allowed_values" in str(exc_info.value)

    def test_variable_must_have_overlay_target(self):
        """Variables must declare at least one grading_overlay_target."""
        data = load_base_spec()

        data["variable_contracts"][0]["grading_overlay_targets"] = []

        with pytest.raises(ValidationError) as exc_info:
            HammerSpec.model_validate(data)

        assert "must declare at least one grading_overlay_target" in str(exc_info.value)


class TestResourceLimits:
    """Tests for resource constraint validation."""

    def test_cpu_too_low(self):
        """CPU count must be at least 1."""
        data = load_base_spec()
        data["topology"]["nodes"][0]["resources"]["cpu"] = 0

        with pytest.raises(ValidationError) as exc_info:
            HammerSpec.model_validate(data)

        assert "greater than or equal to 1" in str(exc_info.value).lower()

    def test_ram_too_low(self):
        """RAM must be at least 256 MB."""
        data = load_base_spec()
        data["topology"]["nodes"][0]["resources"]["ram_mb"] = 100

        with pytest.raises(ValidationError) as exc_info:
            HammerSpec.model_validate(data)

        assert "greater than or equal to 256" in str(exc_info.value).lower()

    def test_port_out_of_range(self):
        """Port numbers must be within valid range."""
        data = load_base_spec()

        # Add a forwarded port with invalid port number
        data["topology"]["forwarded_ports"] = [
            {"host_port": 70000, "guest_port": 80, "protocol": "tcp"}
        ]

        with pytest.raises(ValidationError) as exc_info:
            HammerSpec.model_validate(data)

        assert "less than or equal to 65535" in str(exc_info.value).lower()
