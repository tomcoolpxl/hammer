# Plan: Add `hammer init` command

## Context

When writing a new spec and assignment, instructors want to `vagrant up` and manually iterate on their playbook before finalizing behavioral/variable contracts. Currently `hammer build` generates the full student + grading bundles including tests, overlays, and lock files — far more than needed for early-stage development. A lightweight `hammer init` command that emits just the Vagrantfile, inventory, ansible.cfg, and host_vars gives instructors exactly what they need to stand up VMs and test manually.

## Changes

### 1. Add `init_assignment()` to builder (`src/hammer/builder/__init__.py`)

New public function that generates only the infrastructure scaffold:

```python
def init_assignment(spec, output_dir, box_version="generic/alma9"):
```

Produces:
- `Vagrantfile` — via existing `render_vagrantfile()`
- `inventory/hosts.yml` — via existing `render_student_inventory()`
- `ansible.cfg` — via existing `render_ansible_cfg()`
- `host_vars/<node>.yml` — via existing `write_student_host_vars()` (provides `ansible_host` IPs)
- `roles/` — empty directory (playbook convention)

Reuses: `generate_network_plan()`, `render_vagrantfile()`, `render_student_inventory()`, `render_ansible_cfg()`, `write_student_host_vars()`. No execution plan needed (no group_vars/overlays/tests).

Export from `__all__`.

### 2. Add `init` subcommand to CLI (`src/hammer/cli.py`)

- New subparser: `hammer init --spec <file> --out <dir> [--box-version <box>]`
- New handler `_cmd_init(args)` following existing Rich output pattern
- Dispatch in `main()`

### 3. Update prerequisites (`src/hammer/prerequisites.py`)

Add `"init"` alongside `"build"` — no external tools required (just Python/Pydantic), so it passes through with an empty list. Same as `"validate"`.

### 4. Update documentation

- `docs/user-guide/cli-reference.md` — add `## hammer init` section
- `README.md` — add init to the Usage section (between validate and build)
- `docs/QUICKSTART.md` — insert a step between validate and build showing init workflow

### 5. Add unit test (`tests/unit/test_cli.py`)

Add test for `hammer init` following the existing `test_validate_*` pattern — invoke via subprocess, check exit code and that output dir contains exactly Vagrantfile, inventory/hosts.yml, ansible.cfg, host_vars/.

## Files to modify

| File | Change |
|------|--------|
| `src/hammer/builder/__init__.py` | Add `init_assignment()`, export in `__all__` |
| `src/hammer/cli.py` | Add subparser, dispatch, `_cmd_init()` handler |
| `src/hammer/prerequisites.py` | Handle `"init"` command (no-op) |
| `docs/user-guide/cli-reference.md` | Add `## hammer init` docs |
| `README.md` | Add init to Usage section |
| `docs/QUICKSTART.md` | Add init step |
| `tests/unit/test_cli.py` | Add init command test |

## Verification

1. `hammer init --spec real_examples/PE1/spec.yaml --out /tmp/pe1-init` — should create output with only Vagrantfile, inventory/, host_vars/, ansible.cfg, roles/
2. `cd /tmp/pe1-init && vagrant up` should work (manual, not automated)
3. Run existing test suite: `pytest tests/unit/ tests/integration/ -v` — all pass, plus new init test
