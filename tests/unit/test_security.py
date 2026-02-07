"""Security tests for HAMMER input validation."""

from pathlib import Path

import pytest
from pydantic import ValidationError

from hammer.validators import (
    _check_identifier,
    _check_domain,
    _check_safe_path,
    _check_relative_path,
    _check_safe_pattern,
    _check_safe_url,
    _check_safe_zone,
)
from hammer.utils import validate_path_within


class TestSafeIdentifier:
    """Tests for SafeIdentifier validation."""

    def test_valid_identifiers(self):
        assert _check_identifier("webserver") == "webserver"
        assert _check_identifier("node1") == "node1"
        assert _check_identifier("my-node") == "my-node"
        assert _check_identifier("my_node") == "my_node"

    def test_rejects_empty(self):
        with pytest.raises(ValueError):
            _check_identifier("")

    def test_rejects_injection_semicolon(self):
        with pytest.raises(ValueError):
            _check_identifier('; import os #')

    def test_rejects_injection_command_sub(self):
        with pytest.raises(ValueError):
            _check_identifier("$(whoami)")

    def test_rejects_injection_backtick(self):
        with pytest.raises(ValueError):
            _check_identifier("`rm -rf /`")

    def test_rejects_starting_with_digit(self):
        with pytest.raises(ValueError):
            _check_identifier("1node")

    def test_rejects_spaces(self):
        with pytest.raises(ValueError):
            _check_identifier("my node")

    def test_rejects_too_long(self):
        with pytest.raises(ValueError):
            _check_identifier("a" * 65)


class TestSafePath:
    """Tests for SafePath validation."""

    def test_valid_absolute_path(self):
        assert _check_safe_path("/etc/nginx/nginx.conf") == "/etc/nginx/nginx.conf"

    def test_valid_relative_path(self):
        assert _check_safe_path("config/file.txt") == "config/file.txt"

    def test_rejects_traversal(self):
        with pytest.raises(ValueError, match="traversal"):
            _check_safe_path("../../../etc/passwd")

    def test_rejects_traversal_middle(self):
        with pytest.raises(ValueError, match="traversal"):
            _check_safe_path("/opt/../../../etc/shadow")

    def test_rejects_semicolon(self):
        with pytest.raises(ValueError, match="Unsafe"):
            _check_safe_path("/etc/file; rm -rf /")

    def test_rejects_pipe(self):
        with pytest.raises(ValueError, match="Unsafe"):
            _check_safe_path("/etc/file | cat /etc/passwd")

    def test_rejects_backtick(self):
        with pytest.raises(ValueError, match="Unsafe"):
            _check_safe_path("/etc/`whoami`/file")


class TestSafeRelativePath:
    """Tests for SafeRelativePath validation."""

    def test_valid_relative(self):
        assert _check_relative_path("playbook.yml") == "playbook.yml"

    def test_rejects_absolute(self):
        with pytest.raises(ValueError, match="absolute"):
            _check_relative_path("/etc/passwd")

    def test_rejects_traversal(self):
        with pytest.raises(ValueError, match="traversal"):
            _check_relative_path("../../etc/passwd")


class TestSafePattern:
    """Tests for SafePattern validation."""

    def test_valid_pattern(self):
        assert _check_safe_pattern("listen.*80") == "listen.*80"

    def test_rejects_null_byte(self):
        with pytest.raises(ValueError, match="Null"):
            _check_safe_pattern("test\x00pattern")


class TestSafeUrl:
    """Tests for SafeUrl validation."""

    def test_valid_http(self):
        assert _check_safe_url("http://localhost:8080/") == "http://localhost:8080/"

    def test_valid_https(self):
        assert _check_safe_url("https://example.com") == "https://example.com"

    def test_rejects_non_http(self):
        with pytest.raises(ValueError):
            _check_safe_url("ftp://example.com")

    def test_rejects_javascript(self):
        with pytest.raises(ValueError):
            _check_safe_url("javascript:alert(1)")


class TestSafeZone:
    """Tests for SafeZone validation."""

    def test_valid_zone(self):
        assert _check_safe_zone("public") == "public"

    def test_rejects_injection(self):
        with pytest.raises(ValueError):
            _check_safe_zone("; rm -rf /")


class TestValidatePathWithin:
    """Tests for path traversal protection."""

    def test_valid_path(self, tmp_path):
        child = tmp_path / "subdir" / "file.txt"
        child.parent.mkdir(parents=True, exist_ok=True)
        child.touch()
        result = validate_path_within(Path("subdir/file.txt"), tmp_path)
        assert result == child

    def test_rejects_traversal(self, tmp_path):
        with pytest.raises(ValueError, match="traversal"):
            validate_path_within(Path("../../etc/passwd"), tmp_path)

    def test_rejects_symlink_escape(self, tmp_path):
        """Symlinks that escape the base directory are caught."""
        link = tmp_path / "escape"
        link.symlink_to("/etc/passwd")
        with pytest.raises(ValueError, match="traversal"):
            validate_path_within(Path("escape"), tmp_path)


class TestSpecRejectsInjection:
    """Integration tests verifying spec-level validation catches injection."""

    def test_assignment_id_injection(self):
        from hammer.spec import HammerSpec
        with pytest.raises(ValidationError):
            HammerSpec.model_validate({
                "assignment_id": '"; import os; #',
                "assignment_version": "1.0",
                "spec_version": "1.0",
                "seed": 42,
                "provider": "libvirt",
                "os": "almalinux9",
                "topology": {"nodes": [{"name": "n1", "groups": ["all"],
                             "resources": {"cpu": 1, "ram_mb": 512}}]},
                "entrypoints": {"playbook_path": "playbook.yml"},
                "idempotence": {"required": True},
                "phase_overlays": {},
            })

    def test_node_name_injection(self):
        from hammer.spec import HammerSpec
        with pytest.raises(ValidationError):
            HammerSpec.model_validate({
                "assignment_id": "test",
                "assignment_version": "1.0",
                "spec_version": "1.0",
                "seed": 42,
                "provider": "libvirt",
                "os": "almalinux9",
                "topology": {"nodes": [{"name": "$(rm -rf /)",
                             "groups": ["all"],
                             "resources": {"cpu": 1, "ram_mb": 512}}]},
                "entrypoints": {"playbook_path": "playbook.yml"},
                "idempotence": {"required": True},
                "phase_overlays": {},
            })

    def test_playbook_path_traversal(self):
        from hammer.spec import HammerSpec
        with pytest.raises(ValidationError):
            HammerSpec.model_validate({
                "assignment_id": "test",
                "assignment_version": "1.0",
                "spec_version": "1.0",
                "seed": 42,
                "provider": "libvirt",
                "os": "almalinux9",
                "topology": {"nodes": [{"name": "n1", "groups": ["all"],
                             "resources": {"cpu": 1, "ram_mb": 512}}]},
                "entrypoints": {"playbook_path": "../../etc/passwd"},
                "idempotence": {"required": True},
                "phase_overlays": {},
            })
