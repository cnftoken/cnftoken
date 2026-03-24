"""Enhanced policy engine with comprehensive rule management and enforcement."""
import yaml
import sys
import os
from typing import Dict, List, Any, Optional, Callable, Tuple
from pathlib import Path
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
from guard.failure import fail_hard, ExitCode
from guard.audit_logger import get_audit_logger, AuditLevel


class PolicyType(Enum):
    """Types of policies."""
    CORE_PROTECTION = "core_protection"
    CODE_QUALITY = "code_quality"
    SECURITY = "security"
    GOVERNANCE = "governance"
    PERFORMANCE = "performance"
    COMPLIANCE = "compliance"


class PolicySeverity(Enum):
    """Policy violation severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class PolicyViolation:
    """A policy violation report."""
    policy_id: str
    policy_name: str
    severity: PolicySeverity
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    context: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PolicyEnforcementResult:
    """Result of policy enforcement."""
    success: bool
    policies_checked: int
    policies_passed: int
    policies_failed: int
    violations: List[PolicyViolation] = field(default_factory=list)
    enforcement_time_ms: float = 0.0
    details: Dict[str, Any] = field(default_factory=dict)


class PolicyEngine:
    """
    Comprehensive policy enforcement engine.
    
    Features:
    - Rule loading and validation from YAML
    - Policy enforcement with detailed context
    - Violation tracking and reporting
    - Exception handling with audit logging
    - Configuration validation
    - Scoped policy enforcement
    - Performance tracking
    """
    
    def __init__(self, rules_path: Optional[str] = None):
        """
        Initialize policy engine.
        
        Args:
            rules_path: Path to rules.yaml (default: policy/rules.yaml)
        """
        if rules_path is None:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            rules_path = os.path.join(base_dir, 'rules.yaml')
        
        self.rules_path = Path(rules_path)
        self.logger = get_audit_logger()
        self.rules: Dict[str, Any] = {}
        self.violations: List[PolicyViolation] = []
        self.enforcement_history: List[PolicyEnforcementResult] = []
        
        # Load rules on initialization
        self._load_rules()
    
    def _load_rules(self) -> None:
        """Load rules from YAML file."""
        try:
            if not self.rules_path.exists():
                fail_hard(
                    f"Policy rules file not found: {self.rules_path}",
                    component="policy_engine",
                    details={"path": str(self.rules_path)},
                )
            
            with open(self.rules_path, 'r', encoding='utf-8') as f:
                self.rules = yaml.safe_load(f) or {}
            
            self.logger.log(
                AuditLevel.INFO,
                "policy_engine",
                "rules_loaded",
                details={
                    "path": str(self.rules_path),
                    "rule_count": len(self.rules),
                },
            )
        
        except Exception as e:
            fail_hard(
                f"Failed to load policy rules: {str(e)}",
                component="policy_engine",
                details={"path": str(self.rules_path), "error": str(e)},
            )
    
    def get_rule(self, rule_name: str) -> Optional[Any]:
        """Get a specific rule by name."""
        return self.rules.get(rule_name)
    
    def validate_config(self) -> Tuple[bool, List[str]]:
        """
        Validate policy configuration.
        
        Returns:
            Tuple of (is_valid, errors)
        """
        errors = []
        
        # Check required sections
        required = ['core_immutable', 'policy_engine', 'guard_system', 'commit_control']
        for req in required:
            if req not in self.rules:
                errors.append(f"Missing required policy: {req}")
        
        # Validate core_immutable configuration
        if 'core_paths' in self.rules:
            core_paths = self.rules.get('core_paths', [])
            if not isinstance(core_paths, list):
                errors.append("core_paths must be a list")
        
        # Validate commit_control configuration
        commit_ctrl = self.rules.get('commit_control', {})
        if 'allowed_types' in commit_ctrl:
            allowed_types = commit_ctrl['allowed_types']
            if not isinstance(allowed_types, list):
                errors.append("commit_control.allowed_types must be a list")
        
        return len(errors) == 0, errors
    
    def enforce_core_immutability(self) -> bool:
        """
        Enforce core immutability policy.
        
        Returns:
            True if core is immutable, raises otherwise
        """
        if not self.rules.get('core_immutable', False):
            return True
        
        try:
            from guard.change_validator import get_validator
            
            validator = get_validator()
            analysis = validator.analyze_changes()
            
            # Check for changes to core files
            core_paths = self.rules.get('core_paths', ['core'])
            
            for change_type, files in analysis.get('staged_changes', {}).items():
                for file in files:
                    if any(file.startswith(core) for core in core_paths):
                        violation = PolicyViolation(
                            policy_id="core_immutable",
                            policy_name="Core Immutability",
                            severity=PolicySeverity.CRITICAL,
                            message=f"Core file modification detected: {file}",
                            details={
                                "file": file,
                                "change_type": str(change_type),
                            },
                            context={"policy": "core_immutability"},
                        )
                        self.violations.append(violation)
                        
                        self.logger.log(
                            AuditLevel.CRITICAL,
                            "policy_engine",
                            "core_immutability_violation",
                            details={"file": file},
                            status="failure",
                        )
                        
                        return False
            
            return True
        
        except Exception as e:
            fail_hard(
                f"Core immutability check failed: {str(e)}",
                component="policy_engine",
                details={"error": str(e)},
            )
    
    def enforce_guard_system(self) -> bool:
        """
        Enforce guard system requirements.
        
        Returns:
            True if all guard systems are ready
        """
        required_guards = self.rules.get('guard_system', {}).get('required', [])
        
        if not required_guards:
            return True
        
        missing = []
        
        for guard_name in required_guards:
            try:
                # Try to import guard modules
                if guard_name == 'core_integrity_hash_checker':
                    from guard.core_integrity import get_validator
                    get_validator()
                elif guard_name == 'change_validator':
                    from guard.change_validator import get_validator
                    get_validator()
                elif guard_name == 'dual_execution_validator':
                    from guard.dual_execution import get_validator
                    get_validator()
                elif guard_name == 'token_drift_detector':
                    from guard.token_drift import get_validator
                    get_validator()
                else:
                    missing.append(guard_name)
            
            except ImportError:
                missing.append(guard_name)
        
        if missing:
            violation = PolicyViolation(
                policy_id="guard_system",
                policy_name="Guard System Requirements",
                severity=PolicySeverity.CRITICAL,
                message=f"Missing guard systems: {', '.join(missing)}",
                details={"missing": missing},
                context={"policy": "guard_system"},
            )
            self.violations.append(violation)
            return False
        
        return True
    
    def enforce_commit_control(self) -> bool:
        """
        Enforce commit control policy.
        
        Returns:
            True if commit control is satisfied
        """
        commit_rules = self.rules.get('commit_control', {})
        
        if commit_rules.get('enforce_atomic', False):
            try:
                from guard.commit_control import check_atomic_commit
                check_atomic_commit()
            except Exception as e:
                violation = PolicyViolation(
                    policy_id="commit_control",
                    policy_name="Commit Control",
                    severity=PolicySeverity.ERROR,
                    message=f"Commit control violation: {str(e)}",
                    details={"error": str(e)},
                    context={"policy": "commit_control"},
                )
                self.violations.append(violation)
                return False
        
        return True
    
    def enforce_policy(
        self,
        policy_name: str,
        enforcer: Callable[[], bool],
    ) -> bool:
        """
        Enforce a custom policy.
        
        Args:
            policy_name: Name of the policy
            enforcer: Callable that returns True if policy passes
            
        Returns:
            True if policy enforcement succeeds
        """
        try:
            if enforcer():
                self.logger.log(
                    AuditLevel.INFO,
                    "policy_engine",
                    f"policy_enforced",
                    details={"policy": policy_name},
                    status="success",
                )
                return True
            else:
                violation = PolicyViolation(
                    policy_id=policy_name,
                    policy_name=policy_name,
                    severity=PolicySeverity.ERROR,
                    message=f"Policy enforcement failed: {policy_name}",
                    context={"policy": policy_name},
                )
                self.violations.append(violation)
                return False
        
        except Exception as e:
            violation = PolicyViolation(
                policy_id=policy_name,
                policy_name=policy_name,
                severity=PolicySeverity.CRITICAL,
                message=f"Policy execution error: {str(e)}",
                details={"error": str(e)},
                context={"policy": policy_name},
            )
            self.violations.append(violation)
            return False
    
    def enforce_all(self) -> PolicyEnforcementResult:
        """
        Enforce all policies.
        
        Returns:
            PolicyEnforcementResult with detailed report
        """
        import time
        start_time = time.time()
        
        self.violations.clear()
        
        policies_checked = 0
        policies_passed = 0
        
        # 1. Config validation
        is_valid, errors = self.validate_config()
        policies_checked += 1
        if is_valid:
            policies_passed += 1
            self.logger.log(
                AuditLevel.INFO,
                "policy_engine",
                "config_validation_passed",
                status="success",
            )
        else:
            for error in errors:
                violation = PolicyViolation(
                    policy_id="config_validation",
                    policy_name="Configuration Validation",
                    severity=PolicySeverity.ERROR,
                    message=error,
                    context={"policy": "config_validation"},
                )
                self.violations.append(violation)
        
        # 2. Core immutability
        policies_checked += 1
        if self.enforce_core_immutability():
            policies_passed += 1
        
        # 3. Guard system
        policies_checked += 1
        if self.enforce_guard_system():
            policies_passed += 1
        
        # 4. Commit control
        policies_checked += 1
        if self.enforce_commit_control():
            policies_passed += 1
        
        elapsed_ms = (time.time() - start_time) * 1000
        
        result = PolicyEnforcementResult(
            success=len(self.violations) == 0,
            policies_checked=policies_checked,
            policies_passed=policies_passed,
            policies_failed=policies_checked - policies_passed,
            violations=self.violations,
            enforcement_time_ms=elapsed_ms,
            details={
                "strict_mode": self.rules.get('policy_engine', {}).get('strict', False),
                "fail_on_violation": self.rules.get('policy_engine', {}).get('fail_on_violation', False),
            },
        )
        
        self.enforcement_history.append(result)
        
        # Log result
        log_level = AuditLevel.INFO if result.success else AuditLevel.WARNING
        self.logger.log(
            log_level,
            "policy_engine",
            "enforcement_completed",
            details={
                "checked": result.policies_checked,
                "passed": result.policies_passed,
                "failed": result.policies_failed,
                "violations": len(result.violations),
                "time_ms": round(result.enforcement_time_ms, 2),
            },
            status="success" if result.success else "failure",
        )
        
        # Fail if strict mode and violations exist
        if self.rules.get('policy_engine', {}).get('fail_on_violation', False) and result.violations:
            violation_msgs = [v.message for v in result.violations[:3]]
            fail_hard(
                f"Policy enforcement failed with {len(result.violations)} violation(s)",
                component="policy_engine",
                details={"violations": violation_msgs},
            )
        
        return result
    
    def get_report(self) -> str:
        """Generate policy enforcement report."""
        lines = [
            "=== POLICY ENGINE REPORT ===",
            "",
            f"Rules File:  {self.rules_path}",
            f"Strict Mode: {self.rules.get('policy_engine', {}).get('strict', False)}",
            "",
            "Violations:",
        ]
        
        if not self.violations:
            lines.append("  ✓ No violations detected")
        else:
            for violation in self.violations[:10]:
                icon = "✗" if violation.severity in [PolicySeverity.CRITICAL, PolicySeverity.ERROR] else "⚠"
                lines.append(f"  {icon} [{violation.severity.value.upper()}] {violation.policy_name}")
                lines.append(f"     {violation.message}")
        
        if len(self.violations) > 10:
            lines.append(f"  ... and {len(self.violations) - 10} more violations")
        
        # Show enforcement history
        if self.enforcement_history:
            lines.extend(["", "Enforcement History:"])
            for i, result in enumerate(self.enforcement_history[-5:], 1):
                status = "✓" if result.success else "✗"
                lines.append(
                    f"  {status} Enforcement {i}: {result.policies_passed}/{result.policies_checked} passed "
                    f"({result.enforcement_time_ms:.2f}ms)"
                )
        
        return "\n".join(lines)


# Global engine instance
_engine: Optional[PolicyEngine] = None


def get_engine(rules_path: Optional[str] = None) -> PolicyEngine:
    """Get or create global policy engine."""
    global _engine
    if _engine is None:
        _engine = PolicyEngine(rules_path)
    return _engine


# Backward compatible functions
def load_rules(path=None) -> Dict[str, Any]:
    """Load rules (backward compatible)."""
    engine = get_engine(path)
    return engine.rules


def enforce_core_immutability(rules=None) -> None:
    """Enforce core immutability (backward compatible)."""
    engine = get_engine()
    if not engine.enforce_core_immutability():
        fail_hard(
            "Core immutability check failed",
            component="policy_engine",
        )


def enforce_all() -> PolicyEnforcementResult:
    """Enforce all policies (backward compatible)."""
    engine = get_engine()
    return engine.enforce_all()


if __name__ == '__main__':
    engine = get_engine()
    result = engine.enforce_all()
    print(engine.get_report())
    if not result.success:
        sys.exit(1)
