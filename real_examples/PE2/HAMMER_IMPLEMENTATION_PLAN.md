# Hammer Implementation Plan for PE2 Support

## Executive Summary

This document outlines what was needed to make Hammer fully support the PE2 assignment
as a regression test.

**Status Summary:**

| Feature | Status | Priority | Effort |
|---------|--------|----------|--------|
| GroupContract | DONE | HIGH | - |
| Per-node port forwarding | DONE | HIGH | - |
| /etc/hosts provisioning | DONE | HIGH | - |
| Domain/FQDN support | DONE | MEDIUM | - |
| Vault password integration | DONE | LOW | - |

---

## Completed Features

### 1. GroupContract (DONE)

Added `GroupContract` to spec.py for verifying system groups exist:

```yaml
behavioral_contracts:
  groups:
    - name: "mysql"
      exists: true
      gid: 1000  # optional
      node_selector: { group: "dbservers" }
      weight: 2.0
```

**Files changed:**
- `src/hammer/spec.py` - Added `GroupContract` model
- `src/hammer/plan.py` - Added `GroupCheck` dataclass
- `src/hammer/testgen/behavioral.py` - Added `generate_group_tests()`
- `src/hammer/testgen/templates/test_groups.py.j2` - New template
- `src/hammer/testgen/__init__.py` - Wire up group tests

### 2. Per-Node Port Forwarding (DONE)

Moved `forwarded_ports` from `Topology` level to `Node` level:

```yaml
topology:
  nodes:
    - name: "server0"
      groups: ["webservers"]
      resources:
        cpu: 1
        ram_mb: 1024
      forwarded_ports:
        - host_port: 8888
          guest_port: 80
          protocol: tcp
    - name: "server1"
      groups: ["dbservers"]
      resources:
        cpu: 1
        ram_mb: 1024
      forwarded_ports:
        - host_port: 8889
          guest_port: 80
          protocol: tcp
```

**Files changed:**
- `src/hammer/spec.py` - Moved `ForwardedPort` before `Node`, added `forwarded_ports` to `Node`
- `src/hammer/builder/templates/Vagrantfile.j2` - Render per-node ports

### 3. /etc/hosts Provisioning (DONE)

Added shell provisioner to Vagrantfile template that populates /etc/hosts on each VM:

```ruby
server0.vm.provision "shell", inline: <<-SHELL
  grep -q "server0.pxldemo.local" /etc/hosts || echo "192.168.116.10 server0 server0.pxldemo.local" >> /etc/hosts
  grep -q "server1.pxldemo.local" /etc/hosts || echo "192.168.116.11 server1 server1.pxldemo.local" >> /etc/hosts
SHELL
```

**Files changed:**
- `src/hammer/builder/templates/Vagrantfile.j2` - Added /etc/hosts provisioner

### 4. Domain/FQDN Support (DONE)

Added optional `domain` field to Topology:

```yaml
topology:
  domain: "pxldemo.local"
  nodes:
    - name: "server0"
      # hostname becomes: server0.pxldemo.local
```

When domain is set:
- VM hostnames use FQDN
- Inventory uses FQDN as host identifiers
- host_vars files use FQDN in filename
- /etc/hosts includes both short and FQDN

**Files changed:**
- `src/hammer/spec.py` - Added `domain` to `Topology`
- `src/hammer/builder/vagrantfile.py` - Pass domain to template
- `src/hammer/builder/templates/Vagrantfile.j2` - Use FQDN for hostname
- `src/hammer/builder/inventory.py` - Pass domain, use FQDN in filenames
- `src/hammer/builder/templates/student_inventory.yml.j2` - Use FQDN in inventory

### 5. Vault Password Integration (DONE)

Added vault password support for encrypted Ansible vault files:

```yaml
features:
  vault: true

vault:
  vault_password: "passwordpxl"
  vaulted_vars_files:
    - "vault.yml"
  vaulted_variables:
    - "vault_secret_key"
  bindings_to_verify: []
```

When vault is configured:
- `.vault_pass` file is generated in grading bundle (mode 0600)
- `--vault-password-file` can be passed to `run_playbook()`

**Files changed:**
- `src/hammer/spec.py` - Added `vault_password` field to `VaultSpec`
- `src/hammer/builder/__init__.py` - Generate `.vault_pass` file
- `src/hammer/runner/ansible.py` - Added `vault_password_file` parameter to `run_playbook()`

---

## PE2 Spec

The `spec.yaml` file is now complete and can be built with:

```bash
# Python API
from hammer.spec import load_spec_from_file
from hammer.builder import build_assignment

spec = load_spec_from_file(Path('real_examples/PE2/spec.yaml'))
lock = build_assignment(spec, Path('output'), spec_dir=Path('real_examples/PE2'))

# Or via CLI (when available)
hammer build real_examples/PE2/spec.yaml -o output
```

---

## Next Steps

1. **Create solution playbooks** that pass all behavioral contracts
2. **Test locally**: `vagrant up` in student_bundle, run playbooks, verify
3. **Integration test**: Run generated tests against solution
4. **CI integration**: Add PE2 as regression test

---

## Generated Artifacts

When built, PE2 produces:

```
output/
├── lock.json
├── student_bundle/
│   ├── Vagrantfile
│   ├── ansible.cfg
│   ├── README.md
│   ├── inventory/
│   │   └── hosts.yml
│   ├── group_vars/
│   │   ├── all.yml
│   │   ├── servers.yml
│   │   ├── webservers.yml
│   │   └── dbservers.yml
│   ├── host_vars/
│   │   ├── server0.pxldemo.local.yml
│   │   └── server1.pxldemo.local.yml
│   └── templates/
│       ├── httpd.conf.j2
│       ├── index.html.j2
│       └── motd.j2
└── grading_bundle/
    ├── Vagrantfile
    ├── ansible.cfg
    ├── inventory/
    ├── group_vars/
    ├── host_vars/
    ├── overlays/
    │   ├── baseline/
    │   └── mutation/
    └── tests/
        ├── conftest.py
        ├── baseline/
        │   ├── test_packages.py
        │   ├── test_services.py
        │   ├── test_users.py
        │   ├── test_groups.py  # NEW
        │   ├── test_files.py
        │   ├── test_firewall.py
        │   └── test_http.py
        ├── mutation/
        └── idempotence/
```
