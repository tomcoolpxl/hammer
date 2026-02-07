# HAMMER Quickstart

Get up and running with HAMMER in 5 minutes.

## Prerequisites

- Python 3.10+
- Ansible (`pip install ansible`)
- Vagrant + libvirt (for grading only)

## Install

```bash
git clone <repo-url>
cd hammer
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## 1. Validate a Spec

```bash
hammer validate --spec real_examples/PE1/spec.yaml
```

This checks YAML syntax, Pydantic model validation, and cross-field semantic rules.

## 2. Build Assignment Bundles

```bash
hammer build --spec real_examples/PE1/spec.yaml --out /tmp/pe1-build
```

This generates:
- `student_bundle/` — Vagrantfile, inventory, scaffolding for students
- `grading_bundle/` — Inventory, overlays, generated pytest tests
- `lock.json` — Deterministic build metadata

## 3. Grade a Submission

```bash
hammer grade \
  --spec real_examples/PE1/spec.yaml \
  --student-repo real_examples/PE1/ \
  --out /tmp/pe1-results \
  --verbose
```

This runs the full pipeline: build, vagrant up, converge, test, report.

## 4. Run Specific Phases

```bash
hammer grade \
  --spec real_examples/PE1/spec.yaml \
  --student-repo real_examples/PE1/ \
  --out /tmp/pe1-results \
  --phase baseline --phase mutation
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `HAMMER_PLAYBOOK_TIMEOUT` | 600 | Ansible playbook timeout (seconds) |
| `HAMMER_PYTEST_TIMEOUT` | 300 | Pytest test timeout (seconds) |
| `HAMMER_REBOOT_TIMEOUT` | 120 | Node reboot timeout (seconds) |

## Next Steps

- See `docs/user-guide/` for spec authoring guide
- See `CONTRIBUTING.md` for development setup
- See `docs/TROUBLESHOOTING.md` for common issues
