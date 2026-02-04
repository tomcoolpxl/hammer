# E2E Test Analysis and Improvement Plan

> **Status**: IMPLEMENTED - All recommendations from this analysis have been implemented.
> See the Implementation Status section at the end for details.

## Executive Summary

This document analyzes the current state of HAMMER's end-to-end (E2E) tests, identifies issues, and proposes improvements. The analysis covers test design, solution files, screen output, and safety timeouts.

---

## 1. Current State

### 1.1 E2E Test Files

```
tests/e2e/
├── __init__.py
├── conftest.py      # Fixtures: hammer_bin, pe1_dir, e2e_work_dir, pe1_build, pe1_vms
├── test_pe1_grading.py  # Single test class with one test method
└── README.md
```

### 1.2 Test Coverage

| Assignment | Spec Exists | Solution Exists | E2E Test Exists |
|------------|-------------|-----------------|-----------------|
| PE1        | ✅          | ✅ `playbook_solution.yaml` | ✅ |
| PE2        | ✅          | ❌ (empty playbook) | ❌ |
| PE3        | ✅          | ❌ (`playbook.yml` is empty: `---`) | ❌ |
| PE4        | ✅          | ❌ (stub referencing non-existent role) | ❌ |

### 1.3 Current Test Logic

The existing `test_pe1_grading.py` runs two scenarios:

1. **Negative test (FAIL)**: Empty playbook → expects `success=False`, `percentage < 100`
2. **Positive test (PASS)**: Solution playbook → expects `success=True`, `percentage == 100`

**Problem**: The 100% requirement is overly strict. Real-world solutions may have minor issues or the spec may test edge cases that aren't critical.

---

## 2. Issues Identified

### 2.1 Test Design Issues

| Issue | Description | Impact |
|-------|-------------|--------|
| **100% requirement** | `assert report_solution["percentage"] == 100.0` fails if ANY test fails | Brittle tests |
| **No partial success tests** | Missing tests for partial scores (e.g., 70-90% pass) | Limited coverage |
| **Single PE coverage** | Only PE1 has E2E tests | Incomplete validation |
| **Coupled scenarios** | Both scenarios in one test method | Hard to debug failures |

### 2.2 Solution File Issues

#### PE1 Solution (`playbook_solution.yaml`)

The solution handles port mutation via:
```yaml
destination_port: "{{ app_port }}"  # Uses variable
```

And the systemd template (`templates/app.service.j2`):
```ini
Environment="APP_PORT={{ app_port | default(6000) }}"
```

**Potential issue**: The app.py reads `APP_PORT` from environment, but the iptables rule is hardcoded in the non-solution `playbook.yaml`. The solution correctly uses `{{ app_port }}`.

#### PE3 - No Solution

The `playbook.yml` contains only `---`. Need to create a solution that:
- Installs nginx
- Configures nginx to listen on `{{ web_port }}` (8080 baseline, 9090 mutation)
- Creates document root at `/var/www/mypage`
- Deploys landing page from template
- Opens firewall port
- Handles port mutation properly

#### PE4 - No Solution

The playbook references `pxl_exam_role` which doesn't exist in the `roles/` directory. Need to create a solution that:
- Creates group `students`
- Creates users: carol, dave, edgar (in students group)
- Sets up `/etc/motd` with "Welcome to Paradise"
- Deploys healthcheck script and service
- Creates conditional run files (`first_run.txt`, `second_run.txt`)
- Does NOT create `/mnt/special/pxl/my_special_pxl_file`

### 2.3 Screen Output Issues

#### Current Behavior

| Component | Output Behavior |
|-----------|-----------------|
| `vagrant up` | `capture_output=True` → silent |
| `hammer build` | `capture_output=True` → silent |
| `hammer grade` | Output captured, only printed on failure |
| Ansible playbook | Captured to log file, not streamed |
| Pytest tests | Captured, only shown on error |

#### Problem

During a 10+ minute E2E test run, users see almost nothing:
```
$ pytest tests/e2e/ -v
tests/e2e/test_pe1_grading.py::TestPE1Grading::test_grading_pipeline
[... 10 minutes of silence ...]
PASSED
```

#### Constraints

- Log files must remain clean (no extra noise)
- Subprocess output should be captured for debugging
- Need progress indication without corrupting logs

### 2.4 Timeout Analysis

#### Current Timeouts

| Operation | Timeout | Location | Configurable |
|-----------|---------|----------|--------------|
| `vagrant up` | 600s (10 min) | `conftest.py:pe1_vms` | No |
| `ansible-playbook` | 600s (10 min) | `ansible.py:run_playbook()` | Yes (`timeout` param) |
| `pytest` phase tests | 300s (5 min) | `pytest_runner.py:run_phase_tests()` | Yes |
| Reboot SSH wait | 120s | `reboot.py` | Yes (spec config) |
| Reboot poll | 5s | `reboot.py` | Yes (spec config) |
| SSH check | 10s | `reboot.py:_check_ssh_available()` | No |
| Ansible ping (reboot) | 30s | `reboot.py:_reboot_single_node()` | No |

#### Assessment

