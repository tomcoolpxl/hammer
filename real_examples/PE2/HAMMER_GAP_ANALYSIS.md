# Hammer Gap Analysis for PE2 Assignment

This document analyzes what features are missing from Hammer to fully support creating
assignments like PE2, and proposes an implementation plan.

## Executive Summary

PE2 is a multi-VM Ansible automation assignment requiring students to configure Apache
and Chrony services across two AlmaLinux servers. Comparing PE2 requirements against
Hammer's current capabilities reveals these gaps:

| Gap | Priority | Effort | Status |
|-----|----------|--------|--------|
| Group behavioral contract | HIGH | Low | Missing |
| Per-node port forwarding | HIGH | Low | Missing |
| Vault password integration | MEDIUM | Medium | Partial |
| Domain/FQDN in hostnames | LOW | Low | Missing |

---

## Detailed Gap Analysis

### 1. Group Behavioral Contract (HIGH PRIORITY)

**Current State:** Hammer has `UserContract` but no `GroupContract`

**PE2 Requirement:**
- Create `mysql` group on server1
- Verify group exists before creating user

**What's Needed:**
- Add `GroupContract` to spec.py:
```python
class GroupContract(BaseModel):
    name: NonEmptyStr
    exists: bool = True
    gid: Optional[int] = None
    node_selector: NodeSelector
    weight: float = Field(default=1.0, ge=0.0)
```
- Add `groups` to `BehavioralContracts`
- Create `test_groups.py.j2` template
- Update `plan.py` with `GroupCheck` dataclass
- Update `behavioral.py` with `generate_group_tests()`

---

### 2. Per-Node Port Forwarding (HIGH PRIORITY)

**Current State:** `forwarded_ports` is topology-level, applies uniformly

**PE2 Requirement:**
```
server0: guest 22 -> host 2222, guest 80 -> host 8888
server1: guest 22 -> host 2200, guest 80 -> host 8889
```

**What's Needed:**
- Move `forwarded_ports` from `Topology` to `Node` level:
```python
class Node(BaseModel):
    name: NonEmptyStr
    groups: List[NonEmptyStr]
    resources: NodeResources
    forwarded_ports: Optional[List[ForwardedPort]] = None  # NEW
```
- Update Vagrantfile.j2 template to render per-node ports
- Update inventory generation to use correct SSH ports

---

### 3. Vault Password Integration (MEDIUM PRIORITY)

**Current State:** `features.vault: true` flag exists, `VaultSpec` defined, but:
- No vault password file generation
- No vault variable injection during grading
- No `--vault-password-file` passed to ansible-playbook

**PE2 Requirement:**
- Vault file encrypted with password `passwordpxl`
- Variable `vault_secret_key: PXLPXL`
- Test that `/var/www/html/secret.txt` contains vault value

**What's Needed:**
- Add `vault_password` field to VaultSpec
- Generate `.vault_pass` file in grading bundle
- Pass `--vault-password-file` to ansible-playbook calls in runner
- Current file `content_regex` tests can verify the outcome

---

### 4. Domain/FQDN Configuration (LOW PRIORITY)

**Current State:** Hostname = node name only

**PE2 Requirement:**
- Short hostname: `server0`
- FQDN: `server0.pxldemo.local`

**What's Needed:**
- Add optional `domain` field to topology:
```yaml
topology:
  domain: "pxldemo.local"  # NEW, optional
  nodes: [...]
```
- Generate FQDN as `{node.name}.{domain}` when domain is set

---

## Features Already Covered

These PE2 requirements work with current Hammer:

| PE2 Requirement | Hammer Coverage |
|-----------------|-----------------|
| Package installation (httpd, chrony, etc.) | `packages` contract |
| Service running/enabled (httpd, chronyd) | `services` contract |
| User creation (mysql, webadmin, etc.) | `users` contract |
| File/directory existence | `files` contract |
| File ownership (mysql:mysql) | `files` contract with owner/group |
| Firewall port open (8080) | `firewall` contract |
| HTTP endpoint test | `http_endpoints` contract |
| Content verification | `files` contract with content_regex |
| Multi-node topology | Already supported |
| Group vars per host group | Already supported |

---

## Implementation Plan

### Phase 1: Enable PE2 (Required)

**Task 1.1: Add GroupContract** (~2 hours)
```
Files to modify:
- src/hammer/spec.py          # Add GroupContract model
- src/hammer/plan.py          # Add GroupCheck dataclass
- src/hammer/testgen/behavioral.py    # Add generate_group_tests()
- src/hammer/testgen/templates/test_groups.py.j2  # New template
- src/hammer/testgen/__init__.py      # Wire up group tests
```

**Task 1.2: Per-Node Port Forwarding** (~2 hours)
```
Files to modify:
- src/hammer/spec.py          # Move forwarded_ports to Node
- src/hammer/builder/templates/Vagrantfile.j2  # Per-node ports
- src/hammer/builder/__init__.py  # Update inventory SSH ports
```

