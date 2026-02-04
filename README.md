# HAMMER

**H**ands-on **A**nsible **M**ulti-node **M**achine **E**valuation **R**unner

HAMMER is an automated grading system for Ansible assignments. It validates student playbooks against a specification, testing them across multiple phases with variable mutations to ensure robust, idempotent infrastructure code.

## Features

### Core Features
- **Spec-driven grading**: Define assignments using a declarative YAML specification
- **Multi-phase testing**: Baseline, mutation, and idempotence phases
- **Variable contract verification**: Test that playbooks correctly handle variable changes
- **Behavioral contracts**: Verify packages, services, files, firewall rules, users, groups, and HTTP endpoints
- **Deterministic builds**: Same spec + seed produces identical test environments
- **Detailed reporting**: JSON and human-readable grade reports

### Advanced Features
- **Phase-specific contracts**: Apply tests only in specific phases (baseline, mutation, idempotence)
- **Reboot testing**: Reboot nodes after converge to verify boot-time behavior
- **Pure behavioral testing**: Optional variable_contracts for assignments without variable mutation
- **External HTTP testing**: Verify HTTP endpoints from the host or cross-VM
- **Output verification**: Check Ansible debug messages and output patterns
- **Expected failures**: Allow specific task failures for error handling assignments

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

## Specification Format

A HAMMER spec defines the complete grading configuration.

### Minimal Example (Variable Testing)

```yaml
assignment_id: "nginx-port-assignment"
assignment_version: "2025.01"
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

entrypoints:
  playbook_path: "site.yml"

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

idempotence:
  required: true

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

### Advanced Example (Pure Behavioral with Reboot)

```yaml
assignment_id: "pe4-exam"
assignment_version: "2025.01"
spec_version: "1.0"
seed: 42
provider: "libvirt"
os: "almalinux9"

features:
  handlers: false

topology:
  domain: "example.local"
  nodes:
    - name: "server0"
      groups: ["servers"]
      resources:
        cpu: 1
        ram_mb: 1024
      forwarded_ports:
        - host_port: 8888
          guest_port: 80
          protocol: tcp

entrypoints:
  playbook_path: "playbook.yml"

# No variable_contracts - pure behavioral testing

behavioral_contracts:
  users:
    - name: "appuser"
      exists: true
      groups: ["wheel"]
      node_selector: { host: "server0" }

  services:
    # Only check after reboot
    - name: "myservice"
      enabled: true
      running: true
      node_selector: { host: "server0" }
      phases: [mutation, idempotence]

  files:
    # Always check
    - items:
        - path: "/opt/first_run.txt"
          present: true
      node_selector: { host: "server0" }

    # Baseline only - file should NOT exist yet
    - items:
        - path: "/opt/second_run.txt"
          present: false
      node_selector: { host: "server0" }
      phases: [baseline]

    # After 2nd run - file should exist
    - items:
        - path: "/opt/second_run.txt"
          present: true
      node_selector: { host: "server0" }
      phases: [mutation, idempotence]

  # Test from grading host via port forwarding
  external_http:
    - url: "http://localhost:8888/"
      from_host: true
      expected_status: 200
      response_contains: "Welcome"
      phases: [mutation]

  # Verify Ansible output patterns
  output_checks:
    - pattern: "Configuration complete"
      match_type: contains
      expected: true
    - pattern: "Error:.*critical"
      match_type: regex
      expected: false

idempotence:
  required: true

phase_overlays:
  baseline:
    group_vars: {}

  mutation:
    group_vars: {}
    reboot:
      enabled: true
      nodes: [server0]
      timeout: 120
      poll_interval: 5
    failure_policy:
      allow_failures: true
      max_failures: 1
      expected_patterns: ["Connection refused"]
```

## Behavioral Contracts Reference

### packages
Verify package installation state.

```yaml
packages:
  - name: "nginx"
    state: "present"  # or "absent"
    node_selector: { group: "web" }
    phases: [baseline, mutation]  # optional
    weight: 1.0
```

### pip_packages
Verify pip package installation.

```yaml
pip_packages:
  - name: "flask"
    state: "present"
    python: "/usr/bin/python3"  # optional
    node_selector: { host: "app1" }
```

### services
Verify service state.

```yaml
services:
  - name: "nginx"
    enabled: true
    running: true
    node_selector: { group: "web" }
    phases: [mutation, idempotence]  # e.g., only after reboot
```

### users
Verify user existence and properties.

```yaml
users:
  - name: "appuser"
    exists: true
    uid: 1001  # optional
    home: "/home/appuser"  # optional
    shell: "/bin/bash"  # optional
    groups: ["wheel", "developers"]  # supplementary groups
    node_selector: { host: "server0" }
