import sys
from pathlib import Path
import pytest

# Ensure src is in path
PROJECT_ROOT = Path(__file__).parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from hammer.spec import load_spec_from_file
from hammer.plan import build_execution_plan, resolve_node_selector

FIXTURES_DIR = PROJECT_ROOT / "tests" / "fixtures"

@pytest.fixture
def full_spec():
    return load_spec_from_file(FIXTURES_DIR / "valid_full.yaml")

def test_node_selector_resolution(full_spec):
    """Test that group selector resolves to list of hostnames."""
    from hammer.spec import NodeSelector
    
    # Test group selector
    sel = NodeSelector(group="web")
    hosts = resolve_node_selector(sel, full_spec.topology)
    assert hosts == ["web1"]
    
    # Test host selector
    sel_host = NodeSelector(host="app1")
    hosts = resolve_node_selector(sel_host, full_spec.topology)
    assert hosts == ["app1"]

def test_variable_resolution_baseline_vs_mutation(full_spec):
    """
    Test variable resolution logic.
    Baseline: http_port 8080 (group_vars/web)
    Mutation: http_port 9090 (extra_vars overrides group_vars)
    """
    plan = build_execution_plan(full_spec)
    
    # Baseline check
    baseline_vars = plan.variables["baseline"].resolved
    assert baseline_vars["http_port"].value == 8080
    assert baseline_vars["http_port"].source == "group_vars"
    
    assert baseline_vars["welcome_text"].value == "hello"
    
    # Mutation check
    mutation_vars = plan.variables["mutation"].resolved
    assert mutation_vars["http_port"].value == 9090
    assert mutation_vars["http_port"].source == "extra_vars"
    
    assert mutation_vars["welcome_text"].value == "bonjour"
    assert mutation_vars["welcome_text"].source == "group_vars"

def test_idempotence_uses_mutation_vars(full_spec):
    """Idempotence phase should use the same variables as mutation."""
    plan = build_execution_plan(full_spec)
    
    mut_vars = plan.variables["mutation"].resolved
    idem_vars = plan.variables["idempotence"].resolved
    
    assert mut_vars["http_port"].value == idem_vars["http_port"].value
    assert mut_vars["welcome_text"].value == idem_vars["welcome_text"].value

def test_handler_expectations(full_spec):
    """
    Verify handler expectations are correctly planned per phase.
    Baseline: at_least_once
    Mutation: exactly_once
    Idempotence: zero
    """
    plan = build_execution_plan(full_spec)
    
    # Check baseline
    handlers_base = plan.contracts["baseline"].handlers
    assert len(handlers_base) == 1
    h_base = handlers_base[0]
    assert h_base.expectations["baseline"].expected_runs == "at_least_once"
    
    # Check mutation
    handlers_mut = plan.contracts["mutation"].handlers
    h_mut = handlers_mut[0]
    assert h_mut.expectations["mutation"].expected_runs == "exactly_once"
    
    # Check idempotence
    handlers_idem = plan.contracts["idempotence"].handlers
    h_idem = handlers_idem[0]
    assert h_idem.expectations["idempotence"].expected_runs == "zero"

def test_binding_checks_value_propagation(full_spec):
    """Verify that binding checks get the resolved variable value."""
    plan = build_execution_plan(full_spec)

    # In baseline, http_port is 8080
    base_bindings = plan.contracts["baseline"].bindings
    port_binding = next(b for b in base_bindings if b.binding_target.get("service") == "nginx")
    assert port_binding.expected_value == 8080

    # In mutation, http_port is 9090
    mut_bindings = plan.contracts["mutation"].bindings
    port_binding_mut = next(b for b in mut_bindings if b.binding_target.get("service") == "nginx")
    assert port_binding_mut.expected_value == 9090


# -------------------------
# PE4 Support Tests
# -------------------------

