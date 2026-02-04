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
def pe3_dir():
    """Return path to PE3 example."""
    return REAL_EXAMPLES_DIR / "PE3"


@pytest.fixture(scope="session")
def pe4_dir():
    """Return path to PE4 example."""
    return REAL_EXAMPLES_DIR / "PE4"


@pytest.fixture(scope="session")
def e2e_work_dir():
    """Create a temporary directory for E2E tests."""
    tmpdir = tempfile.mkdtemp(prefix="hammer_e2e_")
    path = Path(tmpdir)

    print(f"\n{'='*60}")
    print(f"[E2E] Created work directory: {path}")
    print(f"{'='*60}")

    yield path

    # Cleanup: make sure VMs are destroyed before removing dir
    # This is a safety net in case fixtures didn't clean up
    print(f"\n[E2E] Cleaning up work directory: {path}")
    if path.exists():
        try:
            shutil.rmtree(path)
        except OSError:
            pass
    print(f"[E2E] Cleanup complete!")


@pytest.fixture(scope="session")
def pe1_build(e2e_work_dir, pe1_dir, hammer_bin):
    """Build PE1 assignment."""
    output_dir = e2e_work_dir / "PE1_build"
    spec_path = pe1_dir / "spec.yaml"

    print(f"\n{'='*60}")
    print(f"[PE1] Building assignment from {spec_path}")
    print(f"[PE1] Output directory: {output_dir}")
    print(f"{'='*60}")

    # Use split() if hammer_bin contains spaces (e.g. "python -m ...")
    if " " in hammer_bin:
        cmd = hammer_bin.split() + ["build", "--spec", str(spec_path), "--out", str(output_dir)]
    else:
        cmd = [hammer_bin, "build", "--spec", str(spec_path), "--out", str(output_dir)]

    subprocess.run(cmd, check=True, capture_output=True)

    print(f"[PE1] Build complete!")
    return output_dir


@pytest.fixture(scope="session")
def pe1_vms(pe1_build):
    """Bring up VMs for PE1 and ensure they are destroyed afterwards."""
    grading_dir = pe1_build / "grading_bundle"

    # Check if vagrant is available
    if shutil.which("vagrant") is None:
        pytest.skip("vagrant not found")

    print(f"\n{'='*60}")
    print(f"[PE1] Starting Vagrant VMs...")
    print(f"[PE1] Working directory: {grading_dir}")
    print(f"[PE1] This may take several minutes...")
    print(f"{'='*60}")

    # Bring up VMs
    # Use -f to avoid interaction, although vagrant up is usually non-interactive
    try:
        subprocess.run(
            ["vagrant", "up"],
            cwd=str(grading_dir),
            check=True,
            capture_output=True,
            timeout=600  # 10 minute timeout
        )
        print(f"[PE1] VMs are ready!")
        yield grading_dir
    except subprocess.CalledProcessError as e:
        print(f"[PE1] Vagrant up failed: {e.stderr.decode()}")
        # Still try to destroy in case some VMs started
        subprocess.run(["vagrant", "destroy", "-f"], cwd=str(grading_dir), capture_output=True)
        pytest.fail(f"Vagrant up failed: {e.stderr.decode()}")
    finally:
        print(f"\n[PE1] Destroying VMs...")
        subprocess.run(["vagrant", "destroy", "-f"], cwd=str(grading_dir), capture_output=True)
        print(f"[PE1] Cleanup complete!")


@pytest.fixture(scope="session")
def pe3_build(e2e_work_dir, pe3_dir, hammer_bin):
    """Build PE3 assignment."""
    output_dir = e2e_work_dir / "PE3_build"
    spec_path = pe3_dir / "spec.yaml"

    print(f"\n{'='*60}")
    print(f"[PE3] Building assignment from {spec_path}")
    print(f"[PE3] Output directory: {output_dir}")
    print(f"{'='*60}")

    # Use split() if hammer_bin contains spaces (e.g. "python -m ...")
    if " " in hammer_bin:
        cmd = hammer_bin.split() + ["build", "--spec", str(spec_path), "--out", str(output_dir)]
    else:
        cmd = [hammer_bin, "build", "--spec", str(spec_path), "--out", str(output_dir)]

    subprocess.run(cmd, check=True, capture_output=True)

    print(f"[PE3] Build complete!")
    return output_dir


