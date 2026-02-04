# HAMMER Project Context

## Project Overview

**HAMMER** (Hands-on Ansible Multi-node Machine Evaluation Runner) is a system for deterministic assignment authoring, generation, and auto-grading for Ansible labs. It targets **Vagrant** + **libvirt/KVM** + **AlmaLinux 9** environments.

The core goal is to generate complete student bundles and grading bundles from a single declarative YAML specification, ensuring reproducibility and rigorous auto-grading via variable mutation, behavioral verification, and precedence checks.

## Key Documents & Structure

The project documentation is organized into the `docs/` directory:

*   **`REQUIREMENTS.md`**: The source of truth for scope, objectives, non-goals, and high-level architecture.
*   **`SPEC_SCHEMA.md`**: Contains the strict **JSON Schema (v1.0)** for the assignment specification file.
*   **`docs/design/01_spec_models.md`**: (Formerly `PYDANTIC_MODEL_SET.md`) Provides the **Pydantic v2** data models.
*   **`docs/design/02_normalization_logic.md`**: (Formerly `NORMALIZATION_MODEL_AND EXEC_PLAN_BUILDER.md`) Defines the "Phase Normalization" layer and Execution Plan.
*   **`docs/planning/IMPLEMENTATION_ROADMAP.md`**: The detailed, phased implementation plan.
*   **`docs/user-guide/`**: User documentation for spec authoring and CLI usage.
*   **`docs/E2E_TEST_ANALYSIS.md`**: E2E test analysis and implementation status.

## Architecture

The system follows a pipeline architecture:

1.  **Input:** A strict YAML assignment spec.
2.  **Validation:** `HammerSpec` (Pydantic) validates the input.
3.  **Normalization:** The spec is converted into an **Execution Plan** containing:
    *   **PhaseVariablePlan:** Resolved variables for 'baseline', 'mutation', and 'idempotence' phases.
    *   **PhaseContractPlan:** Concrete checks for bindings, services, files, etc.
4.  **Generation:**
    *   **Student Bundle:** Vagrantfile, inventory, scaffolding.
    *   **Grading Bundle:** Grading inventory, overlays, runner scripts.
    *   **Tests:** Pytest/Testinfra tests generated from the Contract Plan.
5.  **Execution (Runner):** A Python CLI (`hammer grade`) executes the plan, collecting artifacts and scores.

## Development Conventions

*   **Language:** Python 3.10+
*   **Validation:** Pydantic v2.x (Strict validation, fail-fast).
*   **Testing:** Pytest (for the runner/generator) and Testinfra (for the generated assignment tests).
*   **Style:** Code provided in markdown is "production-grade" and ready to be extracted into the codebase.
*   **Philosophy:**
    *   **Determinism:** All derived choices (IPs, mutation values) must be deterministic based on a seed.
    *   **Minimalism:** The v1 implementation should be a small, focused CLI.
    *   **Hard Edges:** Avoid flaky heuristic checks; prefer reachability and explicit system state.

## Current Status

**All core phases complete.** The following is implemented and tested:

*   `hammer validate --spec FILE` - Validates spec against Pydantic models
*   `hammer build --spec FILE --out DIR` - Generates student/grading bundles with:
    *   Vagrantfile, inventory, group_vars, host_vars
    *   Phase overlays (baseline/mutation)
    *   Generated pytest/testinfra tests for all phases
*   `hammer grade` - Full grading pipeline with converge/verify/report
*   Full integration test verified: `vagrant up`, `ansible all -m ping`, `vagrant destroy`

### Test Infrastructure

| Test Type | Count | Description |
|-----------|-------|-------------|
| Unit tests | 123 | Core functionality |
| Integration tests | 86 | Build artifacts without VMs |
| E2E tests | 5 | Full grading with Vagrant VMs |

### Example Assignments

| Assignment | Spec | Solution | E2E Test |
|------------|------|----------|----------|
| PE1 | ✅ | ✅ `playbook_solution.yaml` | ✅ |
| PE2 | ✅ | ❌ | ❌ |
| PE3 | ✅ | ✅ `playbook_solution.yml` | ✅ |
| PE4 | ✅ | ✅ `roles/pxl_exam_role/` | ✅ |

## Feature Summary

### Core Features
- **Variable Contracts**: Test variable mutation and precedence
- **Behavioral Contracts**: Packages, services, files, users, groups, firewall, HTTP endpoints
- **Three-Phase Testing**: Baseline, mutation, idempotence
- **Deterministic Builds**: Same spec + seed = identical environment

