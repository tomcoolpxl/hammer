"""Integration tests for lock.json artifact structure and determinism."""

import json
import tempfile
import pytest
from pathlib import Path

from hammer.spec import load_spec_from_file
from hammer.builder import build_assignment, LockArtifact


PROJECT_ROOT = Path(__file__).parents[2]
REAL_EXAMPLES_DIR = PROJECT_ROOT / "real_examples"


@pytest.fixture
def pe1_lock():
    """Build PE1 and return the lock artifact."""
    spec_path = REAL_EXAMPLES_DIR / "PE1" / "spec.yaml"
    spec = load_spec_from_file(spec_path)

    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir)
        lock = build_assignment(
            spec=spec,
            output_dir=output_dir,
            spec_dir=spec_path.parent,
        )
        lock_path = output_dir / "lock.json"
        lock_content = lock_path.read_text()
        yield lock, json.loads(lock_content)


class TestLockArtifactStructure:
    """Test lock.json has correct structure."""

    def test_lock_has_spec_hash(self, pe1_lock):
        """Lock should contain spec_hash."""
        lock, lock_json = pe1_lock
        assert "spec_hash" in lock_json
        assert isinstance(lock_json["spec_hash"], str)
        assert len(lock_json["spec_hash"]) == 64  # SHA256 hex

    def test_lock_has_seed(self, pe1_lock):
        """Lock should contain seed from spec."""
        lock, lock_json = pe1_lock
        assert "seed" in lock_json
        assert isinstance(lock_json["seed"], int)

    def test_lock_has_resolved_network(self, pe1_lock):
        """Lock should contain resolved network plan."""
        lock, lock_json = pe1_lock
        assert "resolved_network" in lock_json

        network = lock_json["resolved_network"]
        assert "cidr" in network
        assert "node_ip_map" in network

    def test_lock_has_pinned_versions(self, pe1_lock):
        """Lock should contain pinned versions."""
        lock, lock_json = pe1_lock
        assert "pinned_versions" in lock_json

        versions = lock_json["pinned_versions"]
        assert "almalinux_box" in versions

    def test_lock_has_checksums(self, pe1_lock):
        """Lock should contain file checksums."""
        lock, lock_json = pe1_lock
        assert "checksums" in lock_json
        assert isinstance(lock_json["checksums"], dict)

        # Should have checksums for key files
        checksums = lock_json["checksums"]
        assert len(checksums) >= 1


class TestLockArtifactContent:
    """Test lock.json content validity."""

    def test_spec_hash_is_valid_hex(self, pe1_lock):
        """Spec hash should be valid hex string."""
        lock, lock_json = pe1_lock
        spec_hash = lock_json["spec_hash"]

        # Should be valid hex
        try:
            int(spec_hash, 16)
        except ValueError:
            pytest.fail("spec_hash is not valid hex")

    def test_network_cidr_is_valid(self, pe1_lock):
        """Network CIDR should be valid."""
        lock, lock_json = pe1_lock
        cidr = lock_json["resolved_network"]["cidr"]

        # Should be in CIDR notation
        assert "/" in cidr
        ip, prefix = cidr.split("/")
        assert 0 <= int(prefix) <= 32

        # IP should have 4 octets
        octets = ip.split(".")
        assert len(octets) == 4
        for octet in octets:
            assert 0 <= int(octet) <= 255

    def test_node_ips_match_topology(self, pe1_lock):
        """Node IPs should match nodes in topology."""
        lock, _ = pe1_lock
        node_ip_map = lock.resolved_network.node_ip_map

        # Should have at least one node
        assert len(node_ip_map) >= 1

    def test_checksums_are_valid_sha256(self, pe1_lock):
        """All checksums should be valid SHA256 hashes."""
        lock, lock_json = pe1_lock

        for filepath, checksum in lock_json["checksums"].items():
            assert isinstance(checksum, str)
            assert len(checksum) == 64, f"Invalid checksum length for {filepath}"

            try:
                int(checksum, 16)
            except ValueError:
                pytest.fail(f"Invalid hex checksum for {filepath}")


