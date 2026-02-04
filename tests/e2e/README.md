# HAMMER E2E Tests

These tests perform full grading runs using real Vagrant VMs and the PE1, PE3, and PE4 assignments.

## Prerequisites

- **Vagrant** installed and in PATH.
- **libvirt** (KVM) installed and configured.
- **AlmaLinux 9** Vagrant box available (`generic/alma9`).
- Python environment with all dependencies installed.

## Running E2E Tests

E2E tests are slow and resource-intensive because they bring up actual virtual machines. They are marked with `@pytest.mark.e2e`.

### Running with Live Output

For real-time progress during long-running tests, use the `-s` flag to disable output capture:

```bash
# Show all output including vagrant/ansible progress
.venv/bin/python -m pytest tests/e2e/ -v -s

# Or use the shorthand
.venv/bin/python -m pytest tests/e2e/ -vs
```

The `-s` flag shows progress as tests run, which is helpful for debugging and monitoring.

### Run All E2E Tests

```bash
.venv/bin/python -m pytest tests/e2e/ -v -s -m e2e
```

### Run Specific Assignment Tests

```bash
# PE1 (Pyramid App)
.venv/bin/python -m pytest tests/e2e/test_pe1_grading.py -v -s

# PE3 (Nginx Webserver)
.venv/bin/python -m pytest tests/e2e/test_pe3_grading.py -v -s

# PE4 (Ansible Exam)
.venv/bin/python -m pytest tests/e2e/test_pe4_grading.py -v -s
```

**Note**: The tests use `vagrant up` and `vagrant destroy`. If a test is interrupted, you may need to manually clean up VMs:

```bash
# Find and destroy any leftover VMs
virsh list --all
vagrant global-status --prune
```

## What is tested?

Each assignment (PE1, PE3, PE4) has two test scenarios:

1. **Empty Playbook/Role Test**: Verifies that an empty or minimal playbook/role correctly fails the assignment (< 50% score).

2. **Solution Playbook/Role Test**: Verifies that the provided solution (`playbook_solution.yaml` or solution role) passes with at least 80% score.

### PE1 (Pyramid App)
- Tests baseline, mutation, and idempotence phases.
- Uses `real_examples/PE1/playbook_solution.yaml`.

### PE3 (Nginx Webserver)
- Tests nginx configuration with parameterized ports.
- Uses `real_examples/PE3/playbook_solution.yml`.

### PE4 (Ansible Exam)
- Tests role-based configuration with users, services, and conditional files.
- Uses `real_examples/PE4/roles/pxl_exam_role/`.

## Test Thresholds

- Empty playbook/role: Must score < 50% (verifies grading detects missing work)
- Solution playbook/role: Must score >= 80% (allows for minor flakiness)

## Troubleshooting

If tests fail, the output will show:
- Failed test names and messages
- Grading scores for each scenario
- STDOUT/STDERR from hammer commands

Use `-s` flag to see real-time progress and identify where tests get stuck.