def test_phase_filtering_baseline_only():
    """Test that contracts with phases=[baseline] only appear in baseline."""
    from hammer.plan import _applies_to_phase

    # Contract only for baseline
    assert _applies_to_phase(["baseline"], "baseline") is True
    assert _applies_to_phase(["baseline"], "mutation") is False
    assert _applies_to_phase(["baseline"], "idempotence") is False


def test_phase_filtering_mutation_idempotence():
    """Test that contracts with phases=[mutation, idempotence] work correctly."""
    from hammer.plan import _applies_to_phase

    # Contract for mutation and idempotence
    assert _applies_to_phase(["mutation", "idempotence"], "baseline") is False
    assert _applies_to_phase(["mutation", "idempotence"], "mutation") is True
    assert _applies_to_phase(["mutation", "idempotence"], "idempotence") is True


def test_phase_filtering_none_means_all():
    """Test that phases=None means all phases."""
    from hammer.plan import _applies_to_phase

    # None means all phases
    assert _applies_to_phase(None, "baseline") is True
    assert _applies_to_phase(None, "mutation") is True
    assert _applies_to_phase(None, "idempotence") is True


def test_empty_variable_contracts():
    """Test that plan building works with no variable_contracts."""
    spec_path = FIXTURES_DIR.parent.parent / "real_examples" / "PE4" / "spec.yaml"
    pe4_spec = load_spec_from_file(spec_path)

    plan = build_execution_plan(pe4_spec)

    # Should have no bindings
    assert len(plan.contracts["baseline"].bindings) == 0
    assert len(plan.contracts["mutation"].bindings) == 0
    assert len(plan.contracts["idempotence"].bindings) == 0

    # Should still have behavioral contracts
    # Note: Some may be filtered by phase
    assert plan.contracts["baseline"] is not None
    assert plan.contracts["mutation"] is not None


def test_phase_specific_files_contract():
    """Test that phase-specific file contracts are filtered correctly."""
    spec_path = FIXTURES_DIR.parent.parent / "real_examples" / "PE4" / "spec.yaml"
    pe4_spec = load_spec_from_file(spec_path)

    plan = build_execution_plan(pe4_spec)

    # In baseline, the second_run.txt absent check should be present
    baseline_files = plan.contracts["baseline"].files

    # Find the check for second_run.txt in baseline
    baseline_absent = any(
        any(item.get("path") == "/opt/second_run.txt" and item.get("present") is False
            for item in fc.items)
        for fc in baseline_files
    )
    assert baseline_absent, "Baseline should check for absent second_run.txt"

    # In mutation, second_run.txt should be expected to be present
    mutation_files = plan.contracts["mutation"].files

    # The absent check should NOT be in mutation
    mutation_absent = any(
        any(item.get("path") == "/opt/second_run.txt" and item.get("present") is False
            for item in fc.items)
        for fc in mutation_files
    )
    assert not mutation_absent, "Mutation should NOT check for absent second_run.txt"

    # The present check should be in mutation
    mutation_present = any(
        any(item.get("path") == "/opt/second_run.txt" and item.get("present") is True
            for item in fc.items)
        for fc in mutation_files
    )
    assert mutation_present, "Mutation should check for present second_run.txt"


def test_phase_specific_service_contract():
    """Test that myhealthcheck service is only checked in mutation/idempotence."""
    spec_path = FIXTURES_DIR.parent.parent / "real_examples" / "PE4" / "spec.yaml"
    pe4_spec = load_spec_from_file(spec_path)

    plan = build_execution_plan(pe4_spec)

    # Service should NOT be in baseline
    baseline_services = [s.name for s in plan.contracts["baseline"].services]
    assert "myhealthcheck" not in baseline_services

    # Service SHOULD be in mutation
    mutation_services = [s.name for s in plan.contracts["mutation"].services]
    assert "myhealthcheck" in mutation_services

    # Service SHOULD be in idempotence
    idempotence_services = [s.name for s in plan.contracts["idempotence"].services]
    assert "myhealthcheck" in idempotence_services
