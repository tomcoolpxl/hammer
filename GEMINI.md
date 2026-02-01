# HAMMER Project Context

## Project Overview

**HAMMER** (Hands-on Ansible Multi-node Machine Evaluation Runner) is a system for deterministic assignment authoring, generation, and auto-grading for Ansible labs. It targets **Vagrant** + **libvirt/KVM** + **AlmaLinux 9** environments.

The core goal is to generate complete student bundles and grading bundles from a single declarative YAML specification, ensuring reproducibility and rigorous auto-grading via variable mutation and precedence checks.

## Key Documents & Structure

The project documentation is organized into the `docs/` directory:

*   **`REQUIREMENTS.md`**: The source of truth for scope, objectives, non-goals, and high-level architecture.
*   **`SPEC_SCHEMA.md`**: Contains the strict **JSON Schema (v1.0)** for the assignment specification file.
*   **`docs/design/01_spec_models.md`**: (Formerly `PYDANTIC_MODEL_SET.md`) Provides the **Pydantic v2** data models.
*   **`docs/design/02_normalization_logic.md`**: (Formerly `NORMALIZATION_MODEL_AND EXEC_PLAN_BUILDER.md`) Defines the "Phase Normalization" layer and Execution Plan.
*   **`docs/planning/IMPLEMENTATION_ROADMAP.md`**: The detailed, phased implementation plan.

## Architecture

The system follows a pipeline architecture:

1.  **Input:** A strict YAML assignment spec.
2.  **Validation:** `HammerSpec` (Pydantic) validates the input.
3.  **Normalization:** The spec is converted into an **Execution Plan** containing:
    *   **PhaseVariablePlan:** Resolved variables for 'baseline', 'mutation', and 'idempotence' phases.
    *   **PhaseContractPlan:** Concrete checks for bindings, services, files, etc.
4.  **Generation:**
    *   **Student Bundle:** Vagrantfile, inventory, scaffolding.
    *   **Grading Bundle:** Grading inventory, overlays, runner scripts.
    *   **Tests:** Pytest/Testinfra tests generated from the Contract Plan.
5.  **Execution (Runner):** A Python CLI (`hammer grade`) executes the plan, collecting artifacts and scores.

## Development Conventions

*   **Language:** Python 3.10+
*   **Validation:** Pydantic v2.x (Strict validation, fail-fast).
*   **Testing:** Pytest (for the runner/generator) and Testinfra (for the generated assignment tests).
*   **Style:** Code provided in markdown is "production-grade" and ready to be extracted into the codebase.
*   **Philosophy:**
    *   **Determinism:** All derived choices (IPs, mutation values) must be deterministic based on a seed.
    *   **Minimalism:** The v1 implementation should be a small, focused CLI.
    *   **Hard Edges:** Avoid flaky heuristic checks; prefer reachability and explicit system state.

## Next Steps (Implementation)

Please refer to **`docs/planning/IMPLEMENTATION_ROADMAP.md`** for the detailed step-by-step plan.

The immediate focus is **Phase 1: Skeleton, Spec Loader, and Validation**.
