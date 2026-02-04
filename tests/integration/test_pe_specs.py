"""Integration tests for validating PE spec files."""

import pytest
from pathlib import Path

from hammer.spec import load_spec_from_file, HammerSpec


PROJECT_ROOT = Path(__file__).parents[2]
REAL_EXAMPLES_DIR = PROJECT_ROOT / "real_examples"


def get_pe_specs():
    """Discover all PE spec files."""
    specs = []
    for pe_dir in sorted(REAL_EXAMPLES_DIR.iterdir()):
        if pe_dir.is_dir() and pe_dir.name.startswith("PE"):
            spec_file = pe_dir / "spec.yaml"
            if spec_file.exists():
                specs.append((pe_dir.name, spec_file))
    return specs


@pytest.fixture(scope="module")
def pe_specs():
    """Load all PE specs."""
    return {name: load_spec_from_file(path) for name, path in get_pe_specs()}


class TestPESpecsValidation:
    """Test that all PE specs validate correctly."""

    @pytest.mark.parametrize("pe_name,spec_path", get_pe_specs())
    def test_spec_loads_without_error(self, pe_name, spec_path):
        """Each PE spec should load and validate without errors."""
        spec = load_spec_from_file(spec_path)
        assert isinstance(spec, HammerSpec)

    @pytest.mark.parametrize("pe_name,spec_path", get_pe_specs())
    def test_spec_has_required_fields(self, pe_name, spec_path):
        """Each spec should have all required top-level fields."""
        spec = load_spec_from_file(spec_path)

        assert spec.assignment_id, f"{pe_name}: missing assignment_id"
        assert spec.assignment_version, f"{pe_name}: missing assignment_version"
        assert spec.spec_version == "1.0", f"{pe_name}: invalid spec_version"
        assert spec.seed is not None, f"{pe_name}: missing seed"
        assert spec.provider == "libvirt", f"{pe_name}: provider must be libvirt"
        assert spec.os == "almalinux9", f"{pe_name}: os must be almalinux9"

    @pytest.mark.parametrize("pe_name,spec_path", get_pe_specs())
    def test_spec_has_valid_topology(self, pe_name, spec_path):
        """Each spec should have at least one node."""
        spec = load_spec_from_file(spec_path)

        assert len(spec.topology.nodes) >= 1, f"{pe_name}: no nodes defined"
        for node in spec.topology.nodes:
            assert node.name, f"{pe_name}: node missing name"
            assert len(node.groups) >= 1, f"{pe_name}: node {node.name} has no groups"
            assert node.resources.cpu >= 1, f"{pe_name}: invalid CPU count"
            assert node.resources.ram_mb >= 256, f"{pe_name}: invalid RAM"

    @pytest.mark.parametrize("pe_name,spec_path", get_pe_specs())
    def test_spec_has_valid_entrypoints(self, pe_name, spec_path):
        """Each spec should have valid entrypoints."""
        spec = load_spec_from_file(spec_path)

        assert spec.entrypoints.playbook_path, f"{pe_name}: missing playbook_path"
        assert spec.entrypoints.playbook_path.endswith(".yaml") or \
               spec.entrypoints.playbook_path.endswith(".yml"), \
               f"{pe_name}: playbook_path should be YAML file"

    @pytest.mark.parametrize("pe_name,spec_path", get_pe_specs())
    def test_spec_has_phase_overlays(self, pe_name, spec_path):
        """Each spec should have phase overlays defined."""
        spec = load_spec_from_file(spec_path)

        assert spec.phase_overlays is not None, f"{pe_name}: missing phase_overlays"
        # At minimum, baseline or no variable contracts
        if spec.variable_contracts:
            assert spec.phase_overlays.baseline is not None, \
                f"{pe_name}: variable_contracts require baseline overlay"

    @pytest.mark.parametrize("pe_name,spec_path", get_pe_specs())
    def test_spec_idempotence_defined(self, pe_name, spec_path):
        """Each spec should have idempotence policy defined."""
        spec = load_spec_from_file(spec_path)

        assert spec.idempotence is not None, f"{pe_name}: missing idempotence policy"
        assert isinstance(spec.idempotence.required, bool)

    def test_all_pe_specs_discovered(self):
        """Ensure we're testing all expected PE specs."""
        specs = get_pe_specs()
        pe_names = [name for name, _ in specs]

        # We expect PE1-PE4 to exist
        expected = ["PE1", "PE2", "PE3", "PE4"]
        for expected_pe in expected:
            assert expected_pe in pe_names, f"Missing expected spec: {expected_pe}"


class TestPESpecsConsistency:
    """Test consistency across PE specs."""

    def test_unique_assignment_ids(self, pe_specs):
        """Each PE should have a unique assignment_id."""
        ids = [spec.assignment_id for spec in pe_specs.values()]
        assert len(ids) == len(set(ids)), "Duplicate assignment_ids found"

    def test_consistent_provider(self, pe_specs):
        """All specs should use the same provider."""
        providers = {spec.provider for spec in pe_specs.values()}
        assert len(providers) == 1, "Inconsistent providers across specs"
        assert "libvirt" in providers

    def test_consistent_os(self, pe_specs):
        """All specs should use the same OS."""
        os_list = {spec.os for spec in pe_specs.values()}
        assert len(os_list) == 1, "Inconsistent OS across specs"
        assert "almalinux9" in os_list
