# HAMMER Gap Analysis for PE1 Assignment

## Executive Summary

This document analyzes what features HAMMER needs to support the PE1 Ansible assignment
as a real-world regression test. PE1 is a Python web application deployment exercise with
multiple grading tiers (Basic 50%, Extras 50%).

## PE1 Assignment Requirements

### Basic (50%)
1. Deploy `app.py` (Pyramid web app) to `/opt/pyramid_app/`
2. Install system packages: `python3`, `python3-pip`
3. Install pip packages: `pyramid`, `waitress`, `psutil`, `distro`
4. App listens on port 6000
5. App accessible at HTTP `/hostname` endpoint
6. App runs in background (non-idempotent shell command allowed)

### Extra 1 - iptables Firewall (20%)
1. Install `iptables-services` package
2. iptables service running and enabled
3. Port 6000 open in iptables (not firewalld)

### Extra 2 - Systemd Service (15%)
1. Deploy systemd unit file (`app.service`)
2. Service enabled and started
3. App survives reboot

### Extra 3 - User Management (15%)
1. Create user `app_user`
2. User owns `/opt/pyramid_app/` and `app.py`

---

## Current HAMMER Capabilities

| Requirement | HAMMER Support | Notes |
|-------------|----------------|-------|
| System packages | ✅ **Supported** | `PackageContract` |
| Service enabled/running | ✅ **Supported** | `ServiceContract` |
| File exists | ✅ **Supported** | `FilesContract.present` |
| File mode | ✅ **Supported** | `FilesContract.mode` |
| File owner/group | ✅ **Supported** | `FilesContract.owner/group` |
| File content regex | ✅ **Supported** | `FilesContract.content_regex` |
| Port listening | ✅ **Supported** | `service_listen_port` binding |
| firewalld ports | ✅ **Supported** | `FirewallContract` (zones) |
| TCP reachability | ✅ **Supported** | `ReachabilityContract` |
| Variable mutation | ✅ **Supported** | `phase_overlays` |
| Idempotence check | ✅ **Supported** | `idempotence` policy |

---

## Missing Features for PE1

### 1. Pip Package Contracts (Priority: HIGH)

**Current state:** Not supported.

**Required:** Verify Python pip packages are installed.

```yaml
behavioral_contracts:
  pip_packages:    # NEW
    - name: "pyramid"
      state: "present"
      python: "/usr/bin/python3"  # optional, default system python
      node_selector:
        group: "web"
```

**Implementation:**
- Add `PipPackageContract` to spec.py
- Add `pip_packages` to behavioral_contracts
- Generate test using `pip show <package>` or testinfra's `pip` module
- Test template: `test_pip_packages.py.j2`

---

### 2. User Contracts (Priority: HIGH)

**Current state:** Not supported.

**Required:** Verify system users exist with specified properties.

```yaml
behavioral_contracts:
  users:    # NEW
    - name: "app_user"
      exists: true
      uid: null          # optional
      gid: null          # optional
      home: null         # optional
      shell: null        # optional
      groups: []         # optional supplementary groups
      node_selector:
        group: "web"
```

**Implementation:**
- Add `UserContract` to spec.py
- Generate test using testinfra's `host.user()` interface
- Test template: `test_users.py.j2`

---

### 3. HTTP Endpoint Contracts (Priority: HIGH)

**Current state:** Not supported. Reachability only checks TCP connection, not HTTP response.

**Required:** Verify HTTP endpoints return expected status/content.

```yaml
behavioral_contracts:
  http_endpoints:    # NEW
    - url: "http://localhost:{{ app_port }}/hostname"
      method: "GET"
      expected_status: 200
      response_contains: "Hostname:"    # optional
      response_regex: "PXL PE.*"        # optional
      timeout_seconds: 5
      node_selector:
        host: "web1"
```

**Implementation:**
- Add `HttpEndpointContract` to spec.py
- Generate test using Python `requests` or `curl` via testinfra
- Support variable interpolation in URL
- Test template: `test_http.py.j2`

---

### 4. iptables Support (Priority: MEDIUM)

**Current state:** `FirewallContract` only supports `firewalld` with zones.

**Required:** Support both firewalld and iptables.

```yaml
behavioral_contracts:
  firewall:
    - open_ports:
        - port: 6000
          protocol: "tcp"
          zone: null           # null = iptables mode
      firewall_type: "iptables"  # NEW: "firewalld" | "iptables"
      node_selector:
        group: "web"
```

**Implementation:**
- Add `firewall_type` field to `FirewallContract`
- Modify test generation to check `iptables -L -n` for iptables mode
- Keep existing firewalld behavior as default
- Test template: Conditional in `test_firewall.py.j2`

