# Phase 1 Detailed Plan: Skeleton & Spec Loader

**Objective:** Initialize the Python project and implement the strict Pydantic schema validation for HAMMER assignment specs.

## 1. Project Initialization
*   [ ] **Directory Structure:**
    ```text
    hammer/
    ├── src/
    │   └── hammer/
    │       ├── __init__.py
    │       └── spec.py       <-- The core models
    ├── tests/
    │   ├── unit/
    │   │   └── test_spec.py
    │   └── fixtures/
    │       ├── valid_full.yaml
    │       └── invalid_logic.yaml
    ├── pyproject.toml        <-- Dependencies (pydantic, pyyaml)
    └── .gitignore
    ```
*   [ ] **Dependencies:**
    *   Runtime: `pydantic>=2.0`, `pyyaml`
    *   Dev: `pytest`, `ruff`, `mypy`

## 2. Implementation: `src/hammer/spec.py`
*   [ ] **Translation:** Port the code from `docs/design/01_spec_models.md` into this file.
*   [ ] **Refinement:** Ensure all imports are correct and `pydantic` v2 syntax (`field_validator`, `model_validator`) is used accurately.
*   [ ] **Loader Helper:** Add a helper function `load_spec_from_file(path: Path) -> HammerSpec` to handle YAML reading and Pydantic parsing.

## 3. Implementation: Test Fixtures
*   [ ] **`valid_full.yaml`**: Copy the "Reference example assignment spec" from `SPEC_SCHEMA.md`.
*   [ ] **`invalid_logic.yaml`**: Create a spec that passes structural JSON validation but fails Pydantic semantic validation (e.g., duplicate node names, or variables with bindings but no mutation overlay).

## 4. Verification: Unit Tests
*   [ ] **`test_spec_loading`**: Load `valid_full.yaml`, assert specific fields match (e.g., `spec.assignment_id == "hammer-nginx-port"`).
*   [ ] **`test_semantic_validation`**: Load `invalid_logic.yaml`, assert `pydantic.ValidationError` is raised with a message about the specific logic error.
*   [ ] **`test_feature_flags`**: Test that defining `handler_contracts` without `features.handlers=true` raises an error.

## 5. Verification: Linting & Types
*   [ ] Run `ruff check .`
*   [ ] Run `mypy src`
