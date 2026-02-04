import pytest
import subprocess
import shutil
import os
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).parents[2]
REAL_EXAMPLES_DIR = PROJECT_ROOT / "real_examples"


@pytest.fixture(scope="session")
def hammer_bin():
    """Return the path to the hammer executable."""
    # Try to find it in the venv
    venv_bin = PROJECT_ROOT / ".venv" / "bin" / "hammer"
    if venv_bin.exists():
        return str(venv_bin)
    
    # Fallback to 'hammer' in path
    if shutil.which("hammer"):
        return "hammer"
        
    # Last resort: python -m hammer.cli
    return f"{os.sys.executable} -m hammer.cli"


@pytest.fixture(scope="session")
def pe1_dir():
    """Return path to PE1 example."""
    return REAL_EXAMPLES_DIR / "PE1"


@pytest.fixture(scope="session")
def e2e_work_dir():
    """Create a temporary directory for E2E tests."""
    tmpdir = tempfile.mkdtemp(prefix="hammer_e2e_")
    path = Path(tmpdir)
    yield path
    
    # Cleanup: make sure VMs are destroyed before removing dir
    # This is a safety net in case fixtures didn't clean up
    if path.exists():
        try:
            shutil.rmtree(path)
        except OSError:
            pass


@pytest.fixture(scope="session")
def pe1_build(e2e_work_dir, pe1_dir, hammer_bin):
    """Build PE1 assignment."""
    output_dir = e2e_work_dir / "PE1_build"
    spec_path = pe1_dir / "spec.yaml"
    
    # Use split() if hammer_bin contains spaces (e.g. "python -m ...")
    if " " in hammer_bin:
        cmd = hammer_bin.split() + ["build", "--spec", str(spec_path), "--out", str(output_dir)]
    else:
        cmd = [hammer_bin, "build", "--spec", str(spec_path), "--out", str(output_dir)]
        
    subprocess.run(cmd, check=True, capture_output=True)
    
    return output_dir


@pytest.fixture(scope="session")
def pe1_vms(pe1_build):
    """Bring up VMs for PE1 and ensure they are destroyed afterwards."""
    grading_dir = pe1_build / "grading_bundle"
    
    # Check if vagrant is available
    if shutil.which("vagrant") is None:
        pytest.skip("vagrant not found")
        
    # Bring up VMs
    # Use -f to avoid interaction, although vagrant up is usually non-interactive
    try:
        print(f"
Bringing up VMs in {grading_dir}...")
        subprocess.run(
            ["vagrant", "up"], 
            cwd=str(grading_dir), 
            check=True, 
            capture_output=True,
            timeout=600  # 10 minute timeout
        )
        yield grading_dir
    except subprocess.CalledProcessError as e:
        print(f"Vagrant up failed: {e.stderr.decode()}")
        # Still try to destroy in case some VMs started
        subprocess.run(["vagrant", "destroy", "-f"], cwd=str(grading_dir), capture_output=True)
        pytest.fail(f"Vagrant up failed: {e.stderr.decode()}")
    finally:
        print(f"
Destroying VMs in {grading_dir}...")
        subprocess.run(["vagrant", "destroy", "-f"], cwd=str(grading_dir), capture_output=True)
