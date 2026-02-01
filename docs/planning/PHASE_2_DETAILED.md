# Phase 2 Detailed Plan: Normalization & Execution Plan

**Objective:** Implement the "Planner" logic that transforms the parsed Spec into a deterministic, phase-resolved Execution Plan. This plan is what the runner and builder will eventually consume.

## 1. Implementation: `src/hammer/plan.py`
*   [ ] **Translation:** Port the code from `docs/design/02_normalization_logic.md` into `src/hammer/plan.py`.
*   [ ] **Refinement:**
    *   Add Pydantic models for the Plan outputs (`PhaseVariablePlan`, `ExecutionPlan`, etc.) instead of just dataclasses if we want easier serialization/validation, or stick to dataclasses if we prefer simplicity. *Decision: Use Pydantic models for consistency and serialization support.*
    *   Ensure type safety and correct imports from `hammer.spec`.
*   [ ] **Core Functions:**
    *   `build_phase_variable_plan(...)`: Resolves overlays.
    *   `build_phase_contract_plan(...)`: Generates concrete checks.
    *   `build_execution_plan(...)`: Top-level orchestrator.

## 2. Implementation: Test Fixtures
*   [ ] Use existing `tests/fixtures/valid_full.yaml`.
*   [ ] Create a new `tests/fixtures/complex_precedence.yaml` (optional, if valid_full isn't enough) to test tricky variable overrides. *Note: valid_full already has a mutation phase with extra_vars overriding group_vars, which is a good start.*

## 3. Verification: Unit Tests (`tests/unit/test_plan.py`)
*   [ ] **`test_variable_resolution`**: Verify that for `valid_full.yaml`:
    *   Baseline: `http_port` is 8080 (from student default/group var).
    *   Mutation: `http_port` is 9090 (from extra_vars).
*   [ ] **`test_binding_normalization`**: Verify that `http_port` bindings are generated with the resolved values (8080 in baseline, 9090 in mutation).
*   [ ] **`test_handler_planning`**: Verify that the nginx restart handler expectation is:
    *   Baseline: `at_least_once`
    *   Mutation: `exactly_once`
    *   Idempotence: `zero`
*   [ ] **`test_node_selector_resolution`**: Verify `web` group selector resolves to `['web1']`.

## 4. Verification: CLI Integration (Optional but recommended)
*   [ ] Add `hammer plan --spec ...` command to dump the generated plan as JSON. This is incredibly useful for debugging.
