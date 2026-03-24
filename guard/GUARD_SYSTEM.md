"""Comprehensive Guard system documentation and usage guide."""

# Guard System - Enhanced Governance and Validation

Sistem `guard/` yang disempurnakan menyediakan governance yang kuat dan disiplin untuk seluruh proyek.

## 🏗️ Arsitektur Guard (8 Komponen)

### 1. **Audit Logger** (`audit_logger.py`)
- **Tujuan**: Centralized audit trail dengan structured logging
- **Fitur**:
  - Structured JSON logging (JSONL format)
  - Severity levels (DEBUG, INFO, WARNING, CRITICAL, FAILURE)
  - Checkpoint system untuk state snapshots
  - Audit summary dan reporting
- **Usage**:
  ```python
  from guard import get_audit_logger, AuditLevel
  
  logger = get_audit_logger()
  logger.log(
      AuditLevel.INFO,
      "my_component",
      "action_performed",
      details={"key": "value"},
      status="success",
  )
  ```

### 2. **Enforcement Rules** (`enforcement_rules.py`)
- **Tujuan**: Rule-based validation engine dengan sophisticated checks
- **Fitur**:
  - Register custom validation rules
  - Severity levels (WARN, FAIL, CRITICAL)
  - Auto-fix capability
  - Pass-rate calculation
  - Detailed enforcement reports
- **Usage**:
  ```python
  from guard import Rule, RuleSeverity, get_enforcement_engine
  
  engine = get_enforcement_engine()
  engine.register_rule(Rule(
      id="rule_id",
      name="Rule Name",
      description="What it validates",
      severity=RuleSeverity.CRITICAL,
      condition=lambda: os.path.exists("file.txt"),
  ))
  
  results = engine.evaluate_all()
  print(engine.get_report())
  ```

### 3. **State Manager** (`state_manager.py`)
- **Tujuan**: State tracking dan checkpoint/rollback system
- **Fitur**:
  - Key-value state persistence
  - Checkpoint creation dengan hashing
  - Checkpoint listing dan restoration
  - State history tracking
  - Automatic cleanup (keep N recent)
- **Usage**:
  ```python
  from guard import get_state_manager
  
  manager = get_state_manager()
  manager.set("key", "value")
  manager.update({"key1": "value1", "key2": "value2"})
  
  # Create checkpoint
  hash = manager.create_checkpoint("checkpoint_1")
  
  # Later: restore from checkpoint
  manager.restore_checkpoint("checkpoint_1")
  ```

### 4. **Security Validator** (`security_validator.py`)
- **Tujuan**: File security dan integrity validation
- **Checks**:
  - File permissions (world/group writable detection)
  - File integrity (SHA256 hashing)
  - File size validation
  - File extension safety
  - Path traversal prevention
  - Binary file detection
- **Usage**:
  ```python
  from guard import get_security_validator
  
  validator = get_security_validator()
  
  # Check directory
  violations = validator.check_directory_structure(".")
  
  # Check file permissions
  if validator.check_file_permissions("file.txt"):
      print("Permissions OK")
  
  # Get detailed report
  print(validator.get_report())
  ```

### 5. **Test Validator** (`test_validator.py`)
- **Tujuan**: Automated test execution dan validation
- **Supports**:
  - Python tests (pytest)
  - Rust tests (cargo)
  - Integration tests
  - Test result aggregation
  - Detailed reporting
- **Usage**:
  ```python
  from guard import get_test_validator
  
  validator = get_test_validator()
  
  # Run all tests
  all_passed = validator.run_all_tests()
  
  # Run specific test type
  success, output = validator.run_python_tests()
  
  # Get report
  print(validator.get_report())
  ```

### 6. **Performance Guard** (`performance_guard.py`)
- **Tujuan**: Performance monitoring dan regression detection
- **Fitur**:
  - Execution time measurement
  - Baseline comparison
  - Regression detection (>10% threshold)
  - Threshold validation
  - Performance metrics history