@pytest.fixture(scope="session")
def pe3_vms(pe3_build):
    """Bring up VMs for PE3 and ensure they are destroyed afterwards."""
    grading_dir = pe3_build / "grading_bundle"

    # Check if vagrant is available
    if shutil.which("vagrant") is None:
        pytest.skip("vagrant not found")

    print(f"\n{'='*60}")
    print(f"[PE3] Starting Vagrant VMs...")
    print(f"[PE3] Working directory: {grading_dir}")
    print(f"[PE3] This may take several minutes...")
    print(f"{'='*60}")

    # Bring up VMs
    try:
        subprocess.run(
            ["vagrant", "up"],
            cwd=str(grading_dir),
            check=True,
            capture_output=True,
            timeout=600  # 10 minute timeout
        )
        print(f"[PE3] VMs are ready!")
        yield grading_dir
    except subprocess.CalledProcessError as e:
        print(f"[PE3] Vagrant up failed: {e.stderr.decode()}")
        # Still try to destroy in case some VMs started
        subprocess.run(["vagrant", "destroy", "-f"], cwd=str(grading_dir), capture_output=True)
        pytest.fail(f"Vagrant up failed: {e.stderr.decode()}")
    finally:
        print(f"\n[PE3] Destroying VMs...")
        subprocess.run(["vagrant", "destroy", "-f"], cwd=str(grading_dir), capture_output=True)
        print(f"[PE3] Cleanup complete!")


@pytest.fixture(scope="session")
def pe4_build(e2e_work_dir, pe4_dir, hammer_bin):
    """Build PE4 assignment."""
    output_dir = e2e_work_dir / "PE4_build"
    spec_path = pe4_dir / "spec.yaml"

    print(f"\n{'='*60}")
    print(f"[PE4] Building assignment from {spec_path}")
    print(f"[PE4] Output directory: {output_dir}")
    print(f"{'='*60}")

    # Use split() if hammer_bin contains spaces (e.g. "python -m ...")
    if " " in hammer_bin:
        cmd = hammer_bin.split() + ["build", "--spec", str(spec_path), "--out", str(output_dir)]
    else:
        cmd = [hammer_bin, "build", "--spec", str(spec_path), "--out", str(output_dir)]

    subprocess.run(cmd, check=True, capture_output=True)

    print(f"[PE4] Build complete!")
    return output_dir


@pytest.fixture(scope="session")
def pe4_vms(pe4_build):
    """Bring up VMs for PE4 and ensure they are destroyed afterwards."""
    grading_dir = pe4_build / "grading_bundle"

    # Check if vagrant is available
    if shutil.which("vagrant") is None:
        pytest.skip("vagrant not found")

    print(f"\n{'='*60}")
    print(f"[PE4] Starting Vagrant VMs...")
    print(f"[PE4] Working directory: {grading_dir}")
    print(f"[PE4] This may take several minutes...")
    print(f"{'='*60}")

    # Bring up VMs
    try:
        subprocess.run(
            ["vagrant", "up"],
            cwd=str(grading_dir),
            check=True,
            capture_output=True,
            timeout=600  # 10 minute timeout
        )
        print(f"[PE4] VMs are ready!")
        yield grading_dir
    except subprocess.CalledProcessError as e:
        print(f"[PE4] Vagrant up failed: {e.stderr.decode()}")
        # Still try to destroy in case some VMs started
        subprocess.run(["vagrant", "destroy", "-f"], cwd=str(grading_dir), capture_output=True)
        pytest.fail(f"Vagrant up failed: {e.stderr.decode()}")
    finally:
        print(f"\n[PE4] Destroying VMs...")
        subprocess.run(["vagrant", "destroy", "-f"], cwd=str(grading_dir), capture_output=True)
        print(f"[PE4] Cleanup complete!")