---

### 5. Directory Contracts (Priority: MEDIUM)

**Current state:** `FilesContract` may work for directories but unclear.

**Required:** Explicitly support directory existence and properties.

```yaml
behavioral_contracts:
  files:
    - items:
        - path: "/opt/pyramid_app"
          present: true
          is_directory: true    # NEW
          mode: "0755"
          owner: "app_user"
          group: "app_user"
```

**Implementation:**
- Add `is_directory` boolean to `FileContractItem`
- Modify test generation to use `host.file(path).is_directory`
- Current `present` check may already work but should be explicit

---

### 6. Static File Distribution (Priority: HIGH)

**Current state:** `required_files` copies FROM student repo TO grading bundle.
There is no mechanism to provide files TO students.

**Required:** Include provided files (app.py, templates) in student bundle.

```yaml
entrypoints:
  playbook_path: "playbook.yaml"
  required_files: ["app.py", "app.service.j2"]  # existing: student must provide
  provided_files:    # NEW: assignment provides these
    - source: "app.py"
      destination: "files/app.py"
    - source: "app.service.j2"
      destination: "templates/app.service.j2"
```

**Implementation:**
- Add `provided_files` to `Entrypoints` spec
- During `hammer build`, copy provided files into student bundle
- Store provided files alongside spec or in a `files/` directory
- Runner should verify provided files exist in student submission

---

### 7. Process Contracts (Priority: LOW)

**Current state:** Only systemd services are supported.

**Required:** Verify arbitrary processes are running (e.g., `python3 app.py`).

```yaml
behavioral_contracts:
  processes:    # NEW
    - pattern: "python3.*app\\.py"
      count_min: 1
      count_max: 1    # optional
      user: "app_user"  # optional
      node_selector:
        group: "web"
```

**Implementation:**
- Add `ProcessContract` to spec.py
- Generate test using testinfra's `host.process.filter()`
- Test template: `test_processes.py.j2`

**Note:** For PE1 Basic, this is needed since nohup process is not a systemd service.
However, Extra 2 makes this a systemd service, so this is lower priority.

---

### 8. Idempotence Exceptions (Priority: LOW)

**Current state:** `allowed_changes` lists task names that can change.

**Required:** PE1 Basic explicitly allows non-idempotent app start via shell.

Current spec supports this via `allowed_changes`, so no change needed.
Just document clearly how to use it.

---

## Implementation Roadmap

### Phase A: Core Contracts (enables basic PE1 grading)

1. **Pip Package Contracts** - Required for Basic
2. **User Contracts** - Required for Extra 3
3. **HTTP Endpoint Contracts** - Required for Basic verification
4. **Static File Distribution** - Required to provide app.py to students

### Phase B: Firewall Improvements

5. **iptables Support** - Required for Extra 1
6. **Directory Contracts** - Clarify/improve file contract for directories

### Phase C: Advanced (Optional)

7. **Process Contracts** - Nice-to-have for non-systemd processes

---

## PE1 Spec Draft (with proposed features)