```

### groups
Verify group existence.

```yaml
groups:
  - name: "developers"
    exists: true
    gid: 2001  # optional
    node_selector: { group: "all" }
```

### files
Verify file/directory state.

```yaml
files:
  - items:
      - path: "/etc/myapp/config.yml"
        present: true
        mode: "0644"
        owner: "root"
        group: "root"
        content_regex: "port: \\d+"
      - path: "/var/log/myapp"
        present: true
        is_directory: true
    node_selector: { host: "server0" }
```

### firewall
Verify firewall port rules.

```yaml
firewall:
  - open_ports:
      - port: 80
        protocol: "tcp"
        zone: "public"
      - port: { var: "http_port" }  # reference a variable
        protocol: "tcp"
        zone: "public"
    node_selector: { group: "web" }
    firewall_type: "firewalld"  # or "iptables"
```

### reachability
Verify network connectivity between nodes.

```yaml
reachability:
  - from_host: "client1"
    to_host: "server1"
    protocol: "tcp"
    port: 80
    expectation: "reachable"  # or "not_reachable"
```

### http_endpoints
Verify HTTP endpoints from within VMs.

```yaml
http_endpoints:
  - url: "http://localhost:8080/health"
    method: "GET"
    expected_status: 200
    response_contains: "healthy"
    response_regex: "status.*ok"  # optional
    timeout_seconds: 5
    node_selector: { host: "web1" }
```

### external_http
Verify HTTP from host machine or cross-VM.

```yaml
external_http:
  # From grading host (via port forwarding)
  - url: "http://localhost:8888/"
    from_host: true
    expected_status: 200

  # From another VM
  - url: "http://web1:80/"
    from_node: { host: "client1" }
    expected_status: 200
    response_contains: "Welcome"
```

### output_checks
Verify Ansible output patterns (debug messages, etc.).

```yaml
output_checks:
  - pattern: "Server configured successfully"
    match_type: "contains"  # or "regex"
    expected: true
    description: "Verify success message"

  - pattern: "FAILED"
    expected: false  # should NOT appear
```

## Phase Overlay Options

### reboot
Reboot nodes after converge, before running tests.

```yaml
phase_overlays:
  mutation:
    reboot:
      enabled: true
      nodes: [server0]  # or omit for all nodes
      timeout: 120  # seconds to wait for SSH
      poll_interval: 5  # seconds between checks
```

### failure_policy
Allow expected failures during converge.

```yaml
phase_overlays:
  baseline:
    failure_policy:
      allow_failures: true
      max_failures: 2  # optional limit
      expected_patterns:  # optional - only allow matching failures
        - "Connection refused"
        - "timeout"
```

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
│   │   ├── reachability.py
│   │   └── templates/   # Test templates
│   └── runner/          # Grading execution
│       ├── ansible.py   # Playbook runner
│       ├── reboot.py    # Node reboot handling
│       ├── pytest_runner.py
│       └── results.py   # Result models
├── tests/
│   ├── unit/            # Unit tests
│   ├── integration/     # Integration tests (no VMs)
│   ├── e2e/             # End-to-end tests (with VMs)
│   └── fixtures/        # Test specs and playbooks
├── real_examples/       # Real assignment examples
│   ├── PE1/             # Pyramid app (with solution)
│   ├── PE2/             # Multi-node deployment
│   ├── PE3/             # Nginx webserver (with solution)
│   └── PE4/             # Role-based exam (with solution)
└── docs/
    ├── user-guide/      # User documentation
    └── planning/        # Design documents
```

## Development

### Running Tests

```bash
# Activate virtual environment
source .venv/bin/activate

# Run unit tests
pytest tests/unit/ -v

# Run integration tests
pytest tests/integration/ -v

# Run E2E tests (requires Vagrant + libvirt)
# Use -s flag for real-time progress output
pytest tests/e2e/ -v -s -m e2e

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
3. Optionally reboots nodes (if configured)
4. Executes generated pytest-testinfra tests (verify)
5. Records pass/fail results with weights

## Real Examples

See the `real_examples/` directory for complete working examples:

- **PE1**: Python Pyramid web application with variable contracts and port mutation
- **PE2**: Multi-node deployment with database and web tiers
- **PE3**: Nginx webserver with variable contracts (solution: `playbook_solution.yml`)
- **PE4**: Role-based exam with users, services, conditional files, and reboot testing (solution: `roles/pxl_exam_role/`)

PE1, PE3, and PE4 include solution playbooks/roles for E2E testing.

## License

MIT License
