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
