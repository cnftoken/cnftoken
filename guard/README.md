# Guard System - Enhanced Governance

**Strong and disciplined governance system with comprehensive validation, monitoring, and enforcement.**

## 🎯 What It Does

Guard adalah sistem governance yang memberikan:

- **Audit Trail** - Centralized logging dari semua operasi
- **Enforcement Rules** - Validasi berbasis rule dengan severity levels
- **State Management** - Checkpoint dan rollback capabilities
- **Security Validation** - File permissions, integrity, safety checks
- **Test Automation** - Run dan track test results
- **Performance Monitoring** - Detect regressions dan track metrics
- **Unified Dashboard** - See health status semua systems sekaligus

## 📦 Components

| Component | Purpose |
|-----------|---------|
| `audit_logger.py` | Structured logging untuk semua actions |
| `enforcement_rules.py` | Rule-based validation engine |
| `state_manager.py` | State tracking + checkpoints |
| `security_validator.py` | File security + integrity checks |
| `test_validator.py` | Automated test execution |
| `performance_guard.py` | Performance monit &  regression detection |
| `guard_status.py` | Unified status dashboard |

Plus 7 original validators (core integrity, change validation, dll)

## 🚀 Quick Examples

### Check System Health
```python
from guard import GuardStatus

status = GuardStatus()
status.print_status(verbose=True)

if status.is_healthy():
    print("✓ System is healthy")
```

### Log an Action
```python
from guard import get_audit_logger, AuditLevel

logger = get_audit_logger()
logger.log(
    AuditLevel.INFO,
    "my_component",
    "action_done",
    details={"key": "value"},
    status="success",
)
```

### Create Checkpoint
```python
from guard import get_state_manager

manager = get_state_manager()
manager.create_checkpoint("before_deploy")
# ... do something risky...
manager.restore_checkpoint("before_deploy")  # undo if needed
```

### Enforce Rules
```python
from guard import Rule, RuleSeverity, get_enforcement_engine

engine = get_enforcement_engine()
engine.register_rule(Rule(
    id="test_rule",
    name="Tests Must Pass",
    severity=RuleSeverity.CRITICAL,
    condition=lambda: os.path.exists(".tests_passed"),
))

if engine.enforce_critical():
    print("✓ All critical rules passed")
```

### Run Tests
```python
from guard import get_test_validator

validator = get_test_validator()
all_passed = validator.run_all_tests()

if not all_passed:
    print(validator.get_report())
```

## 📁 Output Directories

- `guard/.logs/` - Audit logs (JSONL + JSON summaries)
- `guard/.state/` - State files and checkpoints
- `guard/.metrics/` - Performance metrics and baselines

## 📊 Data Files

- `guard/core_hash.sha256` - Core directory integrity hash
- `guard/.logs/audit.jsonl` - Structured audit trail
- `guard/.state/current_state.json` - Current system state
- `guard/.metrics/baseline.json` - Performance baselines

## ✅ Key Features

✨ **Audit Trail** - Every action logged with timestamp, level, context
✨ **Checkpoints** - Create snapshots before risky operations
✨ **Rollback** - Restore from any checkpoint instantly
✨ **Security** - Detect dangerous files, permissions, path traversal
✨ **Regression Detection** - Track performance, alert on degradation
✨ **Test Integration** - Run Python/Rust tests, aggregate results
✨ **Health Dashboard** - See all systems at a glance

## 🔧 Usage

```bash
# Check guard health
python -m guard.guard_status

# Run all tests
python -m guard.test_validator

# Check for security issues
python -c "from guard import get_security_validator; \
           v = get_security_validator(); \
           v.check_directory_structure('.'); \
           print(v.get_report())"
```

## 📖 Full Documentation

See [GUARD_SYSTEM.md](GUARD_SYSTEM.md) for comprehensive documentation including:
- Detailed API reference
- Configuration options
- Integration examples
- Best practices
- CI/CD integration

## 🎓 Design Principles

1. **Always Log** - Every action should create audit trail
2. **Fail Safe** - Critical violations stop execution
3. **State Aware** - Track what changed and be able to undo
4. **Security First** - Validate before allowing operations
5. **Performance Conscious** - Monitor and alert on regressions

---

**Version**: Enhanced Guard System v2.0  
**Status**: Production Ready ✅