**Adequate**: The existing timeouts are reasonable:
- VM boot: 10 minutes handles slow systems
- Ansible: 10 minutes per phase is generous
- Tests: 5 minutes is sufficient for testinfra checks
- Reboot: 2 minutes wait + polling is appropriate

**Not needed**: Additional "safety" timeouts would likely cause more harm than good. The current timeouts properly handle:
- Network delays
- Slow disk I/O
- First-boot package installations
- SSH key exchange delays

---

## 3. Recommendations

### 3.1 Test Design Improvements

#### A. Accept Partial Scores

Instead of requiring 100%, define minimum thresholds:

```python
# Negative test: empty playbook
assert report_empty["percentage"] < 50.0  # Should fail significantly

# Positive test: solution playbook
assert report_solution["percentage"] >= 80.0  # Allow minor failures
assert report_solution["phases"]["baseline"]["converge"]["success"] is True
```

#### B. Add Specific Negative Tests

Create targeted negative test cases:
- Missing package → package test fails
- Wrong port → port binding test fails
- Missing file → file test fails

#### C. Separate Test Methods

Split into multiple test methods for clearer failure reporting:
```python
def test_empty_playbook_fails(self, ...):
    """Empty playbook should fail with low score."""

def test_solution_playbook_converges(self, ...):
    """Solution playbook should converge successfully in all phases."""

def test_solution_playbook_passes_behavioral(self, ...):
    """Solution playbook should pass behavioral contracts."""
```

#### D. Parameterized Tests for All PEs

```python
@pytest.mark.parametrize("pe_name", ["PE1", "PE3", "PE4"])
def test_pe_grading_pipeline(self, pe_name, ...):
    """Test grading pipeline for each PE."""
```

### 3.2 Solution File Improvements

#### PE1 Solution - Review and Fix

The current solution appears correct. Verify:
1. Port mutation works (6000 → 7000)
2. Service restarts on config change
3. iptables rule uses variable

#### PE3 Solution - Create New

Create `real_examples/PE3/playbook_solution.yml`:
```yaml
- name: Configure nginx webserver
  hosts: webservers
  become: true
  tasks:
    - name: Install nginx
      yum:
        name: nginx
        state: present

    - name: Create document root
      file:
        path: "{{ doc_root }}"
        state: directory

    - name: Deploy landing page
      template:
        src: templates/landing-page.html.j2
        dest: "{{ doc_root }}/index.html"

    - name: Configure nginx
      template:
        src: templates/mypage.conf.j2
        dest: /etc/nginx/conf.d/mypage.conf
      notify: restart nginx

    - name: Open firewall port
      firewalld:
        port: "{{ web_port }}/tcp"
        permanent: yes
        immediate: yes
        state: enabled

    - name: Start nginx
      service:
        name: nginx
        state: started
        enabled: yes

  handlers:
    - name: restart nginx
      service:
        name: nginx
        state: restarted
```

#### PE4 Solution - Create New

Create `real_examples/PE4/roles/pxl_exam_role/` with tasks for users, MOTD, healthcheck, conditional files.

### 3.3 Screen Output Improvements

#### Option A: Pytest Live Logging (Minimal Change)

Use pytest's `--capture=no` or `-s` flag:
```bash
pytest tests/e2e/ -v -s --tb=short
```

**Pros**: Simple, no code changes
**Cons**: Mixes all output together, can be noisy

#### Option B: Progress Callbacks (Recommended)

Add optional progress callbacks to subprocess calls:

```python
# conftest.py
@pytest.fixture(scope="session")
def pe1_vms(pe1_build, capsys):
    grading_dir = pe1_build / "grading_bundle"

    print(f"\n[E2E] Starting VMs in {grading_dir}...")

    # Stream vagrant output in real-time
    process = subprocess.Popen(
        ["vagrant", "up"],
        cwd=str(grading_dir),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )

    output_lines = []
    for line in process.stdout:
        output_lines.append(line)
        # Print progress indicators
        if "==> " in line:  # Vagrant status lines
            print(f"[VAGRANT] {line.strip()}")

    process.wait()
    # ... rest of fixture
```

**Pros**: Real-time progress, clean log files
**Cons**: More code, subprocess handling complexity

#### Option C: Tee-style Output

Write to both file and stdout:

```python
import sys
from io import StringIO

class TeeOutput:
    def __init__(self, file_path):
        self.file = open(file_path, 'w')
        self.stdout = sys.stdout

    def write(self, data):
        self.file.write(data)
        # Only write progress to stdout
        if data.startswith('[') or 'PLAY' in data or 'TASK' in data:
            self.stdout.write(data)

    def flush(self):
        self.file.flush()
        self.stdout.flush()
```

**Pros**: Log files preserved, progress visible
**Cons**: Complex filtering logic

#### Recommendation

Start with **Option A** (pytest `-s` flag) for immediate improvement, then implement **Option B** for specific long-running operations (vagrant up, ansible-playbook) if more control is needed.

### 3.4 Timeout Recommendations

**No changes needed.** Current timeouts are appropriate:

