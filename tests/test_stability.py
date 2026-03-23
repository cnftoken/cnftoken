import pytest
from guard.change_validator import check_core_changes


def test_stability_no_modification(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    # create empty repository state
    # since git commands won't run without repo, we use pytest skip for isolation
    pytest.skip('git not available in this environment for stable check')
