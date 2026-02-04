# HAMMER CLI Reference

## `hammer validate`

Validates a specification file against the HAMMER schema.

**Usage:**
```bash
hammer validate --spec <file.yaml>
```

---

## `hammer build`

Generates student and grading bundles from a specification.

**Usage:**
```bash
hammer build --spec <file.yaml> --out <output_dir>
```

**Options:**
- `--spec`: (Required) Path to the spec file.
- `--out`: (Required) Directory to create bundles in.
- `--box-version`: Vagrant box to use (default: `generic/alma9`).

---

## `hammer grade`

Executes the full grading pipeline for a student submission.

**Usage:**
```bash
hammer grade --spec <spec.yaml> --student-repo <repo_dir> --out <results_dir> [options]
```

**Options:**
- `--spec`: (Required) Path to the spec file.
- `--student-repo`: (Required) Path to the student's playbook/roles.
- `--out`: (Required) Directory to store results.
- `--grading-bundle`: Path to an existing grading bundle with already running VMs.
- `--skip-build`: Use the existing grading bundle in the output directory instead of regenerating it.
- `--phase`: Run only specific phase(s) (baseline, mutation, idempotence). Can be repeated.
- `--verbose, -v`: Enable verbose output (shows Ansible and Pytest output).