- **Usage**:
  ```python
  from guard import get_performance_guard
  
  guard = get_performance_guard()
  
  # Measure function execution
  result = guard.measure("metric_name", my_function, *args)
  
  # Record metric
  guard.record_metric("my_metric", 0.5, unit="seconds")
  
  # Set baseline
  guard.set_baseline({"metric_1": 0.5, "metric_2": 1.0})
  
  # Get report
  print(guard.get_report())
  ```

### 7. **Original Guard Components** (Enhanced with audit logging)
- `core_integrity.py` - Core directory hash validation
- `change_validator.py` - Prevent core modifications
- `dual_execution.py` - Consistency validation
- `token_drift.py` - Token drift detection
- `auto_stage.py` - Automatic git staging
- `commit_control.py` - Semantic commit enforcement
- `failure.py` - Failure handling

### 8. **Guard Status Dashboard** (`guard_status.py`)
- **Tujuan**: Unified status reporting untuk semua guard systems
- **Fitur**:
  - System health check
  - Aggregated metrics
  - Comprehensive reporting
  - Verbose diagnostics
- **Usage**:
  ```python
  from guard import GuardStatus
  
  status = GuardStatus()
  
  # Check health
  if status.is_healthy():
      print("System is healthy")
  
  # Print status
  status.print_status(verbose=True)
  
  # Or use helper function
  from guard import print_guard_status
  print_guard_status(verbose=True)
  
  # Ensure health (exits if not)
  status.ensure_health()
  ```

---

## 📁 Directory Structure

```
guard/
├── Validators (Original)
│   ├── core_integrity.py        # Core hash validation
│   ├── change_validator.py      # Prevent core changes
│   ├── dual_execution.py        # Consistency checks
│   ├── token_drift.py           # Drift detection
│   ├── auto_stage.py            # Auto-staging
│   ├── commit_control.py        # Semantic commits
│   └── failure.py               # Failure handling
│
├── Enhanced Systems
│   ├── audit_logger.py          # Structured logging
│   ├── enforcement_rules.py     # Rule-based validation
│   ├── state_manager.py         # State + checkpoints
│   ├── security_validator.py    # Security checks
│   ├── test_validator.py        # Test automation
│   ├── performance_guard.py     # Performance monitoring
│   └── guard_status.py          # Unified status dashboard
│
├── Data Directories
│   ├── .logs/                   # Audit logs (JSONL+JSON)
│   ├── .state/                  # State files & checkpoints
│   ├── .metrics/                # Performance metrics
│   └── core_hash.sha256         # Core integrity hash
│
└── __init__.py                  # Package exports
```

---

## 🚀 Quick Start

### 1. Basic Guard Check

```python
from guard import (
    get_audit_logger,
    get_enforcement_engine,
    GuardStatus,
)

# Log an action
logger = get_audit_logger()
logger.log(
    "INFO",
    "my_system",
    "started",
    details={"version": "1.0"},
)

# Check system health
status = GuardStatus()
status.print_status()
```

### 2. Set Up Enforcement Rules

```python
from guard import Rule, RuleSeverity, get_enforcement_engine
import os

engine = get_enforcement_engine()

# Define critical rules
engine.register_rules([
    Rule(
        id="python_env",
        name="Python Environment",
        description="Python environment should be set up",
        severity=RuleSeverity.CRITICAL,
        condition=lambda: os.path.exists("venv") or os.environ.get("VIRTUAL_ENV"),
    ),
    Rule(
        id="git_configured",
        name="Git Configured",
        description="Git should be configured",
        severity=RuleSeverity.CRITICAL,
        condition=lambda: os.path.exists(".git"),
    ),
])

# Enforce critical rules only
if engine.enforce_critical():
    print("✓ Critical rules passed")
else:
    print("✗ Critical rules failed")
    print(engine.get_report())
```

### 3. Security Validation

```python
from guard import get_security_validator

validator = get_security_validator()

# Check directory for security issues
violations = validator.check_directory_structure(".")

# Display report
print(validator.get_report())

# Check specific file
if validator.check_file_permissions("sensitive_file.txt"):
    print("✓ File permissions are safe")
else:
    print("✗ File has unsafe permissions")
```

### 4. State Management & Checkpoints

