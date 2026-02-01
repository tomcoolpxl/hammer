# Phase 5 Implementation Plan: The "Grade" Command (Runner)

## Overview

Implement `hammer grade --spec SPEC.yml --student-repo DIR --out RESULTS_DIR` to execute the grading pipeline on a student submission.

## Grading Pipeline

```
1. Setup Phase
   └── Copy grading bundle to working directory
   └── Link/copy student playbook and roles

2. For each phase (baseline, mutation, idempotence):
   a. Converge
      └── Run ansible-playbook with phase overlays
      └── Capture play recap (changed, ok, failed counts)

   b. Snapshot
      └── Run snapshot extraction playbook
      └── Collect system state (ports, services, files)

   c. Verify
      └── Run pytest with phase-specific tests
      └── Collect test results (passed, failed, scores)

3. Results Aggregation
   └── Compute weighted scores
   └── Generate JSON report
   └── Generate human-readable summary
```

## Module Structure

```
src/hammer/
    runner/
        __init__.py         # Exports grade_assignment()
        ansible.py          # Ansible execution wrapper
        snapshot.py         # Snapshot playbook generation
        pytest_runner.py    # Pytest execution and result parsing
        results.py          # Result models and aggregation
        templates/
            snapshot_playbook.yml.j2
```

## Implementation Steps

### Step 1: Add ansible-runner Dependency
**File:** `pyproject.toml`
- Add `"ansible-runner>=2.3.0"` to dependencies

### Step 2: Result Models
**File:** `src/hammer/runner/results.py`

```python
class PhaseResult(BaseModel):
    phase: str
    converge: ConvergeResult
    tests: TestResult
    score: float

class ConvergeResult(BaseModel):
    ok: int
    changed: int
    failed: int
    unreachable: int
    skipped: int
    play_recap: Dict[str, Any]

class TestResult(BaseModel):
    passed: int
    failed: int
    skipped: int
    total_weight: float
    earned_weight: float
    details: List[TestCaseResult]

class GradeReport(BaseModel):
    assignment_id: str
    timestamp: str
    phases: Dict[str, PhaseResult]
    total_score: float
    max_score: float
    percentage: float
```

### Step 3: Ansible Execution Wrapper
**File:** `src/hammer/runner/ansible.py`

Functions:
- `run_playbook(playbook_path, inventory, extra_vars, ...)` → ConvergeResult
- `parse_play_recap(runner_result)` → Dict

Uses ansible-runner for:
- Programmatic execution
- Capturing stdout/stderr
- Parsing play recap

### Step 4: Snapshot Playbook Generator
**File:** `src/hammer/runner/snapshot.py`
**File:** `src/hammer/runner/templates/snapshot_playbook.yml.j2`

Generates playbook to collect:
- Listening ports (`ss -tlnp`)
- Service states (`systemctl show`)
- File stats (`stat`)
- Firewall rules (`firewall-cmd --list-all`)

### Step 5: Pytest Runner
**File:** `src/hammer/runner/pytest_runner.py`

Functions:
- `run_phase_tests(tests_dir, phase, ...)` → TestResult
- `parse_pytest_json(result_file)` → List[TestCaseResult]

Uses pytest with:
- `--json-report` for structured output
- `-m <phase>` marker filtering
- Timeout handling

### Step 6: Main Grade Orchestrator
**File:** `src/hammer/runner/__init__.py`

```python
def grade_assignment(
    spec: HammerSpec,
    student_repo: Path,
    output_dir: Path,
    skip_vm_setup: bool = False,
) -> GradeReport:
    """
    Execute the full grading pipeline.

    1. Prepare working directory
    2. Start VMs (if not skipped)
    3. For each phase:
       - Apply overlays
       - Run converge
       - Run verification tests
    4. Aggregate results
    5. Generate report
    """
```

### Step 7: CLI Integration
**File:** `src/hammer/cli.py`

Add `grade` subcommand:
```python
grade_parser = subparsers.add_parser("grade", help="Grade a student submission")
grade_parser.add_argument("--spec", type=Path, required=True)
grade_parser.add_argument("--student-repo", type=Path, required=True)
grade_parser.add_argument("--out", type=Path, required=True)
grade_parser.add_argument("--skip-vm-setup", action="store_true")
grade_parser.add_argument("--phase", type=str, choices=["baseline", "mutation", "idempotence"])
```

### Step 8: Unit Tests
**File:** `tests/unit/test_runner.py`

Test cases:
- `test_converge_result_parsing`
- `test_test_result_aggregation`
- `test_score_calculation`
- `test_snapshot_playbook_generation`

## Output Structure

```
results/
  report.json           # Full structured report
  summary.txt           # Human-readable summary
  phases/
    baseline/
      converge.log      # Ansible output
      play_recap.json   # Parsed recap
      pytest_report.json
    mutation/
      ...
    idempotence/
      ...
```

## Key Design Decisions

1. **ansible-runner**: Provides clean Python API for Ansible execution
2. **pytest-json-report**: Structured test output for parsing
3. **Phase isolation**: Each phase runs with its own overlay variables
4. **Idempotence check**: Re-run mutation playbook, expect changed=0
5. **Weighted scoring**: Tests contribute proportionally to final score

## Files to Create/Modify

| File | Action |
|------|--------|
| `pyproject.toml` | Modify - add ansible-runner, pytest-json-report |
| `src/hammer/runner/__init__.py` | Create |
| `src/hammer/runner/ansible.py` | Create |
| `src/hammer/runner/snapshot.py` | Create |
| `src/hammer/runner/pytest_runner.py` | Create |
| `src/hammer/runner/results.py` | Create |
| `src/hammer/runner/templates/snapshot_playbook.yml.j2` | Create |
| `src/hammer/cli.py` | Modify - add grade command |
| `tests/unit/test_runner.py` | Create |

## Verification

After implementation:
1. Create a simple reference playbook that configures nginx
2. Run `hammer grade --spec tests/fixtures/valid_full.yaml --student-repo /path/to/playbook --out /tmp/results`
3. Verify report.json contains phase results
4. Verify scores are correctly calculated
