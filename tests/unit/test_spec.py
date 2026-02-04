import sys
from pathlib import Path
import pytest
from pydantic import ValidationError

# Ensure src is in path so we can import hammer
PROJECT_ROOT = Path(__file__).parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from hammer.spec import load_spec_from_file, HammerSpec

FIXTURES_DIR = PROJECT_ROOT / "tests" / "fixtures"

def test_load_valid_full_spec():
    """Test loading a fully valid reference spec."""
    spec_path = FIXTURES_DIR / "valid_full.yaml"
    spec = load_spec_from_file(spec_path)
    
    assert spec.assignment_id == "hammer-nginx-port"
    assert spec.seed == 1337
    assert len(spec.topology.nodes) == 2
    assert spec.features.handlers is True
    
    # Check variable contract
    http_port = next(v for v in spec.variable_contracts if v.name == "http_port")
    assert http_port.type == "int"
    assert len(http_port.binding_targets) == 3

def test_invalid_logic_missing_overlay():
    """Test that a variable with bindings MUST appear in phase_overlays."""
    spec_path = FIXTURES_DIR / "invalid_logic.yaml"
    
    with pytest.raises(ValidationError) as exc_info:
        load_spec_from_file(spec_path)
    
    # The error message should mention the variable name and the specific rule
    error_msg = str(exc_info.value)
    assert "Variable 'broken_var' has bindings but is never set in phase_overlays" in error_msg

def test_feature_flag_enforcement():
    """Test that defining handler_contracts requires features.handlers=true."""
    # We'll construct a minimal failing spec dict directly to avoid needing another fixture file
    # for every edge case.
    
    # Load valid spec as base
    with open(FIXTURES_DIR / "valid_full.yaml", "r") as f:
        import yaml
        data = yaml.safe_load(f)
    
    # Disable handlers feature but keep handler_contracts
    data["features"]["handlers"] = False
    
    with pytest.raises(ValidationError) as exc_info:
        HammerSpec.model_validate(data)
        
    assert "Handler contracts present but features.handlers is false" in str(exc_info.value)

def test_topology_duplicate_nodes():
    """Test that duplicate node names are rejected."""
    with open(FIXTURES_DIR / "valid_full.yaml", "r") as f:
        import yaml
        data = yaml.safe_load(f)

    # Duplicate web1
    data["topology"]["nodes"].append(data["topology"]["nodes"][0])

    with pytest.raises(ValidationError) as exc_info:
        HammerSpec.model_validate(data)

    assert "Duplicate node names in topology" in str(exc_info.value)


# -------------------------
# PE4 Support Tests
# -------------------------

def test_phases_field_on_behavioral_contracts():
    """Test that behavioral contracts can have phases field."""
    with open(FIXTURES_DIR / "valid_full.yaml", "r") as f:
        import yaml
        data = yaml.safe_load(f)

    # Add phases to a service contract
    data["behavioral_contracts"]["services"][0]["phases"] = ["baseline", "mutation"]

    spec = HammerSpec.model_validate(data)
    assert spec.behavioral_contracts.services[0].phases == ["baseline", "mutation"]


def test_phases_field_default_none():
    """Test that phases field defaults to None (all phases)."""
    with open(FIXTURES_DIR / "valid_full.yaml", "r") as f:
        import yaml
        data = yaml.safe_load(f)

    spec = HammerSpec.model_validate(data)
    # By default, no phases specified means all phases
    assert spec.behavioral_contracts.services[0].phases is None


def test_reboot_config_valid():
    """Test that RebootConfig can be added to phase overlays."""
    with open(FIXTURES_DIR / "valid_full.yaml", "r") as f:
        import yaml
        data = yaml.safe_load(f)

    # Add reboot config to mutation phase
    data["phase_overlays"]["mutation"]["reboot"] = {
        "enabled": True,
        "nodes": ["web1"],
        "timeout": 120,
        "poll_interval": 5,
    }

    spec = HammerSpec.model_validate(data)
    assert spec.phase_overlays.mutation.reboot is not None
    assert spec.phase_overlays.mutation.reboot.enabled is True
    assert spec.phase_overlays.mutation.reboot.nodes == ["web1"]
    assert spec.phase_overlays.mutation.reboot.timeout == 120


