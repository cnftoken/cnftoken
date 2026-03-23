import pytest
from guard.dual_execution import validate_two_runs
from guard.core_integrity import compute_core_hash


def test_dual_execution_consistency(tmp_path, monkeypatch):
    # This test checks deterministic operation of compute_core_hash when no core dir exists.
    monkeypatch.chdir(tmp_path)
    assert validate_two_runs(compute_core_hash) is True
