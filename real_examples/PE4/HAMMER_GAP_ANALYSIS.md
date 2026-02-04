# PE4 HAMMER Gap Analysis

## Executive Summary

PE4 is a single-node Ansible exam that tests user/group management, file permissions, systemd service creation, conditional execution, and error handling. **Most PE4 requirements are already supported by HAMMER**, but there are gaps that need addressing:

1. **Phase-specific behavioral contracts** - Different expected states per phase
2. **Reboot testing** - Verify services actually start on boot
3. **Optional variable contracts** - PE4 has no variables to mutate

## PE4 Requirements Mapped to HAMMER

### ✅ FULLY SUPPORTED

| PE4 Requirement | HAMMER Feature | Notes |
|-----------------|----------------|-------|
| **Q1: Users** (carol, dave, edgar) | `behavioral_contracts.users` | UserContract supports exists, home, groups |
| **Q1: Group** (students) | `behavioral_contracts.groups` | GroupContract supports exists, gid |
| **Q1: Users in group** | `UserContract.groups` | Supplementary group membership check |
| **Q2: MOTD file exists** | `behavioral_contracts.files` | FileContractItem with present: true |
| **Q2: MOTD ownership** | `FileContractItem.owner/group` | edgar:students |
| **Q2: MOTD permissions** | `FileContractItem.mode` | "0664" |
| **Q2: MOTD content** | `FileContractItem.content_regex` | Pattern match |
| **Q3: Script exists** | `behavioral_contracts.files` | present: true |
| **Q3: Script executable** | `FileContractItem.mode` | "0755" or similar |
| **Q3: Service file exists** | `behavioral_contracts.files` | present: true |
| **Q3: Service enabled** | `behavioral_contracts.services` | enabled: true |
| **Q5: File NOT exists** | `FileContractItem.present: false` | Negative existence check |
| **FQDN support** | `topology.domain` | Domain suffix for node names |
| **Port forwarding** | `Node.forwarded_ports` | Per-node port forwards |

### ⚠️ NEEDS IMPLEMENTATION

| PE4 Requirement | Gap | Solution |
|-----------------|-----|----------|
| **Q3: Service starts on boot** | Only checks `systemctl is-enabled`, not actual boot | Add reboot testing |
| **Q4: Conditional first/second run** | Same contracts apply to all phases | Add `phases` field to contracts |
| **No variable contracts** | `variable_contracts` is required | Make it optional |

---

## Gap 1: Phase-Specific Behavioral Contracts

### Problem

PE4 Q4 requires different expected states after different playbook runs:
- After run 1 (baseline): `first_run.txt` exists, `second_run.txt` does NOT
- After run 2 (mutation): both files exist

Currently, behavioral contracts apply identically to all phases.

### Solution

Add optional `phases` field to all behavioral contracts:

```yaml
behavioral_contracts:
  files:
    # Check in baseline only - second_run.txt should NOT exist yet
    - items:
        - path: "/opt/second_run.txt"
          present: false
      node_selector: { host: "server0" }
      phases: [baseline]
      weight: 1.0

    # Check in mutation/idempotence - second_run.txt should exist
    - items:
        - path: "/opt/second_run.txt"
          present: true
      node_selector: { host: "server0" }
      phases: [mutation, idempotence]
      weight: 1.0
```

### Schema Changes

```python
# In spec.py - add to all behavioral contract classes

PhaseName = Literal["baseline", "mutation", "idempotence"]

class FilesContract(BaseModel):
    items: List[FileContractItem]
    node_selector: NodeSelector
    phases: Optional[List[PhaseName]] = None  # None = all phases
    weight: float = Field(default=1.0, ge=0.0)

# Same for: PackageContract, ServiceContract, UserContract,
# GroupContract, FirewallContract, ReachabilityContract, HttpEndpointContract
```

### Implementation

1. Add `phases` field to all behavioral contract models
2. In `plan.py`: filter contracts by phase when building PhaseContractPlan
3. In `testgen`: only generate tests for contracts matching the phase
4. Default behavior (phases=None): include in all phases (backward compatible)

---

## Gap 2: Reboot Testing

### Problem

