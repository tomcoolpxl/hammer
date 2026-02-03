"""Unit tests for HAMMER test generation module."""

import ast
import sys
import tempfile
from pathlib import Path

import pytest

# Ensure src is in path
PROJECT_ROOT = Path(__file__).parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from hammer.spec import load_spec_from_file, HammerSpec
from hammer.plan import build_execution_plan
from hammer.builder.network import generate_network_plan
from hammer.testgen import generate_tests
from hammer.testgen.bindings import generate_binding_tests
from hammer.testgen.behavioral import (
    generate_package_tests,
    generate_service_tests,
    generate_file_tests,
    generate_firewall_tests,
    generate_handler_tests,
)
from hammer.testgen.reachability import generate_reachability_tests

FIXTURES_DIR = PROJECT_ROOT / "tests" / "fixtures"


@pytest.fixture
def full_spec() -> HammerSpec:
    return load_spec_from_file(FIXTURES_DIR / "valid_full.yaml")


@pytest.fixture
def plan(full_spec):
    return build_execution_plan(full_spec)


@pytest.fixture
def network(full_spec):
    return generate_network_plan(full_spec)


class TestBindingTestGeneration:
    """Tests for binding test generation."""

    def test_binding_test_generation(self, full_spec, plan):
        """Binding tests should be generated for all binding targets."""
        contract = plan.contracts["baseline"]
        tests = generate_binding_tests(full_spec, contract, "baseline")

        # Should have tests for http_port and welcome_text bindings
        assert len(tests) > 0

        # Check that tests have required fields
        for test in tests:
            assert "test_name" in test
            assert "host" in test
            assert "binding_type" in test
            assert "expected_value" in test

    def test_binding_test_names_are_valid_identifiers(self, full_spec, plan):
        """Generated test names should be valid Python identifiers."""
        contract = plan.contracts["baseline"]
        tests = generate_binding_tests(full_spec, contract, "baseline")

        for test in tests:
            name = test["test_name"]
            assert name.isidentifier(), f"'{name}' is not a valid Python identifier"


class TestPackageTestGeneration:
    """Tests for package test generation."""

    def test_package_test_generation(self, plan):
        """Package tests should be generated from contracts."""
        contract = plan.contracts["baseline"]
        tests = generate_package_tests(contract)

        # Should have nginx package test
        assert len(tests) >= 1

        nginx_test = next((t for t in tests if t["name"] == "nginx"), None)
        assert nginx_test is not None
        assert nginx_test["state"] == "present"
        assert "web1" in nginx_test["hosts"]


class TestServiceTestGeneration:
    """Tests for service test generation."""

    def test_service_test_generation(self, plan):
        """Service tests should be generated from contracts."""
        contract = plan.contracts["baseline"]
        tests = generate_service_tests(contract)

        # Should have nginx service test
        assert len(tests) >= 1

        nginx_test = next((t for t in tests if t["name"] == "nginx"), None)
        assert nginx_test is not None
        assert nginx_test["running"] is True
        assert nginx_test["enabled"] is True


class TestFileTestGeneration:
    """Tests for file test generation."""

    def test_file_test_generation(self, plan):
        """File tests should be generated from contracts."""
        contract = plan.contracts["baseline"]
        tests = generate_file_tests(contract)

        assert len(tests) >= 1

        # Check that file items are present
        for test in tests:
            assert "file_items" in test
            assert len(test["file_items"]) > 0

            for item in test["file_items"]:
                assert "path" in item
                assert "present" in item
                assert "safe_name" in item


class TestFirewallTestGeneration:
    """Tests for firewall test generation."""

    def test_firewall_test_generation(self, plan):
        """Firewall tests should resolve variable references."""
        contract = plan.contracts["baseline"]
        resolved_vars = {"http_port": 8080}
        tests = generate_firewall_tests(contract, resolved_vars)

        assert len(tests) >= 1

        # Check port resolution
        for test in tests:
            for port in test["ports"]:
                # Variable references should be resolved
                assert isinstance(port["port"], int), \
                    f"Port should be resolved to int, got {type(port['port'])}"


class TestReachabilityTestGeneration:
    """Tests for reachability test generation."""

    def test_reachability_test_generation(self, plan):
        """Reachability tests should be generated."""
        contract = plan.contracts["baseline"]
        resolved_vars = {"http_port": 8080}
        tests = generate_reachability_tests(contract, resolved_vars)

        assert len(tests) >= 1

        test = tests[0]
        assert test["from_host"] == "app1"
        assert test["to_host"] == "web1"
        assert test["port"] == 8080
        assert test["expectation"] == "reachable"


