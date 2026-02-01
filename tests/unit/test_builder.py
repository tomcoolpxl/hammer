"""Unit tests for HAMMER builder module."""

import sys
import tempfile
from pathlib import Path

import pytest
import yaml

# Ensure src is in path
PROJECT_ROOT = Path(__file__).parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from hammer.spec import load_spec_from_file, HammerSpec
from hammer.plan import build_execution_plan
from hammer.builder import build_assignment
from hammer.builder.network import generate_network_plan, NetworkPlan
from hammer.builder.vagrantfile import render_vagrantfile
from hammer.builder.inventory import render_student_inventory
from hammer.builder.lock import compute_spec_hash, compute_file_checksum

FIXTURES_DIR = PROJECT_ROOT / "tests" / "fixtures"


@pytest.fixture
def full_spec() -> HammerSpec:
    return load_spec_from_file(FIXTURES_DIR / "valid_full.yaml")


class TestNetworkGeneration:
    """Tests for network plan generation."""

    def test_network_generation_deterministic(self, full_spec):
        """Same seed should produce same network plan."""
        network1 = generate_network_plan(full_spec)
        network2 = generate_network_plan(full_spec)

        assert network1.cidr == network2.cidr
        assert network1.gateway == network2.gateway
        assert network1.node_ip_map == network2.node_ip_map

    def test_network_generation_different_seeds(self):
        """Different seeds should produce different networks."""
        # Load spec and modify seed
        with open(FIXTURES_DIR / "valid_full.yaml", "r") as f:
            data = yaml.safe_load(f)

        data["seed"] = 1337
        spec1 = HammerSpec.model_validate(data)

        data["seed"] = 9999
        spec2 = HammerSpec.model_validate(data)

        network1 = generate_network_plan(spec1)
        network2 = generate_network_plan(spec2)

        # Different seeds should produce different subnet octets
        assert network1.cidr != network2.cidr

    def test_network_structure(self, full_spec):
        """Network plan should have correct structure."""
        network = generate_network_plan(full_spec)

        # Check CIDR format
        assert network.cidr.startswith("192.168.")
        assert network.cidr.endswith(".0/24")

        # Check gateway
        assert network.gateway.startswith("192.168.")
        assert network.gateway.endswith(".1")

        # Check netmask
        assert network.netmask == "255.255.255.0"

        # Check all nodes have IPs
        for node in full_spec.topology.nodes:
            assert node.name in network.node_ip_map
            ip = network.node_ip_map[node.name]
            assert ip.startswith("192.168.")

    def test_ip_assignment_order(self, full_spec):
        """IPs should be assigned starting from .10 in node order."""
        network = generate_network_plan(full_spec)

        # Extract subnet octet
        subnet = network.cidr.split(".")[2]

        # First node should get .10, second .11, etc.
        for idx, node in enumerate(full_spec.topology.nodes):
            expected_suffix = 10 + idx
            expected_ip = f"192.168.{subnet}.{expected_suffix}"
            assert network.node_ip_map[node.name] == expected_ip


class TestVagrantfileGeneration:
    """Tests for Vagrantfile generation."""

    def test_vagrantfile_contains_all_nodes(self, full_spec):
        """Vagrantfile should contain definitions for all nodes."""
        network = generate_network_plan(full_spec)
        content = render_vagrantfile(full_spec, network)

        for node in full_spec.topology.nodes:
            assert f'config.vm.define "{node.name}"' in content
            assert f'{node.name}.vm.hostname = "{node.name}"' in content

    def test_vagrantfile_contains_ips(self, full_spec):
        """Vagrantfile should contain assigned IP addresses."""
        network = generate_network_plan(full_spec)
        content = render_vagrantfile(full_spec, network)

        for node_name, ip in network.node_ip_map.items():
            assert ip in content

    def test_vagrantfile_contains_resources(self, full_spec):
        """Vagrantfile should contain node resource specs."""
        network = generate_network_plan(full_spec)
        content = render_vagrantfile(full_spec, network)

        for node in full_spec.topology.nodes:
            assert f"libvirt.memory = {node.resources.ram_mb}" in content
            assert f"libvirt.cpus = {node.resources.cpu}" in content

    def test_vagrantfile_uses_box_version(self, full_spec):
        """Vagrantfile should use specified box version."""
        network = generate_network_plan(full_spec)
        content = render_vagrantfile(full_spec, network, box_name="custom/box")

        assert 'config.vm.box = "custom/box"' in content