Checking `systemctl is-enabled myhealthcheck` only verifies the service is configured to start on boot. It does NOT verify:
- The service actually starts successfully on boot
- Dependencies are met
- Configuration is valid
- Permissions are correct

PE4 Q3 requires the healthcheck service to **actually work after reboot**.

### Solution

Add per-phase reboot configuration with selective node targeting:

```yaml
phase_overlays:
  baseline:
    group_vars: {}
    # No reboot - test immediately after converge

  mutation:
    group_vars: {}
    reboot:
      enabled: true
      nodes: [server0]  # Selective: only reboot these nodes
      timeout: 120      # Max seconds to wait for SSH (default: 120)
```

### Phase Flow With Reboot

```
baseline:
  1. Apply baseline overlays
  2. Converge (ansible-playbook)
  3. Run baseline tests

mutation:
  1. Apply mutation overlays
  2. Converge (ansible-playbook)
  3. Reboot server0 (ssh: sudo reboot)
  4. Poll SSH until available (max 120s)
  5. Run mutation tests  ← Services checked HERE prove boot behavior

idempotence:
  1. Converge again (same overlays)
  2. Run idempotence tests
```

### Schema Changes

```python
# In spec.py

class RebootConfig(BaseModel):
    """Configuration for rebooting nodes before tests."""
    enabled: bool = False
    nodes: Optional[List[NonEmptyStr]] = None  # None = all nodes
    timeout: int = Field(default=120, ge=30, le=600)  # seconds

class PhaseOverlay(BaseModel):
    inventory_vars: Optional[Dict[str, Any]] = None
    group_vars: Optional[Dict[str, Dict[str, Any]]] = None
    host_vars: Optional[Dict[str, Dict[str, Any]]] = None
    extra_vars: Optional[Dict[str, Any]] = None
    reboot: Optional[RebootConfig] = None  # NEW
```

### Implementation

```python
# In runner/reboot.py (new file)

import time
import subprocess
from pathlib import Path
from typing import List, Optional

def reboot_nodes(
    inventory_path: Path,
    nodes: Optional[List[str]],  # None = all nodes
    timeout: int = 120,
    poll_interval: int = 5,
) -> dict:
    """
    Reboot specified nodes and wait for SSH to come back.

    Returns:
        Dict with node -> {success: bool, duration: float, error: str|None}
    """
    results = {}

    # Get node list from inventory if not specified
    if nodes is None:
        nodes = get_all_nodes_from_inventory(inventory_path)

    for node in nodes:
        results[node] = reboot_single_node(
            inventory_path, node, timeout, poll_interval
        )

    return results

def reboot_single_node(
    inventory_path: Path,
    node: str,
    timeout: int,
    poll_interval: int,
) -> dict:
    """Reboot a single node via SSH and wait for it to come back."""

    start_time = time.time()

    # Send reboot command (don't wait for response - connection will drop)
    try:
        subprocess.run(
            ["ansible", node, "-i", str(inventory_path),
             "-m", "shell", "-a", "sleep 2 && sudo reboot",
             "-B", "1", "-P", "0"],  # Background, don't poll
            timeout=30,
            capture_output=True,
        )
    except subprocess.TimeoutExpired:
        pass  # Expected - connection drops

    # Wait for SSH to go down (optional, adds reliability)
    time.sleep(5)

    # Poll for SSH to come back
    elapsed = 0
    while elapsed < timeout:
        if check_ssh_available(inventory_path, node):
            return {
                "success": True,
                "duration": time.time() - start_time,
                "error": None,
            }
        time.sleep(poll_interval)
        elapsed = time.time() - start_time

    return {
        "success": False,
        "duration": timeout,
        "error": f"SSH did not become available within {timeout}s",
    }

def check_ssh_available(inventory_path: Path, node: str) -> bool:
    """Check if SSH is available on a node."""
    try:
        result = subprocess.run(
            ["ansible", node, "-i", str(inventory_path),
             "-m", "ping"],
            timeout=10,
            capture_output=True,
        )
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        return False
```

### Runner Integration

