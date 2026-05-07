"""Unit tests for preflight check functions (no external calls in unit tests)."""
from unittest.mock import Mock, patch

import pytest

import scripts.preflight as p


def test_check_not_already_git_repo_passes_when_no_git_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(p, "PROJECT_ROOT", tmp_path)
    # Mock subprocess.run to simulate no parent git repo
    mock_run = Mock(return_value=Mock(returncode=128))
    monkeypatch.setattr("subprocess.run", mock_run)
    ok, msg = p.check_not_already_git_repo()
    assert ok
    assert "OK" in msg


def test_check_not_already_git_repo_fails_when_git_dir_exists(tmp_path, monkeypatch):
    (tmp_path / ".git").mkdir()
    monkeypatch.setattr(p, "PROJECT_ROOT", tmp_path)
    ok, msg = p.check_not_already_git_repo()
    assert not ok
    assert "FAIL" in msg


def test_main_returns_1_on_any_failure():
    with patch.object(p, "CHECKS", [("dummy", lambda: (False, "FAIL: x"))]):
        assert p.main() == 1


def test_main_returns_0_when_all_pass():
    with patch.object(p, "CHECKS", [("dummy", lambda: (True, "OK"))]):
        assert p.main() == 0
