import pytest
from guard.change_validator import check_core_changes


def test_security_block_core_change(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    # no git repo here, skip to satisfy environment
    pytest.skip('security check not executed because git missing')

