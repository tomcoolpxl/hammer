# Getting Started with HAMMER

## Prerequisites

HAMMER requires the following tools on your local machine:

- **Python 3.10+**
- **Vagrant** (with libvirt provider)
- **libvirt/KVM**
- **Ansible**

## Installation

1. Clone the HAMMER repository:
   ```bash
   git clone https://github.com/tomcoolpxl/hammer.git
   cd hammer
   ```

2. Create a virtual environment and install dependencies:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -e .
   ```

3. Verify the installation:
   ```bash
   hammer --help
   ```

## Your First Project

1. **Create a Spec**: Look at `real_examples/PE1/spec.yaml` for a reference.
2. **Build the Assignment**:
   ```bash
   hammer build --spec my_spec.yaml --out ./my_assignment
   ```
3. **Explore Bundles**:
   - `my_assignment/student_bundle`: What you give to students.
   - `my_assignment/grading_bundle`: What you use for grading.
4. **Grade a Submission**:
   ```bash
   hammer grade --spec my_spec.yaml --student-repo /path/to/student/code --out ./results
   ```
