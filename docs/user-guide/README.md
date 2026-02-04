# HAMMER User Guide

Welcome to the HAMMER (Hands-on Ansible Multi-node Machine Evaluation Runner) user guide. HAMMER is a system for deterministic assignment authoring, generation, and auto-grading for Ansible labs.

## Table of Contents

1. [Getting Started](getting-started.md) - Installation and your first HAMMER project.
2. [Creating Assignments](creating-specs.md) - How to write HAMMER specifications.
3. [CLI Reference](cli-reference.md) - Detailed guide to HAMMER commands.
4. [Example Walkthrough: PE1](examples/pe1-walkthrough.md) - A complete example of a web application assignment.

## Key Concepts

- **Spec File**: A YAML file defining the topology, variables, and behavioral contracts for an assignment.
- **Student Bundle**: A generated package for students containing a Vagrantfile and inventory.
- **Grading Bundle**: A generated package for instructors containing tests and overlays.
- **Phases**: HAMMER grades in three phases:
    - **Baseline**: Initial run with student variables.
    - **Mutation**: Second run with modified variables (testing precedence and flexibility).
    - **Idempotence**: Third run to ensure the playbook doesn't make unnecessary changes.
