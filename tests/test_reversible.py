import pytest
from guard.core_integrity import compute_core_hash, write_core_hash, validate_core_hash


def test_reversible_hashing(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / 'core').mkdir()
    (tmp_path / 'core/file.txt').write_text('abc')
    write_core_hash()
    assert validate_core_hash()

    # reverse to original by re-writing same contents, should continue to pass
    (tmp_path / 'core/file.txt').write_text('abc')
    assert validate_core_hash()
