# HAMMER CLI Reference

## `hammer validate`

Validates a specification file against the HAMMER schema.

**Usage:**
```bash
hammer validate --spec <file.yaml>
```

---

## `hammer init`

Generates only the Vagrantfile, inventory, and ansible.cfg from a spec. Use this when developing a new assignment to stand up VMs and manually iterate on your playbook before finalizing contracts.

**Usage:**
```bash
hammer init --spec <file.yaml> --out <output_dir>
```

**Options:**
- `--spec`: (Required) Path to the spec file.
- `--out`: (Required) Directory to write infrastructure files into.
- `--box-version`: Vagrant box to use (default: `generic/alma9`).

**Generated files:**
- `Vagrantfile` — VM definitions with networking
- `inventory/hosts.yml` — Ansible inventory with groups
- `ansible.cfg` — Ansible configuration pointing to the inventory
- `host_vars/<node>.yml` — Per-node `ansible_host` IP assignments
- `roles/` — Empty directory for role development

**Typical workflow:**
```bash
# 1. Generate infrastructure from your spec
hammer init --spec spec.yaml --out ./lab

# 2. Bring up VMs
cd ./lab && vagrant up

# 3. Verify connectivity
ansible all -m ping

# 4. Develop your playbook
ansible-playbook site.yml

# 5. Once satisfied, go back and finalize contracts in spec.yaml
# 6. Then use `hammer build` for the full student/grading bundles
```

---

## `hammer build`

Generates student and grading bundles from a specification.

**Usage:**
```bash
hammer build --spec <file.yaml> --out <output_dir>
```

**Options:**
- `--spec`: (Required) Path to the spec file.
- `--out`: (Required) Directory to create bundles in.
- `--box-version`: Vagrant box to use (default: `generic/alma9`).

---

## `hammer grade`

Executes the full grading pipeline for a student submission.

**Usage:**
```bash
hammer grade --spec <spec.yaml> --student-repo <repo_dir> --out <results_dir> [options]
```

**Options:**
- `--spec`: (Required) Path to the spec file.
- `--student-repo`: (Required) Path to the student's playbook/roles.
- `--out`: (Required) Directory to store results.
- `--grading-bundle`: Path to an existing grading bundle with already running VMs.
- `--skip-build`: Use the existing grading bundle in the output directory instead of regenerating it.
- `--phase`: Run only specific phase(s) (baseline, mutation, idempotence). Can be repeated.
- `--verbose, -v`: Enable verbose output (shows Ansible and Pytest output).
