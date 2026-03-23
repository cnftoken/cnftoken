import pytest
from policy.engine import enforce_all
from guard.core_integrity import write_core_hash, validate_core_hash
from guard.change_validator import check_core_changes


def test_pipeline_happy_path(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    # setup core folder to be consistent for validation
    (tmp_path / 'core').mkdir()
    (tmp_path / 'core' / 'marker.txt').write_text('immutable')
    write_core_hash()
    assert validate_core_hash()
    assert check_core_changes() is True
    assert enforce_all() is not None