### Phase 2: Nice to Have

**Task 2.1: Vault Integration** (~3 hours)
```
Files to modify:
- src/hammer/spec.py          # Add vault_password to VaultSpec
- src/hammer/builder/__init__.py  # Generate .vault_pass
- src/hammer/runner/__init__.py   # Pass --vault-password-file
```

**Task 2.2: Domain Support** (~1 hour)
```
Files to modify:
- src/hammer/spec.py          # Add domain to Topology
- src/hammer/builder/templates/Vagrantfile.j2  # Use FQDN
```

---

## PE2 Spec Draft (Once Phase 1 Complete)

```yaml
assignment_id: "pe2-ansible-automation"
assignment_version: "2026.02"
spec_version: "1.0"
seed: 42
provider: "libvirt"
os: "almalinux9"

features:
  vault: false  # Skip for now, test basic first
  selinux: false
  handlers: false
  reachability: false

topology:
  nodes:
    - name: "server0"
      groups: ["servers", "webservers"]
      resources:
        cpu: 1
        ram_mb: 1024
      forwarded_ports:
        - host_port: 8080
          guest_port: 8080
          protocol: tcp
    - name: "server1"
      groups: ["servers", "dbservers"]
      resources:
        cpu: 1
        ram_mb: 1024

entrypoints:
  playbook_path: "playbook.yml"
  required_files:
    - "playbook.yml"
  provided_files:
    - source: "templates/httpd.conf.j2"
      destination: "templates/httpd.conf.j2"
    - source: "templates/index.html.j2"
      destination: "templates/index.html.j2"
    - source: "templates/motd.j2"
      destination: "templates/motd.j2"

variable_contracts:
  - name: "http_port"
    type: "int"
    defaults:
      student: 8080
    allowed_values: [8080, 9090]
    grading_overlay_targets:
      - overlay_kind: "group_vars"
        target_name: "webservers"
    binding_targets:
      - type: "service_listen_port"
        weight: 2.0
        target:
          service: "httpd"
          protocol: "tcp"
          address: "0.0.0.0"
      - type: "firewall_port_open"
        weight: 2.0
        target:
          zone: "public"
          protocol: "tcp"

behavioral_contracts:
  packages:
    # Basic - Web server
    - name: "httpd"
      state: "present"
      node_selector: { group: "webservers" }
      weight: 5.0
    # Basic - DB server
    - name: "chrony"
      state: "present"
      node_selector: { group: "dbservers" }
      weight: 3.0

  services:
    - name: "httpd"
      enabled: true
      running: true
      node_selector: { group: "webservers" }
      weight: 5.0
    - name: "chronyd"
      enabled: true
      running: true
      node_selector: { group: "dbservers" }
      weight: 3.0

  # NEW - requires GroupContract implementation
  groups:
    - name: "mysql"
      exists: true
      node_selector: { group: "dbservers" }
      weight: 2.0

  users:
    - name: "mysql"
      exists: true
      groups: ["mysql"]
      node_selector: { group: "dbservers" }
      weight: 3.0

  files:
    # Backup directory with ownership
    - items:
        - path: "/opt/backup"
          present: true
          is_directory: true
          owner: "mysql"
          group: "mysql"
      node_selector: { group: "dbservers" }
      weight: 3.0
    # Index.html deployed
    - items:
        - path: "/var/www/html/index.html"
          present: true
      node_selector: { group: "webservers" }
      weight: 2.0

  firewall:
    - open_ports:
        - port: { var: "http_port" }
          protocol: "tcp"
          zone: "public"
      firewall_type: "firewalld"
      node_selector: { group: "webservers" }
      weight: 4.0

  http_endpoints:
    - url: "http://localhost:8080/"
      method: "GET"
      expected_status: 200
      response_contains: "Ansible Test Deployment"
      timeout_seconds: 10
      node_selector: { host: "server0" }
      weight: 5.0

idempotence:
  required: true
  enforcement:
    require_changed_zero: true
    require_no_handlers: true

phase_overlays:
  baseline:
    group_vars:
      webservers:
        http_port: 8080
      dbservers:
        backup_dir: "/opt/backup"
  mutation:
    group_vars:
      webservers:
        http_port: 9090
      dbservers:
        backup_dir: "/opt/backup"
```

---

## Regression Test Strategy

1. **Create PE2 spec** after implementing GroupContract
2. **Create solution playbooks** that pass all tests
3. **Validate locally**: `hammer build`, `vagrant up`, `hammer grade`
4. **Add to CI** as integration test

---

## Summary: Minimum Viable Changes

To support PE2-style assignments:

1. **Must have**: GroupContract (for testing `mysql` group creation)
2. **Should have**: Per-node port forwarding (for different SSH/HTTP ports per VM)
3. **Nice to have**: Vault integration, domain support
