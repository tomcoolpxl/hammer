# Phase 4 Implementation Plan: Test Generation Layer

## Overview

Implement test generation that converts `PhaseContractPlan` into executable pytest/testinfra test files. These tests verify that the student's Ansible playbook correctly implements the specified contracts.

## Module Structure

```
src/hammer/
    testgen/
        __init__.py           # Exports generate_tests()
        bindings.py           # Binding contract test generators
        behavioral.py         # Package/service/file/firewall tests
        reachability.py       # Network reachability tests
        handlers.py           # Handler verification tests
        templates/
            conftest.py.j2    # Pytest fixtures and connection setup
            test_bindings.py.j2
            test_packages.py.j2
            test_services.py.j2
            test_files.py.j2
            test_firewall.py.j2
            test_reachability.py.j2
```

## Implementation Steps

### Step 1: Add pytest-testinfra Dependency
**File:** `pyproject.toml`
- Add `"pytest-testinfra>=10.0.0"` to dependencies

### Step 2: Conftest Generator
**File:** `src/hammer/testgen/templates/conftest.py.j2`

Provides:
- SSH connection fixtures per host
- Phase-aware test markers
- Helper functions for common assertions

```python
import pytest
import testinfra

@pytest.fixture(scope="module")
def host_{{ node_name }}(request):
    return testinfra.get_host(
        "paramiko://{{ node_name }}",
        ssh_config=".vagrant/ssh_config"
    )
```

### Step 3: Binding Test Generator
**File:** `src/hammer/testgen/bindings.py`
**File:** `src/hammer/testgen/templates/test_bindings.py.j2`

Test types:
- `service_listen_port`: Check socket listening on expected port
- `firewall_port_open`: Check firewalld port rules
- `template_contains`: Check file contains expected pattern
- `file_contains`: Check file contains expected content
- `file_exists`: Check file presence
- `file_mode`: Check file permissions
- `file_owner`: Check file ownership

### Step 4: Behavioral Test Generators
**File:** `src/hammer/testgen/behavioral.py`

Package tests:
```python
def test_package_nginx_present(host_web1):
    pkg = host_web1.package("nginx")
    assert pkg.is_installed
```

Service tests:
```python
def test_service_nginx_running(host_web1):
    svc = host_web1.service("nginx")
    assert svc.is_running
    assert svc.is_enabled
```

File tests:
```python
def test_file_config_exists(host_web1):
    f = host_web1.file("/etc/nginx/conf.d/hammer.conf")
    assert f.exists
    assert f.mode == 0o644
```

### Step 5: Firewall Test Generator
**File:** `src/hammer/testgen/templates/test_firewall.py.j2`

```python
def test_firewall_port_8080_open(host_web1):
    cmd = host_web1.run("firewall-cmd --list-ports --zone=public")
    assert "8080/tcp" in cmd.stdout
```

### Step 6: Reachability Test Generator
**File:** `src/hammer/testgen/reachability.py`
**File:** `src/hammer/testgen/templates/test_reachability.py.j2`

```python
def test_app1_can_reach_web1_on_port_8080(host_app1):
    # Use nc or curl to test connectivity
    cmd = host_app1.run("nc -zv 192.168.x.10 8080")
    assert cmd.rc == 0
```

### Step 7: Main Test Generator Orchestrator
**File:** `src/hammer/testgen/__init__.py`

```python
def generate_tests(
    spec: HammerSpec,
    plan: ExecutionPlan,
    network: NetworkPlan,
    output_dir: Path,
    phase: str = "baseline",
) -> List[Path]:
    """
    Generate pytest test files for the given phase.

    Returns list of generated test file paths.
    """
```

### Step 8: Integration with Builder
**File:** `src/hammer/builder/__init__.py` (modify)

Update `build_assignment()` to:
1. Generate tests into `grading_bundle/tests/`
2. Generate phase-specific test files (baseline, mutation, idempotence)

### Step 9: Unit Tests
**File:** `tests/unit/test_testgen.py`

Test cases:
- `test_binding_test_generation`
- `test_package_test_generation`
- `test_service_test_generation`
- `test_file_test_generation`
- `test_reachability_test_generation`
- `test_generated_tests_are_valid_python`

## Test File Structure in Grading Bundle

```
grading_bundle/
  tests/
    conftest.py              # Shared fixtures
    baseline/
      test_bindings.py
      test_packages.py
      test_services.py
      test_files.py
      test_firewall.py
      test_reachability.py
    mutation/
      test_bindings.py
      ...
    idempotence/
      test_idempotence.py    # Special: checks changed=0
```

## Key Design Decisions

1. **Testinfra over raw SSH**: Provides clean abstractions for system state
2. **Phase separation**: Each phase gets its own test directory with phase-specific expectations
3. **Variable interpolation**: Tests use resolved values from ExecutionPlan, not raw spec
4. **Host targeting**: Tests are generated per-host based on node_selector resolution

## Files to Create/Modify

| File | Action |
|------|--------|
| `pyproject.toml` | Modify - add pytest-testinfra |
| `src/hammer/testgen/__init__.py` | Create |
| `src/hammer/testgen/bindings.py` | Create |
| `src/hammer/testgen/behavioral.py` | Create |
| `src/hammer/testgen/reachability.py` | Create |
| `src/hammer/testgen/templates/conftest.py.j2` | Create |
| `src/hammer/testgen/templates/test_bindings.py.j2` | Create |
| `src/hammer/testgen/templates/test_packages.py.j2` | Create |
| `src/hammer/testgen/templates/test_services.py.j2` | Create |
| `src/hammer/testgen/templates/test_files.py.j2` | Create |
| `src/hammer/testgen/templates/test_firewall.py.j2` | Create |
| `src/hammer/testgen/templates/test_reachability.py.j2` | Create |
| `src/hammer/builder/__init__.py` | Modify - integrate test generation |
| `tests/unit/test_testgen.py` | Create |

## Verification

After implementation:
1. Run `hammer build --spec tests/fixtures/valid_full.yaml --out /tmp/test_build`
2. Verify `grading_bundle/tests/` contains generated test files
3. Verify generated Python files have valid syntax: `python -m py_compile <file>`
4. Run unit tests: `pytest tests/unit/test_testgen.py`