def test_reboot_config_invalid_node():
    """Test that reboot config with unknown node is rejected."""
    with open(FIXTURES_DIR / "valid_full.yaml", "r") as f:
        import yaml
        data = yaml.safe_load(f)

    # Add reboot config with invalid node name
    data["phase_overlays"]["mutation"]["reboot"] = {
        "enabled": True,
        "nodes": ["nonexistent_node"],
        "timeout": 120,
    }

    with pytest.raises(ValidationError) as exc_info:
        HammerSpec.model_validate(data)

    assert "Reboot config in mutation references unknown node 'nonexistent_node'" in str(exc_info.value)


def test_reboot_config_timeout_bounds():
    """Test that reboot timeout must be within bounds."""
    with open(FIXTURES_DIR / "valid_full.yaml", "r") as f:
        import yaml
        data = yaml.safe_load(f)

    # Timeout too low
    data["phase_overlays"]["mutation"]["reboot"] = {
        "enabled": True,
        "timeout": 10,  # min is 30
    }

    with pytest.raises(ValidationError):
        HammerSpec.model_validate(data)


def test_optional_variable_contracts():
    """Test that variable_contracts can be omitted (None)."""
    with open(FIXTURES_DIR / "valid_full.yaml", "r") as f:
        import yaml
        data = yaml.safe_load(f)

    # Remove variable contracts and related items
    del data["variable_contracts"]
    del data["precedence_scenarios"]
    del data["handler_contracts"]  # has variable_changed trigger
    data["features"]["handlers"] = False

    # Remove firewall with port var reference
    data["behavioral_contracts"]["firewall"] = []

    # Remove reachability with port var reference
    data["behavioral_contracts"]["reachability"] = []

    spec = HammerSpec.model_validate(data)
    assert spec.variable_contracts is None


def test_pe4_spec_validates():
    """Test that the PE4 spec file validates successfully."""
    spec_path = PROJECT_ROOT / "real_examples" / "PE4" / "spec.yaml"
    spec = load_spec_from_file(spec_path)

    assert spec.assignment_id == "pe4-ansible-exam"
    assert spec.variable_contracts is None
    assert spec.behavioral_contracts is not None
    assert spec.phase_overlays.mutation.reboot is not None
    assert spec.phase_overlays.mutation.reboot.enabled is True


def test_external_http_contract_from_host():
    """Test ExternalHttpContract with from_host=True."""
    with open(FIXTURES_DIR / "valid_full.yaml", "r") as f:
        import yaml
        data = yaml.safe_load(f)

    # Add external_http contract from host
    data["behavioral_contracts"]["external_http"] = [
        {
            "url": "http://localhost:8080/",
            "from_host": True,
            "expected_status": 200,
        }
    ]

    spec = HammerSpec.model_validate(data)
    assert spec.behavioral_contracts.external_http is not None
    assert len(spec.behavioral_contracts.external_http) == 1
    assert spec.behavioral_contracts.external_http[0].from_host is True


def test_external_http_contract_from_node():
    """Test ExternalHttpContract with from_node selector."""
    with open(FIXTURES_DIR / "valid_full.yaml", "r") as f:
        import yaml
        data = yaml.safe_load(f)

    # Add external_http contract from another VM
    data["behavioral_contracts"]["external_http"] = [
        {
            "url": "http://web1:80/",
            "from_node": {"host": "app1"},
            "expected_status": 200,
            "response_contains": "Welcome",
        }
    ]

    spec = HammerSpec.model_validate(data)
    assert spec.behavioral_contracts.external_http is not None
    assert spec.behavioral_contracts.external_http[0].from_host is False
    assert spec.behavioral_contracts.external_http[0].from_node.host == "app1"