class TestLockDeterminism:
    """Test that same spec + seed produces identical lock."""

    def test_same_spec_produces_same_hash(self):
        """Building the same spec twice should produce identical spec_hash."""
        spec_path = REAL_EXAMPLES_DIR / "PE1" / "spec.yaml"
        spec = load_spec_from_file(spec_path)

        locks = []
        for _ in range(2):
            with tempfile.TemporaryDirectory() as tmpdir:
                output_dir = Path(tmpdir)
                lock = build_assignment(
                    spec=spec,
                    output_dir=output_dir,
                    spec_dir=spec_path.parent,
                )
                locks.append(lock)

        assert locks[0].spec_hash == locks[1].spec_hash

    def test_same_spec_produces_same_network(self):
        """Building the same spec twice should produce identical network."""
        spec_path = REAL_EXAMPLES_DIR / "PE1" / "spec.yaml"
        spec = load_spec_from_file(spec_path)

        networks = []
        for _ in range(2):
            with tempfile.TemporaryDirectory() as tmpdir:
                output_dir = Path(tmpdir)
                lock = build_assignment(
                    spec=spec,
                    output_dir=output_dir,
                    spec_dir=spec_path.parent,
                )
                networks.append(lock.resolved_network)

        assert networks[0].cidr == networks[1].cidr
        assert networks[0].node_ip_map == networks[1].node_ip_map

    def test_same_spec_produces_identical_checksums(self):
        """Building the same spec twice should produce identical file checksums."""
        spec_path = REAL_EXAMPLES_DIR / "PE1" / "spec.yaml"
        spec = load_spec_from_file(spec_path)

        checksums_list = []
        for _ in range(2):
            with tempfile.TemporaryDirectory() as tmpdir:
                output_dir = Path(tmpdir)
                lock = build_assignment(
                    spec=spec,
                    output_dir=output_dir,
                    spec_dir=spec_path.parent,
                )
                checksums_list.append(lock.checksums)

        assert checksums_list[0] == checksums_list[1]

    def test_different_seeds_produce_different_network(self):
        """Different seeds should produce different network assignments."""
        spec_path = REAL_EXAMPLES_DIR / "PE1" / "spec.yaml"

        # Load and modify spec with different seeds
        import yaml
        with open(spec_path) as f:
            data = yaml.safe_load(f)

        from hammer.spec import HammerSpec

        networks = []
        for seed in [42, 12345]:
            data["seed"] = seed
            spec = HammerSpec.model_validate(data)

            with tempfile.TemporaryDirectory() as tmpdir:
                output_dir = Path(tmpdir)
                lock = build_assignment(
                    spec=spec,
                    output_dir=output_dir,
                    spec_dir=spec_path.parent,
                )
                networks.append(lock.resolved_network.cidr)

        # Different seeds should produce different CIDRs
        assert networks[0] != networks[1]


class TestLockArtifactForAllPEs:
    """Test lock artifact generation for all PE specs."""

    @pytest.mark.parametrize("pe_name", ["PE1", "PE2", "PE3", "PE4"])
    def test_lock_generated(self, pe_name):
        """Each PE should generate a valid lock.json."""
        spec_path = REAL_EXAMPLES_DIR / pe_name / "spec.yaml"
        if not spec_path.exists():
            pytest.skip(f"{pe_name} spec not found")

        spec = load_spec_from_file(spec_path)

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            lock = build_assignment(
                spec=spec,
                output_dir=output_dir,
                spec_dir=spec_path.parent,
            )

            lock_path = output_dir / "lock.json"
            assert lock_path.exists()

            lock_json = json.loads(lock_path.read_text())
            assert "spec_hash" in lock_json
            assert "resolved_network" in lock_json
            assert "checksums" in lock_json

    @pytest.mark.parametrize("pe_name", ["PE1", "PE2", "PE3", "PE4"])
    def test_lock_matches_spec_seed(self, pe_name):
        """Lock seed should match spec seed."""
        spec_path = REAL_EXAMPLES_DIR / pe_name / "spec.yaml"
        if not spec_path.exists():
            pytest.skip(f"{pe_name} spec not found")

        spec = load_spec_from_file(spec_path)

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            lock = build_assignment(
                spec=spec,
                output_dir=output_dir,
                spec_dir=spec_path.parent,
            )

            assert lock.seed == spec.seed
