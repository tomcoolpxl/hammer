# Ansible Debug Output Verification Plan

## Use Case

Assignments may require students to:
1. Use `debug` module to print specific messages
2. Display registered variable values
3. Prove conditional logic executed by printing messages

Example student task:
```yaml
- name: Show configuration status
  debug:
    msg: "Server configured with port {{ http_port }}"
```

## Proposed Solution: OutputContract

Add a new contract type to verify Ansible output contains expected patterns.

### Schema

```yaml
behavioral_contracts:
  output_checks:
    - pattern: "Server configured with port 8080"
      match_type: contains  # or 'regex'
      phase: baseline
      weight: 1.0

    - pattern: "Database connection: SUCCESS"
      match_type: contains
      required: true  # Fail if not found
      weight: 2.0

    - pattern: "Error:.*connection refused"
      match_type: regex
      expected: false  # Should NOT appear
      weight: 1.0
```

### Implementation

```python
# spec.py
class OutputContract(BaseModel):
    """Contract for verifying Ansible output contains expected patterns."""
    pattern: NonEmptyStr
    match_type: Literal["contains", "regex"] = "contains"
    expected: bool = True  # True = should match, False = should NOT match
    phases: Optional[List[ExecutionPhaseName]] = None
    weight: float = Field(default=1.0, ge=0.0)
```

### Test Generation

Since output checks happen after converge (not via testinfra), generate a special test file:

```python
# test_output.py.j2
"""Verify Ansible output patterns."""
import re
import pytest
from pathlib import Path

CONVERGE_LOG = Path(__file__).parent.parent.parent / "converge.log"

{% for check in checks %}
@pytest.mark.{{ phase }}
@pytest.mark.weight({{ check.weight }})
def test_output_{{ check.safe_name }}():
    """Verify output {{ 'contains' if check.expected else 'does NOT contain' }} '{{ check.pattern }}'."""
    log_content = CONVERGE_LOG.read_text()

    {% if check.match_type == 'regex' %}
    match = re.search(r"{{ check.pattern }}", log_content)
    {% else %}
    match = "{{ check.pattern }}" in log_content
    {% endif %}

    {% if check.expected %}
    assert match, f"Expected output to contain '{{ check.pattern }}'"
    {% else %}
    assert not match, f"Expected output to NOT contain '{{ check.pattern }}'"
    {% endif %}
{% endfor %}
```

### Runner Integration

The converge.log is already written by the runner. Output tests just read from it.

### Variable Interpolation

Support `{{ variable }}` in patterns that get resolved from phase variables:

```yaml
output_checks:
  - pattern: "Configured port: {{ http_port }}"
    match_type: contains
```

This would be resolved at build time to the actual expected value.

## Alternative: Post-Converge Assertions

Instead of a separate contract, add `output_assertions` to phase overlays:

```yaml
phase_overlays:
  baseline:
    output_assertions:
      - contains: "Setup complete"
      - regex: "Installed version: \\d+\\.\\d+"
      - not_contains: "FAILED"
```

## Priority

Medium-High - Useful for debugging assignments and conditional logic verification.

## Files to Modify

| File | Changes |
|------|---------|
| `spec.py` | Add `OutputContract`, add to `BehavioralContracts` |
| `plan.py` | Add `OutputCheck`, filtering, build |
| `testgen/behavioral.py` | Add `generate_output_tests()` |
| `testgen/templates/test_output.py.j2` | New template |
| `testgen/__init__.py` | Generate output tests |
