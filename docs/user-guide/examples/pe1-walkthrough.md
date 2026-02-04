# Example Walkthrough: PE1 (Pyramid App)

This walkthrough covers the PE1 assignment, which involves deploying a Python Pyramid web application.

## The Scenario

Students must:
1. Deploy a Python app to `/opt/pyramid_app/app.py`.
2. Install system packages (`python3`, `pip`).
3. Install Python packages (`pyramid`, `waitress`, etc.).
4. Configure a systemd service to keep the app running.
5. Open port 6000 in the `iptables` firewall.
6. Create a dedicated `app_user`.

## The Specification

The spec for this assignment (`real_examples/PE1/spec.yaml`) defines:

- **Topology**: One node named `server0`.
- **Variable Contracts**:
    - `app_port`: Defaults to 6000, mutated to 6001.
    - `app_dir`: Defaults to `/opt/pyramid_app`.
- **Behavioral Contracts**:
    - `packages`: `python3`, `python3-pip`, `iptables-services`.
    - `pip_packages`: `pyramid`, `waitress`.
    - `services`: `iptables`, `app`.
    - `users`: `app_user`.
    - `files`: Verification of `app.py` ownership and permissions.
    - `http_endpoints`: Verification that `http://localhost:6000/hostname` returns the correct data.

## Step 1: Building the Assignment

```bash
hammer build --spec real_examples/PE1/spec.yaml --out ./pe1_assignment
```

This creates:
- `pe1_assignment/student_bundle`: Give this to students.
- `pe1_assignment/grading_bundle`: Keep this for grading.

## Step 2: Student Work

Students create a `playbook.yml` in their bundle and run:
```bash
ansible-playbook playbook.yml
```

## Step 3: Grading

To grade the submission:
```bash
hammer grade 
  --spec real_examples/PE1/spec.yaml 
  --student-repo ./student_submission 
  --out ./grading_results 
  --verbose
```

HAMMER will:
1. Bring up a clean VM.
2. **Phase 1 (Baseline)**: Apply student variables, run playbook, verify state.
3. **Phase 2 (Mutation)**: Change variables (e.g., change port to 6001), run playbook, verify state.
4. **Phase 3 (Idempotence)**: Run playbook again, ensure 0 changes.
5. Generate a report in `./grading_results/results/report.json`.