class TestInventoryGeneration:
    """Tests for inventory generation."""

    def test_student_inventory_yaml_valid(self, full_spec):
        """Student inventory should be valid YAML."""
        network = generate_network_plan(full_spec)
        content = render_student_inventory(full_spec, network)

        # Should parse without error
        parsed = yaml.safe_load(content)

        assert "all" in parsed
        assert "children" in parsed["all"]

    def test_student_inventory_contains_nodes(self, full_spec):
        """Student inventory should contain all nodes."""
        network = generate_network_plan(full_spec)
        content = render_student_inventory(full_spec, network)
        parsed = yaml.safe_load(content)

        # Collect all hosts from all groups
        all_hosts = set()
        for group_data in parsed["all"]["children"].values():
            if "hosts" in group_data:
                all_hosts.update(group_data["hosts"].keys())

        for node in full_spec.topology.nodes:
            assert node.name in all_hosts

    def test_student_inventory_has_connection_info(self, full_spec):
        """Student inventory should have SSH connection info."""
        network = generate_network_plan(full_spec)
        content = render_student_inventory(full_spec, network)
        parsed = yaml.safe_load(content)

        # Check first group's first host
        first_group = list(parsed["all"]["children"].values())[0]
        first_host = list(first_group["hosts"].values())[0]

        assert "ansible_host" in first_host
        assert "ansible_user" in first_host
        assert first_host["ansible_user"] == "vagrant"
        assert "ansible_ssh_private_key_file" in first_host


class TestGradingOverlays:
    """Tests for grading overlay generation."""

    def test_grading_overlays_match_plan(self, full_spec):
        """Grading overlays should match execution plan variables."""
        plan = build_execution_plan(full_spec)

        # Baseline should have http_port = 8080
        baseline_vars = plan.variables["baseline"]
        assert baseline_vars.resolved["http_port"].value == 8080

        # Mutation should have http_port = 9090 via extra_vars
        mutation_vars = plan.variables["mutation"]
        assert mutation_vars.resolved["http_port"].value == 9090
        assert mutation_vars.extra_vars.get("http_port") == 9090


class TestLockArtifact:
    """Tests for lock artifact generation."""

    def test_lock_checksum_reproducible(self, full_spec):
        """Same content should produce same checksum."""
        content = "test content"
        hash1 = compute_file_checksum(content)
        hash2 = compute_file_checksum(content)

        assert hash1 == hash2
        assert len(hash1) == 64  # SHA256 hex length

    def test_spec_hash_deterministic(self, full_spec):
        """Same spec should produce same hash."""
        hash1 = compute_spec_hash(full_spec)
        hash2 = compute_spec_hash(full_spec)

        assert hash1 == hash2

    def test_spec_hash_different_for_different_specs(self):
        """Different specs should produce different hashes."""
        with open(FIXTURES_DIR / "valid_full.yaml", "r") as f:
            data = yaml.safe_load(f)

        spec1 = HammerSpec.model_validate(data)

        data["seed"] = 9999
        spec2 = HammerSpec.model_validate(data)

        assert compute_spec_hash(spec1) != compute_spec_hash(spec2)


class TestFullBuild:
    """Integration tests for full build process."""

    def test_build_creates_all_artifacts(self, full_spec):
        """Build should create student_bundle, grading_bundle, and lock.json."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            lock = build_assignment(full_spec, output_dir)

            # Check directories exist
            assert (output_dir / "student_bundle").is_dir()
            assert (output_dir / "grading_bundle").is_dir()
            assert (output_dir / "lock.json").is_file()

            # Check student bundle contents
            student = output_dir / "student_bundle"
            assert (student / "Vagrantfile").is_file()
            assert (student / "inventory" / "hosts.yml").is_file()
            assert (student / "ansible.cfg").is_file()
            assert (student / "README.md").is_file()
            assert (student / "group_vars").is_dir()
            assert (student / "host_vars").is_dir()

            # Check grading bundle contents
            grading = output_dir / "grading_bundle"
            assert (grading / "Vagrantfile").is_file()
            assert (grading / "inventory" / "hosts.yml").is_file()
            assert (grading / "overlays" / "baseline").is_dir()
            assert (grading / "overlays" / "mutation").is_dir()

    def test_build_lock_contains_checksums(self, full_spec):
        """Lock artifact should contain file checksums."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            lock = build_assignment(full_spec, output_dir)

            assert "student_bundle/Vagrantfile" in lock.checksums
            assert "student_bundle/inventory/hosts.yml" in lock.checksums
            assert "grading_bundle/Vagrantfile" in lock.checksums

    def test_build_lock_contains_network(self, full_spec):
        """Lock artifact should contain resolved network."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            lock = build_assignment(full_spec, output_dir)

            assert lock.resolved_network.cidr.startswith("192.168.")
            assert len(lock.resolved_network.node_ip_map) == len(
                full_spec.topology.nodes
            )

    def test_build_with_custom_box(self, full_spec):
        """Build should use custom box version."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            lock = build_assignment(
                full_spec, output_dir, box_version="custom/alma9"
            )

            assert lock.pinned_versions.almalinux_box == "custom/alma9"

            # Check Vagrantfile uses custom box
            vagrantfile = (output_dir / "student_bundle" / "Vagrantfile").read_text()
            assert 'config.vm.box = "custom/alma9"' in vagrantfile
