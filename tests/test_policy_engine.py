import pytest
from policy.engine import load_rules, enforce_all


def test_load_rules():
    rules = load_rules()
    assert rules.get('core_immutable') is True


def test_enforce_all():
    # At minimum should load rules and run policy checks without exception.
    assert enforce_all() is not None