```python
# In runner/__init__.py - modify run_phase()

def run_phase(phase: str, ...):
    # ... existing converge code ...

    # Check for reboot configuration
    phase_overlay = spec.phase_overlays.baseline if phase == "baseline" else spec.phase_overlays.mutation

    if phase_overlay and phase_overlay.reboot and phase_overlay.reboot.enabled:
        if verbose:
            print(f"[{phase}] Rebooting nodes...")

        reboot_results = reboot_nodes(
            inventory_path=inventory_path,
            nodes=phase_overlay.reboot.nodes,
            timeout=phase_overlay.reboot.timeout,
        )

        # Check all reboots succeeded
        for node, result in reboot_results.items():
            if not result["success"]:
                raise RuntimeError(f"Reboot failed for {node}: {result['error']}")
            if verbose:
                print(f"[{phase}] {node} rebooted in {result['duration']:.1f}s")

    # ... existing test code ...
```

---

## Gap 3: Optional Variable Contracts

### Problem

`variable_contracts` is currently required in HammerSpec. PE4 has no variables to mutate.

### Solution

Make it optional with empty list default:

```python
# In spec.py

class HammerSpec(BaseModel):
    # ... other fields ...
    variable_contracts: Optional[List[VariableContract]] = None  # Changed from required
```

### Affected Code

| File | Change |
|------|--------|
| `spec.py` | Make field optional |
| `plan.py` | Handle None/empty in `build_execution_plan()` |
| `testgen/__init__.py` | Skip binding tests if no variables |
| `testgen/bindings.py` | Handle empty variable list |
| Validators | Update cross-field validators to handle None |

---

## Complete PE4 Spec Example

```yaml
assignment_id: "pe4-ansible-exam"
assignment_version: "2025.01"
spec_version: "1.0"
seed: 42
provider: "libvirt"
os: "almalinux9"

features:
  handlers: false
  reachability: false

topology:
  domain: "pxldemo.local"
  nodes:
    - name: "server0"
      groups: ["servers", "webservers", "dbservers"]
      resources:
        cpu: 1
        ram_mb: 1024
      forwarded_ports:
        - host_port: 8888
          guest_port: 80
          protocol: tcp

entrypoints:
  playbook_path: "playbook.yml"
  required_roles: ["pxl_exam_role"]
  required_files: ["playbook.yml"]

# No variable contracts - pure behavioral testing
variable_contracts: []

behavioral_contracts:
  # ========================================
  # Question 1: Users and Groups
  # ========================================
  groups:
    - name: "students"
      exists: true
      node_selector: { host: "server0" }
      weight: 1.0

  users:
    - name: "carol"
      exists: true
      groups: ["students"]
      node_selector: { host: "server0" }
      weight: 1.0
    - name: "dave"
      exists: true
      groups: ["students"]
      node_selector: { host: "server0" }
      weight: 1.0
    - name: "edgar"
      exists: true
      groups: ["students"]
      node_selector: { host: "server0" }
      weight: 1.0

  # ========================================
  # Question 2: MOTD File
  # ========================================
  files:
    - items:
        - path: "/etc/motd"
          present: true
          owner: "edgar"
          group: "students"
          mode: "0664"
          content_regex: "Welcome to Paradise"
      node_selector: { host: "server0" }
      weight: 2.0

    # ========================================
    # Question 3: Healthcheck Script & Service
    # ========================================
    - items:
        - path: "/opt/healthcheck.sh"
          present: true
          mode: "0755"
      node_selector: { host: "server0" }
      weight: 1.0

    - items:
        - path: "/etc/systemd/system/myhealthcheck.service"
          present: true
      node_selector: { host: "server0" }
      weight: 1.0

    - items:
        - path: "/var/log/healthcheck.log"
          present: true
      node_selector: { host: "server0" }
      phases: [mutation, idempotence]  # Only after reboot (service ran)
      weight: 1.0

    # ========================================
    # Question 4: Conditional Run Files
    # ========================================
    # After first run: first_run.txt exists, second_run.txt does NOT
    - items:
        - path: "/opt/first_run.txt"
          present: true
          content_regex: "First run file"
      node_selector: { host: "server0" }
      weight: 1.0

    - items:
        - path: "/opt/second_run.txt"
          present: false
      node_selector: { host: "server0" }
      phases: [baseline]  # Only check absence in baseline
      weight: 1.0

    # After second run: second_run.txt exists
    - items:
        - path: "/opt/second_run.txt"
          present: true
          content_regex: "Second run file"
      node_selector: { host: "server0" }
      phases: [mutation, idempotence]  # Check presence after 2nd run
      weight: 1.0

    # ========================================
    # Question 5: File Should NOT Exist
    # ========================================
    - items:
        - path: "/mnt/special/pxl/my_special_pxl_file"
          present: false
      node_selector: { host: "server0" }
      weight: 1.0

  services:
    # Question 3: Service enabled AND running after reboot
    - name: "myhealthcheck"
      enabled: true
      running: true  # Verified AFTER reboot = proves boot behavior
      node_selector: { host: "server0" }
      phases: [mutation, idempotence]  # Only check after reboot
      weight: 2.0

idempotence:
  required: true
  enforcement:
    require_changed_zero: true
    require_no_handlers: false

phase_overlays:
  baseline:
    group_vars: {}
    # No reboot - first run tests

  mutation:
    group_vars: {}
    reboot:
      enabled: true
      nodes: [server0]
      timeout: 120
    # Reboot after converge, before tests
    # This verifies: myhealthcheck starts on boot
```

