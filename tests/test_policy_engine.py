"""Comprehensive tests for enhanced policy engine."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from policy.engine import (
    PolicyEngine,
    PolicyViolation,
    PolicyEnforcementResult,
    PolicyType,
    PolicySeverity,
    get_engine,
    enforce_all,
    load_rules,
)


def test_policy_engine_initialization():
    """Test PolicyEngine initialization."""
    print("\n=== Test: PolicyEngine Initialization ===")
    
    engine = get_engine()
    assert engine is not None, "Engine should not be None"
    assert engine.rules is not None, "Rules should be loaded"
    assert len(engine.rules) > 0, "Should have policies loaded"
    
    print("✓ Engine initialized successfully")
    print(f"✓ Loaded {len(engine.rules)} policies")
    print(f"✓ Rules path: {engine.rules_path}")


def test_singleton_pattern():
    """Test that engine uses singleton pattern."""
    print("\n=== Test: Singleton Pattern ===")
    
    engine1 = get_engine()
    engine2 = get_engine()
    
    assert engine1 is engine2, "Should return same instance"
    print("✓ Singleton pattern works correctly")


def test_config_validation():
    """Test policy configuration validation."""
    print("\n=== Test: Config Validation ===")
    
    engine = get_engine()
    is_valid, errors = engine.validate_config()
    
    assert isinstance(is_valid, bool), "Should return boolean"
    assert isinstance(errors, list), "Should return error list"
    
    if is_valid:
        print("✓ Configuration is valid")
        print("✓ All required policies present")
    else:
        print(f"✓ Found {len(errors)} validation errors:")
        for error in errors:
            print(f"  - {error}")


def test_get_rule():
    """Test getting individual rules."""
    print("\n=== Test: Get Rule ===")
    
    engine = get_engine()
    
    rule = engine.get_rule('core_immutable')
    assert rule is not None, "core_immutable rule should exist"
    assert rule is True, "core_immutable should be True"
    print(f"✓ core_immutable rule: {rule}")
    
    commit_rule = engine.get_rule('commit_control')
    assert commit_rule is not None, "commit_control rule should exist"
    assert isinstance(commit_rule, dict), "commit_control should be a dict"
    print(f"✓ commit_control rule keys: {list(commit_rule.keys())}")
    
    nonexistent = engine.get_rule('nonexistent_rule')
    assert nonexistent is None, "Nonexistent rule should return None"
    print("✓ Nonexistent rule returns None")


def test_policy_violation_creation():
    """Test PolicyViolation dataclass."""
    print("\n=== Test: PolicyViolation ===")
    
    violation = PolicyViolation(
        policy_id="test_policy",
        policy_name="Test Policy",
        severity=PolicySeverity.WARNING,
        message="Test violation message",
        details={"test_key": "test_value"},
    )
    
    assert violation.policy_id == "test_policy"
    assert violation.severity == PolicySeverity.WARNING
    assert violation.timestamp is not None
    assert violation.context == {}
    print("✓ PolicyViolation created successfully")
    print(f"✓ Timestamp: {violation.timestamp}")


def test_enforcement_result():
    """Test PolicyEnforcementResult dataclass."""
    print("\n=== Test: PolicyEnforcementResult ===")
    
    violations = [
        PolicyViolation(
            policy_id="test1",
            policy_name="Test 1",
            severity=PolicySeverity.ERROR,
            message="Error 1",
        ),
    ]
    
    result = PolicyEnforcementResult(
        success=False,
        policies_checked=5,
        policies_passed=4,
        policies_failed=1,
        violations=violations,
        enforcement_time_ms=123.45,
    )
    
    assert result.success is False
    assert result.policies_checked == 5
    assert result.policies_failed == 1
    assert len(result.violations) == 1
    assert result.enforcement_time_ms == 123.45
    print("✓ PolicyEnforcementResult created successfully")
    print(f"✓ Summary: {result.policies_passed}/{result.policies_checked} passed")


def test_backward_compatibility():
    """Test backward compatible API."""
    print("\n=== Test: Backward Compatibility ===")
    
    # Test load_rules function
    rules = load_rules()
    assert isinstance(rules, dict), "load_rules should return dict"
    assert 'core_immutable' in rules
    print("✓ load_rules() function works")
    
    # Test that old API still accessible
    from policy import enforce_all as old_enforce_all
    print("✓ Old enforce_all import still works")


def test_policy_types_enum():
    """Test PolicyType enum."""
    print("\n=== Test: PolicyType Enum ===")
    
    assert hasattr(PolicyType, 'CORE_PROTECTION')
    assert hasattr(PolicyType, 'CODE_QUALITY')
    assert hasattr(PolicyType, 'SECURITY')
    assert hasattr(PolicyType, 'GOVERNANCE')
    
    print("✓ PolicyType enum has all required values:")
    for ptype in PolicyType:
        print(f"  - {ptype.name} = {ptype.value}")


def test_policy_severity_enum():
    """Test PolicySeverity enum."""
    print("\n=== Test: PolicySeverity Enum ===")
    
    assert hasattr(PolicySeverity, 'INFO')
    assert hasattr(PolicySeverity, 'WARNING')
    assert hasattr(PolicySeverity, 'ERROR')
    assert hasattr(PolicySeverity, 'CRITICAL')
    
    print("✓ PolicySeverity enum has all required values:")
    for severity in PolicySeverity:
        print(f"  - {severity.name} = {severity.value}")


def test_violation_list_operations():
    """Test violation list operations."""
    print("\n=== Test: Violation List Operations ===")
    
    engine = PolicyEngine()
    initial_count = len(engine.violations)
    
    # Add violations
    v1 = PolicyViolation(
        policy_id="test1",
        policy_name="Test 1",
        severity=PolicySeverity.WARNING,
        message="Test 1",
    )
    v2 = PolicyViolation(
        policy_id="test2",
        policy_name="Test 2",
        severity=PolicySeverity.ERROR,
        message="Test 2",
    )
    
    engine.violations.extend([v1, v2])
    assert len(engine.violations) == initial_count + 2
    print(f"✓ Added 2 violations, total: {len(engine.violations)}")
    
    # Clear violations
    engine.violations.clear()
    assert len(engine.violations) == 0
    print("✓ Violations cleared")


def test_enforcement_history():
    """Test enforcement history tracking."""
    print("\n=== Test: Enforcement History ===")
    
    engine = PolicyEngine()
    initial_history = len(engine.enforcement_history)
    
    result = PolicyEnforcementResult(
        success=True,
        policies_checked=1,
        policies_passed=1,
        policies_failed=0,
    )
    
    engine.enforcement_history.append(result)
    assert len(engine.enforcement_history) == initial_history + 1
    print(f"✓ Added to enforcement history")
    print(f"✓ Total enforcement runs: {len(engine.enforcement_history)}")


def test_report_generation():
    """Test report generation."""
    print("\n=== Test: Report Generation ===")
    
    engine = get_engine()
    report = engine.get_report()
    
    assert isinstance(report, str), "Report should be string"
    assert len(report) > 0, "Report should not be empty"
    assert "POLICY ENGINE REPORT" in report, "Should have title"
    
    lines = report.split('\n')
    print(f"✓ Report generated with {len(lines)} lines")
    print(f"✓ Report preview:")
    for line in lines[:5]:
        print(f"  {line}")


def test_core_protection_features():
    """Test core protection features."""
    print("\n=== Test: Core Protection Features ===")
    
    engine = get_engine()
    
    # Test core_immutable is enabled
    core_immutable = engine.get_rule('core_immutable')
    assert core_immutable is True, "Core immutability should be enabled"
    print("✓ Core immutability policy is enabled")
    
    # Test core_paths configuration
    core_paths = engine.get_rule('core_paths')
    assert isinstance(core_paths, list), "core_paths should be a list"
    assert 'core' in core_paths, "core directory should be in core_paths"
    print(f"✓ Protected paths: {core_paths}")


def test_guard_system_integration():
    """Test guard system integration."""
    print("\n=== Test: Guard System Integration ===")
    
    engine = get_engine()
    guard_config = engine.get_rule('guard_system')
    
    assert guard_config is not None, "guard_system config should exist"
    assert 'required' in guard_config, "Should specify required guards"
    
    required_guards = guard_config.get('required', [])
    print(f"✓ Required guards ({len(required_guards)}):")
    for guard in required_guards[:5]:
        print(f"  - {guard}")


def test_commit_control_config():
    """Test commit control configuration."""
    print("\n=== Test: Commit Control Config ===")
    
    engine = get_engine()
    commit_config = engine.get_rule('commit_control')
    
    assert 'enforce_atomic' in commit_config
    assert 'allowed_types' in commit_config
    
    print(f"✓ Enforce atomic: {commit_config['enforce_atomic']}")
    print(f"✓ Allowed types: {commit_config['allowed_types']}")


def test_ci_configuration():
    """Test CI configuration."""
    print("\n=== Test: CI Configuration ===")
    
    engine = get_engine()
    ci_config = engine.get_rule('ci')
    
    assert isinstance(ci_config, dict), "CI config should be dict"
    print(f"✓ CI configuration keys: {list(ci_config.keys())}")
    
    for key, value in list(ci_config.items())[:5]:
        print(f"  - {key}: {value}")


def test_readme_law():
    """Test README policy."""
    print("\n=== Test: README Policy ===")
    
    engine = get_engine()
    readme_law = engine.get_rule('readme_law')
    
    assert readme_law is not None
    print(f"✓ README law policy: {readme_law}")


def run_all_tests():
    """Run all tests."""
    print("\n" + "="*60)
    print("POLICY ENGINE COMPREHENSIVE TEST SUITE")
    print("="*60)
    
    tests = [
        test_policy_engine_initialization,
        test_singleton_pattern,
        test_config_validation,
        test_get_rule,
        test_policy_violation_creation,
        test_enforcement_result,
        test_backward_compatibility,
        test_policy_types_enum,
        test_policy_severity_enum,
        test_violation_list_operations,
        test_enforcement_history,
        test_report_generation,
        test_core_protection_features,
        test_guard_system_integration,
        test_commit_control_config,
        test_ci_configuration,
        test_readme_law,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"✗ FAILED: {str(e)}")
            failed += 1
        except Exception as e:
            print(f"✗ ERROR: {str(e)}")
            failed += 1
    
    print("\n" + "="*60)
    print(f"TEST SUMMARY: {passed} passed, {failed} failed")
    print("="*60)
    
    return failed == 0


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)

