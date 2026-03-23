from guard.core_integrity import write_core_hash, validate_core_hash
from guard.token_drift import validate_token_drift
import pytest


def test_roundtrip_fidelity(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / 'core').mkdir()
    (tmp_path / 'core' / 'x.txt').write_text('data')
    write_core_hash()
    assert validate_core_hash()
    assert validate_token_drift(1000, 1000, threshold=0.01)


def test_pipeline_roundtrip_token_map():
    pytest.skip('Rust-level token-map roundtrip is covered by cnf-token-core unit tests.')