---

## Implementation Phases

### Phase 1: Schema Updates (2-3 hours)

1. Add `phases` field to all behavioral contract classes
2. Add `RebootConfig` model
3. Add `reboot` field to `PhaseOverlay`
4. Make `variable_contracts` optional
5. Update validators

### Phase 2: Plan Builder Updates (1-2 hours)

1. Filter contracts by phase in `build_phase_contract_plan()`
2. Handle empty variable contracts
3. Pass reboot config through to execution plan

### Phase 3: Test Generation Updates (1-2 hours)

1. Filter contracts by phase when generating tests
2. Skip binding tests if no variable contracts
3. Add phase marker to generated test functions

### Phase 4: Runner Updates (2-3 hours)

1. Create `runner/reboot.py` module
2. Integrate reboot into phase execution flow
3. Add reboot status to phase results
4. Handle reboot failures gracefully

### Phase 5: Testing & Validation (2-3 hours)

1. Unit tests for new schema fields
2. Unit tests for reboot module
3. Create PE4 spec file
4. Create sample passing role
5. End-to-end test with libvirt

---

## Files to Create/Modify

| File | Action | Description |
|------|--------|-------------|
| `src/hammer/spec.py` | Modify | Add phases, reboot, optional variable_contracts |
| `src/hammer/plan.py` | Modify | Filter contracts by phase |
| `src/hammer/runner/reboot.py` | Create | Reboot implementation |
| `src/hammer/runner/__init__.py` | Modify | Integrate reboot into flow |
| `src/hammer/testgen/__init__.py` | Modify | Phase filtering |
| `real_examples/PE4/spec.yaml` | Create | PE4 specification |
| `real_examples/PE4/solution/` | Create | Sample passing role |
| `tests/unit/test_reboot.py` | Create | Reboot module tests |
| `tests/unit/test_phase_filtering.py` | Create | Phase filter tests |

---

## Timeline Estimate

| Phase | Effort |
|-------|--------|
| Phase 1: Schema | 2-3 hours |
| Phase 2: Plan Builder | 1-2 hours |
| Phase 3: Test Generation | 1-2 hours |
| Phase 4: Runner/Reboot | 2-3 hours |
| Phase 5: Testing | 2-3 hours |
| **Total** | **8-13 hours** |

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Reboot timing issues | Medium | Medium | Generous default timeout, polling |
| SSH not available after reboot | Low | High | Retry logic, clear error messages |
| Phase filtering breaks existing specs | Low | Medium | Default phases=None means all phases |
| Empty variable_contracts breaks code | Medium | Medium | Comprehensive unit tests first |

---

## Testing Checklist

- [ ] Unit test: phases field filtering
- [ ] Unit test: reboot config validation
- [ ] Unit test: empty variable_contracts handling
- [ ] Unit test: reboot polling logic
- [ ] Integration test: PE4 spec validates
- [ ] Integration test: PE4 bundles build correctly
- [ ] Integration test: Generated tests are valid Python
- [ ] E2E test: Full PE4 grading with libvirt (manual)