class TestHandlerTestGeneration:
    """Tests for handler test generation."""

    def test_handler_test_generation(self, plan):
        """Handler tests should be generated from contracts."""
        contract = plan.contracts["baseline"]
        tests = generate_handler_tests(contract)

        # Should have handler test for "restart nginx"
        assert len(tests) >= 1

        nginx_handler = next(
            (t for t in tests if t["name"] == "restart nginx"), None
        )
        assert nginx_handler is not None
        assert nginx_handler["service"] == "nginx"
        assert nginx_handler["action"] == "restart"
        assert nginx_handler["expected_runs"] == "at_least_once"
        assert nginx_handler["weight"] == 2.0

    def test_handler_test_mutation_phase(self, plan):
        """Handler tests should have correct expectations per phase."""
        baseline = plan.contracts["baseline"]
        mutation = plan.contracts["mutation"]

        baseline_tests = generate_handler_tests(baseline)
        mutation_tests = generate_handler_tests(mutation)

        # Baseline expects at_least_once, mutation expects exactly_once
        baseline_handler = next(
            (t for t in baseline_tests if t["name"] == "restart nginx"), None
        )
        mutation_handler = next(
            (t for t in mutation_tests if t["name"] == "restart nginx"), None
        )

        assert baseline_handler["expected_runs"] == "at_least_once"
        assert mutation_handler["expected_runs"] == "exactly_once"

    def test_handler_test_idempotence_phase(self, plan):
        """Idempotence phase should expect zero handler runs."""
        idempotence = plan.contracts["idempotence"]
        tests = generate_handler_tests(idempotence)

        nginx_handler = next(
            (t for t in tests if t["name"] == "restart nginx"), None
        )
        assert nginx_handler["expected_runs"] == "zero"


class TestFullTestGeneration:
    """Integration tests for full test generation."""

    def test_generate_tests_creates_files(self, full_spec, plan, network):
        """Test generation should create all expected files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            files = generate_tests(full_spec, plan, network, output_dir)

            # Should create conftest.py
            assert (output_dir / "tests" / "conftest.py").exists()

            # Should create phase directories
            for phase in ["baseline", "mutation", "idempotence"]:
                phase_dir = output_dir / "tests" / phase
                assert phase_dir.is_dir()
                assert (phase_dir / "__init__.py").exists()

    def test_generated_tests_are_valid_python(self, full_spec, plan, network):
        """Generated test files should be valid Python syntax."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            files = generate_tests(full_spec, plan, network, output_dir)

            for path in files:
                if path.suffix == ".py":
                    content = path.read_text()
                    try:
                        ast.parse(content)
                    except SyntaxError as e:
                        pytest.fail(f"Invalid Python in {path}: {e}")

    def test_generated_tests_have_test_functions(self, full_spec, plan, network):
        """Generated test files should contain test functions."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            files = generate_tests(full_spec, plan, network, output_dir)

            # Check baseline test files
            baseline_dir = output_dir / "tests" / "baseline"

            for test_file in baseline_dir.glob("test_*.py"):
                content = test_file.read_text()
                tree = ast.parse(content)

                # Find test functions
                test_funcs = [
                    node.name for node in ast.walk(tree)
                    if isinstance(node, ast.FunctionDef)
                    and node.name.startswith("test_")
                ]

                assert len(test_funcs) > 0, \
                    f"No test functions found in {test_file.name}"

    def test_mutation_phase_uses_different_values(self, full_spec, plan, network):
        """Mutation phase tests should use different expected values."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            generate_tests(full_spec, plan, network, output_dir)

            # Check that baseline and mutation have different port values
            baseline_bindings = (
                output_dir / "tests" / "baseline" / "test_bindings.py"
            )
            mutation_bindings = (
                output_dir / "tests" / "mutation" / "test_bindings.py"
            )

            if baseline_bindings.exists() and mutation_bindings.exists():
                baseline_content = baseline_bindings.read_text()
                mutation_content = mutation_bindings.read_text()

                # Baseline should have 8080, mutation should have 9090
                assert "8080" in baseline_content
                assert "9090" in mutation_content