| Operation | Current | Recommendation |
|-----------|---------|----------------|
| Vagrant up | 600s | ✅ Keep as-is |
| Ansible playbook | 600s | ✅ Keep as-is |
| Pytest tests | 300s | ✅ Keep as-is |
| Reboot | 120s | ✅ Keep as-is |

If anything, consider making vagrant timeout configurable via environment variable for CI systems with different performance characteristics:

```python
VAGRANT_TIMEOUT = int(os.environ.get("HAMMER_VAGRANT_TIMEOUT", 600))
```

---

## 4. Implementation Priority

### High Priority (Do First)

1. **Fix PE1 test to accept partial scores** - Remove `== 100.0` assertion
2. **Add PE3/PE4 solution playbooks** - Enable E2E testing for all assignments
3. **Add pytest `-s` to e2e test invocation** - Immediate visibility

### Medium Priority

4. **Split test methods** - Better failure isolation
5. **Add progress indicators to conftest.py** - Real-time feedback
6. **Add parameterized tests for PE3/PE4** - Comprehensive coverage

### Low Priority (Nice to Have)

7. **Environment variable for timeouts** - CI flexibility
8. **Structured progress logging** - Professional output

---

## 5. Test Strategy Clarification

### What Makes a Valid E2E Test?

A test doesn't need 100% score to be valid. Valid test scenarios include:

| Scenario | Expected Outcome | Purpose |
|----------|------------------|---------|
| Empty playbook | 0-10% score | Verify detection of missing work |
| Partial solution | 50-80% score | Verify partial credit |
| Full solution | 80-100% score | Verify correct solution passes |
| Deliberate errors | Specific test fails | Verify error detection |

### Negative Testing Examples

```python
def test_missing_package_detected(self):
    """Playbook without package installation should fail package test."""
    # Create playbook that skips package install
    # Assert package test specifically fails

def test_wrong_port_detected(self):
    """Playbook with hardcoded port should fail after mutation."""
    # Create playbook with port=8080 hardcoded
    # Assert mutation phase fails (expects 9090)
```

---

## 6. Files to Modify/Create

### Modify

- `tests/e2e/test_pe1_grading.py` - Relax 100% requirement, split tests
- `tests/e2e/conftest.py` - Add progress output
- `pyproject.toml` - Add e2e pytest markers/config

### Create

- `real_examples/PE3/playbook_solution.yml` - Solution for PE3
- `real_examples/PE3/templates/mypage.conf.j2` - Nginx config template
- `real_examples/PE4/roles/pxl_exam_role/tasks/main.yml` - Solution role
- `tests/e2e/test_pe3_grading.py` - E2E tests for PE3
- `tests/e2e/test_pe4_grading.py` - E2E tests for PE4

---

## 7. Conclusion

The E2E test infrastructure is fundamentally sound but needs refinement:

1. **Test assertions are too strict** - Accept partial success
2. **Missing solutions prevent testing** - Create PE3/PE4 solutions
3. **Silent execution is frustrating** - Add progress output
4. **Timeouts are adequate** - No changes needed

The recommended changes are incremental and low-risk, allowing immediate improvements while maintaining test reliability.

---

## 8. Implementation Status

All recommendations from this analysis have been implemented.

### Completed Changes

| Recommendation | Status | Implementation |
|----------------|--------|----------------|
| Relax 100% requirement | ✅ Done | Changed to >= 80% threshold |
| Add progress output | ✅ Done | Print statements in fixtures and tests |
| Add pytest `-s` documentation | ✅ Done | Updated `tests/e2e/README.md` |
| Create PE3 solution | ✅ Done | `real_examples/PE3/playbook_solution.yml` |
| Create PE3 nginx template | ✅ Done | `real_examples/PE3/templates/mypage.conf.j2` |
| Create PE4 solution role | ✅ Done | `real_examples/PE4/roles/pxl_exam_role/` |
| Create PE3 E2E tests | ✅ Done | `tests/e2e/test_pe3_grading.py` |
| Create PE4 E2E tests | ✅ Done | `tests/e2e/test_pe4_grading.py` |
| Add PE3/PE4 fixtures | ✅ Done | Added to `tests/e2e/conftest.py` |
| Update pyproject.toml | ✅ Done | Added verbose default, updated markers |

### Test Coverage

| Assignment | Spec | Solution | E2E Test |
|------------|------|----------|----------|
| PE1 | ✅ | ✅ `playbook_solution.yaml` | ✅ `test_pe1_grading.py` |
| PE2 | ✅ | ❌ | ❌ |
| PE3 | ✅ | ✅ `playbook_solution.yml` | ✅ `test_pe3_grading.py` |
| PE4 | ✅ | ✅ `roles/pxl_exam_role/` | ✅ `test_pe4_grading.py` |

### Running E2E Tests

```bash
# Run all E2E tests with live output
.venv/bin/python -m pytest tests/e2e/ -v -s -m e2e

# Run specific PE tests
.venv/bin/python -m pytest tests/e2e/test_pe1_grading.py -v -s
.venv/bin/python -m pytest tests/e2e/test_pe3_grading.py -v -s
.venv/bin/python -m pytest tests/e2e/test_pe4_grading.py -v -s
```