```python
from guard import get_state_manager

manager = get_state_manager()

# Set state
manager.set("environment", "production")
manager.set("version", "1.0.0")

# Create checkpoint before risky operation
manager.create_checkpoint("before_upgrade")

# Do risky operation...
manager.set("version", "2.0.0")

# If something goes wrong, restore
manager.restore_checkpoint("before_upgrade")
print("Restored to", manager.get("version"))  # "1.0.0"
```

### 5. Test Validation

```python
from guard import get_test_validator

validator = get_test_validator()

# Run all tests
all_passed = validator.run_all_tests(verbose=True)

if not all_passed:
    print("Tests failed:")
    print(validator.get_report())
else:
    print("✓ All tests passed")
```

---

## 📊 File Organization

### Audit Logs (`guard/.logs/`)
- `audit.jsonl` - Structured audit events (one JSON per line)
- `summary.log` - Human-readable summary
- `checkpoint_*.json` - State checkpoints

### State Storage (`guard/.state/`)
- `current_state.json` - Current system state
- `state_history.jsonl` - State change history
- `checkpoint_*.json` - Checkpoint snapshots

### Performance Metrics (`guard/.metrics/`)
- `baseline.json` - Performance baselines
- `history.jsonl` - Historical metrics

---

## ✅ Best Practices

1. **Use Audit Logger for Everything**
   - Log all important actions
   - Use appropriate severity levels
   - Include context in details

2. **Checkpoint Before Risky Operations**
   - Create checkpoint before upgrades
   - Create checkpoint before deployments
   - Always have rollback plan

3. **Enforce Critical Rules**
   - Define what \"critical\" means for your project
   - Regularly evaluate enforcement status
   - Fix violations immediately

4. **Monitor Security**
   - Check for dangerous file extensions
   - Monitor file permissions
   - Detect path traversal attempts

5. **Validate Tests**
   - Always run tests before commit
   - Use test results for enforcement decisions
   - Track test coverage trends

6. **Track Performance**
   - Set baselines for key operations
   - Monitor for regressions
   - Investigate threshold violations

7. **Check Health Regularly**
   - Run guard status checks
   - Review audit logs
   - Act on violations

---

## 🔧 Configuration

### Environment Variables
- `GUARD_LOG_DIR` - Override default log directory (default: `guard/.logs`)
- `GUARD_STATE_DIR` - Override default state directory (default: `guard/.state`)
- `GUARD_METRICS_DIR` - Override default metrics directory (default: `guard/.metrics`)

### Performance Thresholds
Edit `performance_guard.py` to adjust:
- Regression threshold: 10% (default)
- Max file size: 10 MB (default)
- Test timeout: 300s for Python, 600s for Rust

### Security Settings
Edit `security_validator.py` to adjust:
- Safe file extensions list
- Dangerous file extensions list
- File size limits

---

## 📈 Monitoring & Reporting

### Generate Full Report
```bash
python -m guard.guard_status
```

### Check Specific Component
```python
from guard import get_audit_logger
logger = get_audit_logger()
logger.write_summary()  # Writes to guard/.logs/summary.log
```

### View Audit Trail
```bash
tail -f guard/.logs/audit.jsonl  # Stream audit events
cat guard/.logs/audit.jsonl | jq  # Parse JSON with jq
```

---

## 🎯 Integration with CI/CD

```bash
# Pre-commit: Run all guards
python -m guard.guard_status ensure_health

# Pre-test: Validate security and state
python -c "from guard import get_security_validator; \
           validator = get_security_validator(); \
           validator.check_directory_structure('.')"

# Pre-deploy: Run tests
python -m guard.test_validator

# Post-deploy: Update baseline
python -c "from guard import get_performance_guard; \
           guard = get_performance_guard(); \
           guard.set_baseline({'deployment': 0.5})"
```

---

## 📝 Changelog

### New in Enhanced Guard System
- ✨ Centralized audit logging with JSONL
- ✨ Rule-based enforcement engine
- ✨ State management with checkpoints
- ✨ Security validation system
- ✨ Automated test execution
- ✨ Performance regression detection
- ✨ Unified status dashboard
- ✨ Comprehensive reporting

---

**Last Updated**: 2026-03-24
**Version**: Enhanced Guard System v2.0
