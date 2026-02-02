# HAMMER

**H**ands-on **A**nsible **M**ulti-node **M**achine **E**valuation **R**unner

HAMMER is an automated grading system for Ansible assignments. It validates student playbooks against a specification, testing them across multiple phases with variable mutations to ensure robust, idempotent infrastructure code.

## Features

- **Spec-driven grading**: Define assignments using a declarative YAML specification
- **Multi-phase testing**: Baseline, mutation, and idempotence phases
- **Variable contract verification**: Test that playbooks correctly handle variable changes
- **Behavioral contracts**: Verify packages, services, files, firewall rules, and network reachability
- **Deterministic builds**: Same spec + seed produces identical test environments
- **Detailed reporting**: JSON and human-readable grade reports

## Requirements

- Python 3.10+
- Vagrant with libvirt provider
- Ansible 2.15+

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/yourusername/hammer.git
cd hammer
```

### 2. Create and activate a virtual environment

```bash
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# or
.venv\Scripts\activate     # Windows
```

### 3. Install HAMMER

```bash
pip install -e ".[dev]"
```

### 4. Install Ansible collections (if not already installed)

```bash
ansible-galaxy collection install ansible.posix
```

## Usage

HAMMER provides three main commands: `validate`, `build`, and `grade`.

### Validate a Specification

Check that a spec file is valid:

```bash
hammer validate --spec path/to/spec.yaml
```

### Build Assignment Bundles

Generate student and grading bundles from a specification:

```bash
hammer build --spec path/to/spec.yaml --out /path/to/output
```

This creates:
- `student_bundle/` - Vagrantfile and inventory for students
- `grading_bundle/` - Complete grading environment with tests
- `lock.json` - Reproducibility artifact with checksums

Options:
- `--box-version` - Vagrant box to use (default: `generic/alma9`)

### Grade a Student Submission

#### Step 1: Start the VMs

First, bring up the grading environment:

```bash
cd /path/to/output/grading_bundle
vagrant up
```

#### Step 2: Run the grader

```bash
hammer grade \
    --spec path/to/spec.yaml \
    --student-repo path/to/student/submission \
    --out /path/to/results \
    --grading-bundle /path/to/output/grading_bundle \
    --verbose
```

Options:
- `--phase` - Run specific phase(s): `baseline`, `mutation`, `idempotence` (can be repeated)
- `--skip-build` - Use existing grading bundle without regenerating
- `--verbose`, `-v` - Enable verbose output

#### Step 3: Review results

Results are written to the output directory:
- `results/report.json` - Full JSON report
- `results/summary.txt` - Human-readable summary
- `results/<phase>/converge.log` - Ansible output for each phase
- `results/<phase>/test.log` - Test output for each phase

### Example Workflow

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# Validate the spec
hammer validate --spec examples/nginx-port/spec.yaml

# Build the bundles
hammer build --spec examples/nginx-port/spec.yaml --out /tmp/nginx-assignment

# Start VMs
cd /tmp/nginx-assignment/grading_bundle
vagrant up

# Grade a student submission
cd /path/to/hammer
hammer grade \
    --spec examples/nginx-port/spec.yaml \
    --student-repo /path/to/student/repo \
    --out /tmp/grade-results \
    --grading-bundle /tmp/nginx-assignment/grading_bundle \
    --verbose

# View results
cat /tmp/grade-results/results/summary.txt

# Clean up VMs when done
cd /tmp/nginx-assignment/grading_bundle
vagrant destroy -f
```

## Specification Format

A HAMMER spec defines:

- **Topology**: Nodes, groups, and resources
- **Variable contracts**: Variables with allowed values and binding targets
- **Behavioral contracts**: Expected packages, services, files, and firewall rules
- **Phase overlays**: Different variable values for each grading phase

Example spec structure:

```yaml
assignment_id: "nginx-port-assignment"
spec_version: "1.0"
seed: 1337
provider: "libvirt"
os: "almalinux9"

topology:
  nodes:
    - name: "web1"
      groups: ["web"]
      resources:
        cpu: 2
        ram_mb: 2048

variable_contracts:
  - name: "http_port"
    type: "int"
    defaults:
      student: 8080
    allowed_values: [8080, 9090]
    grading_overlay_targets:
      - overlay_kind: "group_vars"
        target_name: "web"
    binding_targets:
      - type: "service_listen_port"
        target:
          service: "nginx"
          protocol: "tcp"

behavioral_contracts:
  packages:
    - name: "nginx"
      state: "present"
      node_selector:
        group: "web"
  services:
    - name: "nginx"
      enabled: true
      running: true
      node_selector:
        group: "web"

phase_overlays:
  baseline:
    group_vars:
      web:
        http_port: 8080
  mutation:
    group_vars:
      web:
        http_port: 9090
```

See `tests/fixtures/valid_full.yaml` for a complete example.

## Project Structure

```
hammer/
├── src/hammer/
│   ├── spec.py          # Pydantic models for spec validation
│   ├── plan.py          # Execution plan builder
│   ├── cli.py           # CLI entry points
│   ├── builder/         # Bundle generation
│   │   ├── network.py   # Deterministic IP assignment
│   │   ├── vagrantfile.py
│   │   ├── inventory.py
│   │   └── templates/   # Jinja2 templates
│   ├── testgen/         # Test file generation
│   │   ├── bindings.py
│   │   ├── behavioral.py
│   │   └── templates/   # Test templates
│   └── runner/          # Grading execution
│       ├── ansible.py   # Playbook runner
│       ├── pytest_runner.py
│       └── results.py   # Result models
├── tests/
│   ├── unit/            # Unit tests
│   └── fixtures/        # Test specs and playbooks
└── docs/
    └── planning/        # Design documents
```

## Development

### Running Tests

```bash
# Activate virtual environment
source .venv/bin/activate

# Run unit tests
pytest tests/unit/ -v

# Run with coverage
pytest tests/unit/ --cov=hammer --cov-report=term-missing
```

### Code Quality

```bash
# Linting
ruff check src/

# Type checking
mypy src/hammer/
```

## Grading Phases

HAMMER runs three grading phases:

1. **Baseline**: Tests the playbook with default/student values
2. **Mutation**: Changes variable values to test playbook flexibility
3. **Idempotence**: Re-runs the mutation phase to verify no changes occur

Each phase:
1. Applies phase-specific variable overlays
2. Runs the student's playbook (converge)
3. Executes generated pytest-testinfra tests (verify)
4. Records pass/fail results with weights

## License

MIT License
