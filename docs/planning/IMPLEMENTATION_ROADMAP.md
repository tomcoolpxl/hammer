# HAMMER Implementation Roadmap

This document outlines the phased implementation plan for the HAMMER project. The goal is to deliver a robust, strictly typed, and well-tested system incrementally.

## guiding Principles

1.  **Fail Fast:** Strict schema and type validation at the entry point.
2.  **Determinism:** All outputs must be reproducible from the spec + seed.
3.  **Test-Driven:** Core logic (normalization, planning) must be unit-tested before integration.
4.  **Separation of Concerns:** The "Planner" (generator) is distinct from the "Runner" (executor).

## Technical Stack & Structure

*   **Language:** Python 3.10+
*   **Dependency Management:** `poetry` (Recommended for strict locking) or `pip` with `requirements.txt`.
*   **Validation:** `pydantic` v2.x
*   **Testing:**
    *   `pytest`: Unit tests for python logic.
    *   `pytest-testinfra`: Generated system tests.
    *   `ansible-runner`: Programmatic Ansible execution.
*   **Project Layout:**
    ```text
    hammer/
    ├── docs/               # Documentation
    ├── src/
    │   └── hammer/         # Main package
    │       ├── __init__.py
    │       ├── spec.py     # Pydantic models (Design 01)
    │       ├── plan.py     # Normalization logic (Design 02)
    │       ├── cli.py      # CLI entry points
    │       ├── builder/    # "hammer build" logic (Vagrantfile/Inventory gen)
    │       └── runner/     # "hammer grade" logic
    ├── tests/
    │   ├── unit/           # Fast tests for spec.py and plan.py
    │   ├── integration/    # Slower tests running real builds
    │   └── fixtures/       # Sample specs for testing
    ├── pyproject.toml      # Config
    └── README.md
    ```

## Phase 1: Skeleton, Spec Loader, and Validation
**Goal:** Can load a YAML spec, validate it against strict Pydantic models, and error meaningfully on invalid input.

*   [x] Set up project structure (`src/`, `tests/`, `pyproject.toml`).
*   [x] Configure linting (Ruff) and typing (MyPy).
*   [x] Implement `hammer.spec` module using `docs/design/01_spec_models.md`.
*   [x] Create comprehensive unit tests for valid/invalid specs.
*   [x] Create a basic CLI that accepts `--spec` and prints "Valid". (Implicitly covered by tests, CLI entrypoint planned for later phases or can be added now).

## Phase 2: Normalization & Execution Plan Builder
**Goal:** Can convert a loaded spec into a deterministic "Execution Plan" (JSON-serializable).

*   [x] Implement `hammer.plan` module using `docs/design/02_normalization_logic.md`.
*   [x] Implement variable resolution logic (defaults < inventory < group < host < extra).
*   [x] Implement phase contract planning (bindings, handlers).
*   [x] Unit test the "Planner": Input Spec -> Output Plan JSON. Verify determinism.

## Phase 3: The "Build" Command (Artifact Generation)
**Goal:** Can generate the Student Bundle (Vagrantfile, Inventory) and Grading Bundle from the Execution Plan.

*   [x] Implement `hammer.builder` module.
*   [x] Create Jinja2 templates for `Vagrantfile` (libvirt).
*   [x] Create Jinja2 templates for Ansible Inventories (student & grading).
*   [x] Implement `hammer build` CLI command.
*   [x] **Manual Verification:** Can `vagrant up` the generated bundle locally.

## Phase 4: Test Generation Layer
**Goal:** Can generate `pytest` files that verify the contracts defined in the plan.

*   [x] Design the mapping from `PhaseContractPlan` to `test_*.py` content.
*   [x] Implement test generators for:
    *   Bindings (port, file content, etc.)
    *   Services/Packages
    *   Reachability
*   [x] Update `hammer build` to emit these tests into the bundles.

## Phase 5: The "Grade" Command (Runner)
**Goal:** Can execute the grading pipeline (Converge -> Snapshot -> Verify) on a local student repo.

*   [x] Implement `hammer.runner` module.
*   [x] Integrate `ansible-runner` to run playbooks programmatically.
*   [x] Implement snapshot extraction playbook generation.
*   [x] Implement `hammer grade` CLI command.
*   [x] **Integration Test:** Run a full grading cycle on the "Reference Example" spec.

## Phase 6: Refinement & Regression Suite
**Goal:** Robustness and edge-case handling.

*   [ ] Add regression tests for:
    *   Missing variables.
    *   Invalid binding targets.
    *   Handler failure cases.
*   [ ] Polish CLI output (rich logging).
*   [ ] Documentation updates.

---

**Next Immediate Action:** Proceed to Phase 6 refinement and regression testing.
