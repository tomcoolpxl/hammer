"""HAMMER Test Generation Module.

Generates pytest/testinfra test files from execution plans.
"""

from pathlib import Path
from typing import Any, Dict, List

from jinja2 import Environment, FileSystemLoader

from hammer.spec import HammerSpec
from hammer.plan import ExecutionPlan, ExecutionPhaseName
from hammer.builder.network import NetworkPlan
from hammer.testgen.bindings import generate_binding_tests
from hammer.testgen.behavioral import (
    generate_package_tests,
    generate_pip_package_tests,
    generate_service_tests,
    generate_user_tests,
    generate_file_tests,
    generate_firewall_tests,
    generate_http_endpoint_tests,
)
from hammer.testgen.reachability import generate_reachability_tests


__all__ = ["generate_tests"]


TEMPLATES_DIR = Path(__file__).parent / "templates"


def _get_env() -> Environment:
    """Get Jinja2 environment with templates."""
    return Environment(
        loader=FileSystemLoader(TEMPLATES_DIR),
        keep_trailing_newline=True,
    )


def _get_resolved_vars(plan: ExecutionPlan, phase: ExecutionPhaseName) -> Dict[str, Any]:
    """Get resolved variable values for a phase."""
    phase_vars = plan.variables[phase]
    return {
        name: rv.value
        for name, rv in phase_vars.resolved.items()
    }


def generate_tests(
    spec: HammerSpec,
    plan: ExecutionPlan,
    network: NetworkPlan,
    output_dir: Path,
) -> List[Path]:
    """
    Generate pytest test files for all phases.

    Creates test files in output_dir/tests/ with phase subdirectories.

    Args:
        spec: The HAMMER spec
        plan: The execution plan with contracts
        network: The resolved network plan
        output_dir: Root directory for output (e.g., grading_bundle/)

    Returns:
        List of generated test file paths
    """
    env = _get_env()
    generated_files: List[Path] = []

    tests_dir = output_dir / "tests"
    tests_dir.mkdir(parents=True, exist_ok=True)

    # Generate conftest.py (shared across phases)
    conftest_content = _render_conftest(env, spec, network)
    conftest_path = tests_dir / "conftest.py"
    conftest_path.write_text(conftest_content)
    generated_files.append(conftest_path)

    # Generate phase-specific tests
    for phase in ["baseline", "mutation", "idempotence"]:
        phase_dir = tests_dir / phase
        phase_dir.mkdir(exist_ok=True)

        # Create __init__.py for the phase package
        init_path = phase_dir / "__init__.py"
        init_path.write_text(f'"""HAMMER tests for {phase} phase."""\n')
        generated_files.append(init_path)

        phase_files = _generate_phase_tests(
            env, spec, plan, network, phase, phase_dir
        )
        generated_files.extend(phase_files)

    return generated_files


def _render_conftest(
    env: Environment,
    spec: HammerSpec,
    network: NetworkPlan,
) -> str:
    """Render the conftest.py file."""
    template = env.get_template("conftest.py.j2")
    return template.render(
        assignment_id=spec.assignment_id,
        phase="all",
        nodes=spec.topology.nodes,
        network=network,
    )


def _generate_phase_tests(
    env: Environment,
    spec: HammerSpec,
    plan: ExecutionPlan,
    network: NetworkPlan,
    phase: str,
    phase_dir: Path,
) -> List[Path]:
    """Generate all test files for a specific phase."""
    generated_files: List[Path] = []
    contract = plan.contracts[phase]
    resolved_vars = _get_resolved_vars(plan, phase)

    # Binding tests
    binding_tests = generate_binding_tests(spec, contract, phase)
    if binding_tests:
        content = env.get_template("test_bindings.py.j2").render(
            assignment_id=spec.assignment_id,
            phase=phase,
            tests=binding_tests,
        )
        path = phase_dir / "test_bindings.py"
        path.write_text(content)
        generated_files.append(path)

    # Package tests
    package_tests = generate_package_tests(contract)
    if package_tests:
        content = env.get_template("test_packages.py.j2").render(
            assignment_id=spec.assignment_id,
            phase=phase,
            tests=package_tests,
        )
        path = phase_dir / "test_packages.py"
        path.write_text(content)
        generated_files.append(path)

    # Pip package tests
    pip_package_tests = generate_pip_package_tests(contract)
    if pip_package_tests:
        content = env.get_template("test_pip_packages.py.j2").render(
            assignment_id=spec.assignment_id,
            phase=phase,
            tests=pip_package_tests,
        )
        path = phase_dir / "test_pip_packages.py"
        path.write_text(content)
        generated_files.append(path)

    # Service tests
    service_tests = generate_service_tests(contract)
    if service_tests:
        content = env.get_template("test_services.py.j2").render(
            assignment_id=spec.assignment_id,
            phase=phase,
            tests=service_tests,
        )
        path = phase_dir / "test_services.py"
        path.write_text(content)
        generated_files.append(path)

    # User tests
    user_tests = generate_user_tests(contract)
    if user_tests:
        content = env.get_template("test_users.py.j2").render(
            assignment_id=spec.assignment_id,
            phase=phase,
            tests=user_tests,
        )
        path = phase_dir / "test_users.py"
        path.write_text(content)
        generated_files.append(path)

    # File tests
    file_tests = generate_file_tests(contract)
    if file_tests:
        content = env.get_template("test_files.py.j2").render(
            assignment_id=spec.assignment_id,
            phase=phase,
            tests=file_tests,
        )
        path = phase_dir / "test_files.py"
        path.write_text(content)
        generated_files.append(path)

    # Firewall tests
    firewall_tests = generate_firewall_tests(contract, resolved_vars)
    if firewall_tests:
        content = env.get_template("test_firewall.py.j2").render(
            assignment_id=spec.assignment_id,
            phase=phase,
            tests=firewall_tests,
        )
        path = phase_dir / "test_firewall.py"
        path.write_text(content)
        generated_files.append(path)

    # Reachability tests
    reachability_tests = generate_reachability_tests(contract, resolved_vars)
    if reachability_tests:
        content = env.get_template("test_reachability.py.j2").render(
            assignment_id=spec.assignment_id,
            phase=phase,
            tests=reachability_tests,
        )
        path = phase_dir / "test_reachability.py"
        path.write_text(content)
        generated_files.append(path)

    # HTTP endpoint tests
    http_endpoint_tests = generate_http_endpoint_tests(contract)
    if http_endpoint_tests:
        content = env.get_template("test_http.py.j2").render(
            assignment_id=spec.assignment_id,
            phase=phase,
            tests=http_endpoint_tests,
        )
        path = phase_dir / "test_http.py"
        path.write_text(content)
        generated_files.append(path)

    return generated_files