### Advanced Features (PE4 Support)

| Feature | Description |
|---------|-------------|
| **Phase-Specific Contracts** | `phases` field on all behavioral contracts to filter by execution phase |
| **Reboot Testing** | `RebootConfig` in phase overlays to reboot nodes after converge |
| **Optional variable_contracts** | Pure behavioral testing without variable mutation |
| **External HTTP Testing** | `ExternalHttpContract` for host-to-VM or cross-VM HTTP verification |
| **Output Verification** | `OutputContract` to verify Ansible debug messages and output patterns |
| **Failure Policy** | `FailurePolicy` to allow expected failures during converge |

## Contract Types

### Behavioral Contracts

| Contract | Purpose |
|----------|---------|
| `packages` | Verify package installation state |
| `pip_packages` | Verify pip package installation |
| `services` | Verify service enabled/running state |
| `users` | Verify user existence and properties |
| `groups` | Verify group existence |
| `files` | Verify file existence, permissions, content |
| `firewall` | Verify firewall port rules |
| `reachability` | Verify network connectivity between nodes |
| `http_endpoints` | Verify HTTP endpoints from within VMs |
| `external_http` | Verify HTTP from host or cross-VM |
| `output_checks` | Verify Ansible output patterns |

### Phase Overlay Options

| Option | Description |
|--------|-------------|
| `group_vars` | Variables scoped to groups |
| `host_vars` | Variables scoped to hosts |
| `extra_vars` | Extra vars for ansible-playbook |
| `reboot` | Reboot configuration after converge |
| `failure_policy` | Expected failure handling |

## Example Spec (PE4-style)

```yaml
assignment_id: "pe4-ansible-exam"
spec_version: "1.0"
seed: 42
provider: "libvirt"
os: "almalinux9"

features:
  handlers: false

topology:
  domain: "example.local"
  nodes:
    - name: "server0"
      groups: ["servers"]
      resources:
        cpu: 1
        ram_mb: 1024
      forwarded_ports:
        - host_port: 8888
          guest_port: 80
          protocol: tcp

entrypoints:
  playbook_path: "playbook.yml"

# No variable contracts - pure behavioral testing
# variable_contracts: omitted

behavioral_contracts:
  users:
    - name: "appuser"
      exists: true
      groups: ["wheel"]
      node_selector: { host: "server0" }

  services:
    - name: "myservice"
      enabled: true
      running: true
      node_selector: { host: "server0" }
      phases: [mutation, idempotence]  # Only after reboot

  files:
    - items:
        - path: "/opt/first_run.txt"
          present: true
      node_selector: { host: "server0" }

    - items:
        - path: "/opt/second_run.txt"
          present: false
      node_selector: { host: "server0" }
      phases: [baseline]  # Only check in baseline

    - items:
        - path: "/opt/second_run.txt"
          present: true
      node_selector: { host: "server0" }
      phases: [mutation, idempotence]  # Check after 2nd run

  external_http:
    - url: "http://localhost:8888/"
      from_host: true
      expected_status: 200
      phases: [mutation]

  output_checks:
    - pattern: "Configuration complete"
      match_type: contains
      expected: true
    - pattern: "FAILED"
      expected: false

phase_overlays:
  baseline:
    group_vars: {}

  mutation:
    group_vars: {}
    reboot:
      enabled: true
      nodes: [server0]
      timeout: 120
    failure_policy:
      allow_failures: true
      max_failures: 1
      expected_patterns: ["Connection refused"]

idempotence:
  required: true
```

## Next Steps

Please refer to **`docs/planning/IMPLEMENTATION_ROADMAP.md`** for the detailed step-by-step plan.

### Completed
- ✅ End-to-end testing with PE1, PE3, PE4 assignments
- ✅ User documentation in `docs/user-guide/`
- ✅ Solution playbooks/roles for E2E testing

### Remaining
- PE2 solution and E2E tests
- CI/CD integration (blocked: GitHub Actions lacks KVM support)
- Additional example assignments

## Running Tests

```bash
# Unit + Integration tests
.venv/bin/python -m pytest tests/unit/ tests/integration/ -v

# E2E tests (requires Vagrant + libvirt) - use -s for live output
.venv/bin/python -m pytest tests/e2e/ -v -s -m e2e
```