def test_external_http_contract_invalid_both():
    """Test that specifying both from_host and from_node fails."""
    with open(FIXTURES_DIR / "valid_full.yaml", "r") as f:
        import yaml
        data = yaml.safe_load(f)

    data["behavioral_contracts"]["external_http"] = [
        {
            "url": "http://localhost:8080/",
            "from_host": True,
            "from_node": {"host": "app1"},  # Can't have both
        }
    ]

    with pytest.raises(ValidationError) as exc_info:
        HammerSpec.model_validate(data)

    assert "Cannot specify both from_host=True and from_node" in str(exc_info.value)


def test_external_http_contract_invalid_neither():
    """Test that specifying neither from_host nor from_node fails."""
    with open(FIXTURES_DIR / "valid_full.yaml", "r") as f:
        import yaml
        data = yaml.safe_load(f)

    data["behavioral_contracts"]["external_http"] = [
        {
            "url": "http://localhost:8080/",
            # Neither from_host nor from_node specified
        }
    ]

    with pytest.raises(ValidationError) as exc_info:
        HammerSpec.model_validate(data)

    assert "Must specify either from_host=True or from_node" in str(exc_info.value)


def test_output_contract_contains():
    """Test OutputContract with contains match type."""
    with open(FIXTURES_DIR / "valid_full.yaml", "r") as f:
        import yaml
        data = yaml.safe_load(f)

    data["behavioral_contracts"]["output_checks"] = [
        {
            "pattern": "Server configured successfully",
            "match_type": "contains",
            "expected": True,
            "description": "Check success message",
            "weight": 1.0,
        }
    ]

    spec = HammerSpec.model_validate(data)
    assert spec.behavioral_contracts.output_checks is not None
    assert len(spec.behavioral_contracts.output_checks) == 1
    assert spec.behavioral_contracts.output_checks[0].match_type == "contains"


def test_output_contract_regex():
    """Test OutputContract with regex match type."""
    with open(FIXTURES_DIR / "valid_full.yaml", "r") as f:
        import yaml
        data = yaml.safe_load(f)

    data["behavioral_contracts"]["output_checks"] = [
        {
            "pattern": r"Port: \d+",
            "match_type": "regex",
            "expected": True,
        }
    ]

    spec = HammerSpec.model_validate(data)
    assert spec.behavioral_contracts.output_checks[0].match_type == "regex"


def test_output_contract_expected_false():
    """Test OutputContract for checking absence of pattern."""
    with open(FIXTURES_DIR / "valid_full.yaml", "r") as f:
        import yaml
        data = yaml.safe_load(f)

    data["behavioral_contracts"]["output_checks"] = [
        {
            "pattern": "FAILED",
            "expected": False,  # Should NOT be in output
            "description": "No failures expected",
        }
    ]

    spec = HammerSpec.model_validate(data)
    assert spec.behavioral_contracts.output_checks[0].expected is False


def test_failure_policy_allow_failures():
    """Test FailurePolicy configuration."""
    with open(FIXTURES_DIR / "valid_full.yaml", "r") as f:
        import yaml
        data = yaml.safe_load(f)

    data["phase_overlays"]["baseline"]["failure_policy"] = {
        "allow_failures": True,
        "max_failures": 2,
        "expected_patterns": ["Connection refused", "timeout"],
    }

    spec = HammerSpec.model_validate(data)
    policy = spec.phase_overlays.baseline.failure_policy
    assert policy is not None
    assert policy.allow_failures is True
    assert policy.max_failures == 2
    assert "Connection refused" in policy.expected_patterns


def test_failure_policy_default():
    """Test that failure_policy defaults to None (strict mode)."""
    with open(FIXTURES_DIR / "valid_full.yaml", "r") as f:
        import yaml
        data = yaml.safe_load(f)

    spec = HammerSpec.model_validate(data)
    assert spec.phase_overlays.baseline.failure_policy is None
