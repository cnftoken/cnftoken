import pytest
from guard.core_integrity import compute_core_hash, write_core_hash, validate_core_hash
from guard.token_drift import validate_token_drift


def test_core_hash_roundtrip(tmp_path, monkeypatch):
    # monkeypatch core directory for safe testing
    monkeypatch.chdir(tmp_path)
    d = tmp_path / 'core'
    d.mkdir()
    f = d / 'file.txt'
    f.write_text('x')
    write_core_hash()
    assert validate_core_hash() is True


def test_token_drift_ok():
    assert validate_token_drift(100, 110, threshold=0.5)


def test_token_drift_fail():
    with pytest.raises(Exception):
        validate_token_drift(100, 200, threshold=0.5)
