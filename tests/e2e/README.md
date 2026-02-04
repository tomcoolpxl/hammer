# HAMMER E2E Tests

These tests perform full grading runs using real Vagrant VMs and the PE1 (Pyramid App) assignment.

## Prerequisites

- **Vagrant** installed and in PATH.
- **libvirt** (KVM) installed and configured.
- **AlmaLinux 9** Vagrant box available (`generic/alma9`).
- Python environment with all dependencies installed.

## Running E2E Tests

E2E tests are slow and resource-intensive because they bring up actual virtual machines. They are marked with `@pytest.mark.e2e`.

To run all E2E tests:

```bash
.venv/bin/python -m pytest tests/e2e/ -v -m e2e
```

**Note**: The tests use `vagrant up` and `vagrant destroy`. If a test is interrupted, you may need to manually clean up VMs:

```bash
# Find and destroy any leftover VMs
virsh list --all
vagrant global-status --prune
```

## What is tested?

- `hammer build`: Verifies that grading and student bundles can be generated for PE1.
- `hammer grade`:
    - Verifies that an empty playbook correctly fails the assignment (0% score).
    - Verifies that the provided solution playbook (`real_examples/PE1/playbook_solution.yaml`) passes with a 100% score.
    - Verifies all three phases: baseline, mutation, and idempotence.