```yaml
assignment_id: "pe1-pyramid-app"
assignment_version: "2026.02"
spec_version: "1.0"
seed: 42
provider: "libvirt"
os: "almalinux9"

features:
  vault: false
  selinux: false
  handlers: false
  reachability: true

topology:
  nodes:
    - name: "web1"
      groups: ["web"]
      resources:
        cpu: 2
        ram_mb: 2048
  forwarded_ports:
    - host_port: 6000
      guest_port: 6000
      protocol: tcp

entrypoints:
  playbook_path: "playbook.yaml"
  required_files: ["playbook.yaml"]
  provided_files:                    # NEW
    - source: "app.py"
      destination: "files/app.py"
    - source: "app.service.j2"
      destination: "templates/app.service.j2"

variable_contracts:
  - name: "app_port"
    type: "int"
    defaults:
      student: 6000
    allowed_values: [6000, 7000]
    grading_overlay_targets:
      - overlay_kind: "group_vars"
        target_name: "web"
    binding_targets:
      - type: "service_listen_port"
        weight: 1.0
        target:
          service: "python3"    # or process name
          protocol: "tcp"
          address: "0.0.0.0"

behavioral_contracts:
  # Basic: system packages
  packages:
    - name: "python3"
      state: "present"
      node_selector: { group: "web" }
      weight: 1.0
    - name: "python3-pip"
      state: "present"
      node_selector: { group: "web" }
      weight: 1.0

  # Basic: pip packages (NEW)
  pip_packages:
    - name: "pyramid"
      state: "present"
      node_selector: { group: "web" }
      weight: 1.0
    - name: "waitress"
      state: "present"
      node_selector: { group: "web" }
      weight: 1.0
    - name: "psutil"
      state: "present"
      node_selector: { group: "web" }
      weight: 1.0
    - name: "distro"
      state: "present"
      node_selector: { group: "web" }
      weight: 1.0

  # Extra 1: iptables
  packages:
    - name: "iptables-services"
      state: "present"
      node_selector: { group: "web" }
      weight: 0.5    # Part of Extra 1

  services:
    - name: "iptables"
      enabled: true
      running: true
      node_selector: { group: "web" }
      weight: 0.5    # Part of Extra 1

  # Extra 1: iptables port (NEW firewall_type)
  firewall:
    - open_ports:
        - port: 6000
          protocol: "tcp"
      firewall_type: "iptables"    # NEW
      node_selector: { group: "web" }
      weight: 1.0

  # Basic + Extra 2: files
  files:
    - items:
        - path: "/opt/pyramid_app"
          present: true
          is_directory: true    # NEW
        - path: "/opt/pyramid_app/app.py"
          present: true
          mode: "0644"
      node_selector: { group: "web" }
      weight: 1.0

    # Extra 2: systemd unit file
    - items:
        - path: "/etc/systemd/system/app.service"
          present: true
          mode: "0644"
          content_regex: "ExecStart=.*python3.*app\\.py"
      node_selector: { group: "web" }
      weight: 1.0

  # Extra 2: systemd service
  services:
    - name: "app"
      enabled: true
      running: true
      node_selector: { group: "web" }
      weight: 1.5    # Extra 2

  # Extra 3: user (NEW)
  users:
    - name: "app_user"
      exists: true
      node_selector: { group: "web" }
      weight: 0.5

  # Extra 3: ownership
  files:
    - items:
        - path: "/opt/pyramid_app/app.py"
          present: true
          owner: "app_user"
          group: "app_user"
      node_selector: { group: "web" }
      weight: 1.0

  # Basic: HTTP endpoint (NEW)
  http_endpoints:
    - url: "http://localhost:6000/hostname"
      method: "GET"
      expected_status: 200
      response_contains: "Hostname:"
      node_selector: { host: "web1" }
      weight: 2.0

idempotence:
  required: true
  allowed_changes:
    - "Start app"    # Allow nohup shell command to report changed
  enforcement:
    require_changed_zero: false    # Due to allowed_changes
    require_no_handlers: true

phase_overlays:
  baseline:
    group_vars:
      web:
        app_port: 6000
  mutation:
    group_vars:
      web:
        app_port: 7000
```

---

## Testing Strategy for PE1 Regression

### Local Development Steps

1. Implement missing features (pip_packages, users, http_endpoints, provided_files)
2. Create PE1 spec (`real_examples/PE1/spec.yaml`)
3. Run `hammer validate --spec real_examples/PE1/spec.yaml`
4. Run `hammer build --spec real_examples/PE1/spec.yaml --out /tmp/pe1`
5. Manually verify student bundle contains app.py
6. Start VMs: `cd /tmp/pe1/grading_bundle && vagrant up`
7. Copy reference solution and grade:
   ```bash
   hammer grade \
       --spec real_examples/PE1/spec.yaml \
       --student-repo real_examples/PE1 \
       --out /tmp/pe1-results \
       --grading-bundle /tmp/pe1/grading_bundle
   ```
8. Verify all tests pass with reference solution

### Automated Regression Test

Add to CI:
```bash
# Integration test for PE1
pytest tests/integration/test_pe1.py -v
```

The test should:
1. Build bundles from PE1 spec
2. Spin up Vagrant VMs (or use container-based testing)
3. Run reference solution playbook
4. Execute grader
5. Assert expected score

---

## AlmaLinux Compatibility Notes

The reference solution uses Amazon Linux conventions:
- User `ec2-user` in systemd unit → Change to `vagrant` or `app_user`
- `yum` package manager → Works on AlmaLinux 9 (dnf alias)
- Python 3 should be available as `python3`

Minor tweaks needed:
1. Update `app.service.j2` User field
2. May need `python3-distro` package instead of pip `distro` on RHEL-based

---

## Summary

**Must implement for PE1:**
1. Pip package contracts
2. User contracts
3. HTTP endpoint contracts
4. Static file distribution (provided_files)
5. iptables firewall support

**Nice to have:**
6. Process contracts (for non-systemd processes)
7. Directory contract clarification

**Estimated new code:**
- ~200 lines spec.py additions
- ~150 lines per test generator (5 new)
- ~100 lines builder changes for provided_files
- Total: ~1000 lines

