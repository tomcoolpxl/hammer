"""Unit tests for the reboot module."""

import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
import subprocess

import pytest

# Ensure src is in path
PROJECT_ROOT = Path(__file__).parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from hammer.runner.reboot import (
    reboot_nodes,
    _reboot_single_node,
    _check_ssh_available,
    _get_all_nodes_from_inventory,
    RebootResult,
)


class TestCheckSshAvailable:
    """Tests for _check_ssh_available function."""

    @patch("hammer.runner.reboot.subprocess.run")
    def test_ssh_available_returns_true(self, mock_run):
        """Test that successful ping returns True."""
        mock_run.return_value = MagicMock(returncode=0)

        result = _check_ssh_available(Path("/fake/inventory.yml"), "node1")

        assert result is True
        mock_run.assert_called_once()

    @patch("hammer.runner.reboot.subprocess.run")
    def test_ssh_unavailable_returns_false(self, mock_run):
        """Test that failed ping returns False."""
        mock_run.return_value = MagicMock(returncode=1)

        result = _check_ssh_available(Path("/fake/inventory.yml"), "node1")

        assert result is False

    @patch("hammer.runner.reboot.subprocess.run")
    def test_ssh_timeout_returns_false(self, mock_run):
        """Test that timeout returns False."""
        mock_run.side_effect = subprocess.TimeoutExpired(cmd="ansible", timeout=10)

        result = _check_ssh_available(Path("/fake/inventory.yml"), "node1")

        assert result is False


class TestGetAllNodesFromInventory:
    """Tests for _get_all_nodes_from_inventory function."""

    def test_parse_simple_inventory(self, tmp_path):
        """Test parsing a simple YAML inventory."""
        inventory_content = """
all:
  hosts:
    node1:
      ansible_host: 192.168.1.1
    node2:
      ansible_host: 192.168.1.2
"""
        inventory_file = tmp_path / "hosts.yml"
        inventory_file.write_text(inventory_content)

        nodes = _get_all_nodes_from_inventory(inventory_file)

        assert set(nodes) == {"node1", "node2"}

    def test_parse_inventory_with_groups(self, tmp_path):
        """Test parsing inventory with child groups."""
        inventory_content = """
all:
  children:
    webservers:
      hosts:
        web1:
          ansible_host: 192.168.1.1
        web2:
          ansible_host: 192.168.1.2
    dbservers:
      hosts:
        db1:
          ansible_host: 192.168.1.3
"""
        inventory_file = tmp_path / "hosts.yml"
        inventory_file.write_text(inventory_content)

        nodes = _get_all_nodes_from_inventory(inventory_file)

        assert set(nodes) == {"web1", "web2", "db1"}

    def test_invalid_inventory_returns_empty(self, tmp_path):
        """Test that invalid inventory returns empty list."""
        inventory_file = tmp_path / "hosts.yml"
        inventory_file.write_text("not: valid: yaml: content")

        nodes = _get_all_nodes_from_inventory(inventory_file)

        assert nodes == []

    def test_nonexistent_inventory_returns_empty(self):
        """Test that nonexistent file returns empty list."""
        nodes = _get_all_nodes_from_inventory(Path("/nonexistent/path.yml"))

        assert nodes == []


class TestRebootSingleNode:
    """Tests for _reboot_single_node function."""

    @patch("hammer.runner.reboot._check_ssh_available")
    @patch("hammer.runner.reboot.subprocess.run")
    @patch("hammer.runner.reboot.time.sleep")
    def test_successful_reboot(self, mock_sleep, mock_run, mock_ssh):
        """Test successful node reboot."""
        mock_run.return_value = MagicMock()
        # First call returns False (rebooting), second call returns True (back up)
        mock_ssh.side_effect = [False, True]

        result = _reboot_single_node(
            Path("/fake/inventory.yml"),
            "node1",
            timeout=120,
            poll_interval=5,
        )

        assert result.success is True
        assert result.error is None

    @patch("hammer.runner.reboot._check_ssh_available")
    @patch("hammer.runner.reboot.subprocess.run")
    @patch("hammer.runner.reboot.time.sleep")
    @patch("hammer.runner.reboot.time.time")
    def test_reboot_timeout(self, mock_time, mock_sleep, mock_run, mock_ssh):
        """Test node reboot timeout."""
        mock_run.return_value = MagicMock()
        mock_ssh.return_value = False  # Never comes back

        # Simulate time passing: 0, 5, 10, ..., 125 (past timeout)
        mock_time.side_effect = [0, 0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50,
                                  55, 60, 65, 70, 75, 80, 85, 90, 95, 100,
                                  105, 110, 115, 120, 125]

        result = _reboot_single_node(
            Path("/fake/inventory.yml"),
            "node1",
            timeout=120,
            poll_interval=5,
        )

        assert result.success is False
        assert "SSH did not become available" in result.error


class TestRebootNodes:
    """Tests for reboot_nodes function."""

    @patch("hammer.runner.reboot._reboot_single_node")
    @patch("hammer.runner.reboot._get_all_nodes_from_inventory")
    def test_reboot_specific_nodes(self, mock_get_nodes, mock_reboot):
        """Test rebooting specific nodes."""
        mock_reboot.return_value = RebootResult(success=True, duration=30.0)

        results = reboot_nodes(
            Path("/fake/inventory.yml"),
            nodes=["node1", "node2"],
            timeout=120,
            poll_interval=5,
        )

        assert len(results) == 2
        assert "node1" in results
        assert "node2" in results
        assert results["node1"].success is True
        mock_get_nodes.assert_not_called()

    @patch("hammer.runner.reboot._reboot_single_node")
    @patch("hammer.runner.reboot._get_all_nodes_from_inventory")
    def test_reboot_all_nodes(self, mock_get_nodes, mock_reboot):
        """Test rebooting all nodes when nodes=None."""
        mock_get_nodes.return_value = ["node1", "node2", "node3"]
        mock_reboot.return_value = RebootResult(success=True, duration=30.0)

        results = reboot_nodes(
            Path("/fake/inventory.yml"),
            nodes=None,  # All nodes
            timeout=120,
            poll_interval=5,
        )

        assert len(results) == 3
        mock_get_nodes.assert_called_once()


class TestRebootResult:
    """Tests for RebootResult dataclass."""

    def test_successful_result(self):
        """Test creating a successful reboot result."""
        result = RebootResult(success=True, duration=45.5)

        assert result.success is True
        assert result.duration == 45.5
        assert result.error is None

    def test_failed_result(self):
        """Test creating a failed reboot result."""
        result = RebootResult(
            success=False,
            duration=120.0,
            error="SSH timeout",
        )

        assert result.success is False
        assert result.duration == 120.0
        assert result.error == "SSH timeout"
