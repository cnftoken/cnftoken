"""Enhanced rule-based enforcement engine with debugging and performance tracking."""
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Any, Optional, List, Dict, Tuple
import time
import traceback
from guard.audit_logger import get_audit_logger, AuditLevel


class RuleSeverity(Enum):
    """Rule violation severity."""
    WARN = "warn"
    FAIL = "fail"
    CRITICAL = "critical"


class RuleResult(Enum):
    """Rule evaluation result."""
    PASS = "pass"
    FAIL = "fail"
    SKIP = "skip"


@dataclass
class RuleMetrics:
    """Performance metrics for rule execution."""
    execution_time_ms: float = 0.0
    execution_count: int = 0
    pass_count: int = 0
    fail_count: int = 0
    auto_fix_attempts: int = 0
    auto_fix_successes: int = 0


@dataclass
class Rule:
    """
    Enhanced validation rule.
    
    Attributes:
        id: Unique rule identifier
        name: Human-readable name
        description: What this rule validates
        severity: Severity if violated
        condition: Callable that returns True if rule passes
        enabled: Whether rule is active
        auto_fix: Optional callable to auto-fix violations
        dependencies: List of rule IDs this depends on
        context: Additional context/metadata
        metrics: Performance and execution metrics
    """
    id: str
    name: str
    description: str
    severity: RuleSeverity
    condition: Callable[[], bool]
    enabled: bool = True
    auto_fix: Optional[Callable[[], bool]] = None
    dependencies: List[str] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)
    metrics: RuleMetrics = field(default_factory=RuleMetrics)


class EnforcementEngine:
    """
    Enhanced rule-based enforcement engine.
    
    Features:
    - Rule evaluation with performance tracking
    - Dependency resolution
    - Auto-fix with detailed reporting
    - Context-aware rule execution
    - Debugging information
    - Rule chaining and composition
    """
    
    def __init__(self):
        """Initialize enforcement engine."""
        self.rules: Dict[str, Rule] = {}
        self.results: List[Tuple[Rule, RuleResult, Optional[str], float]] = []
        self.logger = get_audit_logger()
        self.debug_mode: bool = False
    
    def register_rule(self, rule: Rule) -> None:
        """Register a validation rule with metrics."""
        self.rules[rule.id] = rule
        self.logger.log(
            AuditLevel.DEBUG,
            "enforcement_rules",
            "rule_registered",
            details={
                "rule_id": rule.id,
                "rule_name": rule.name,
                "severity": rule.severity.value,
                "dependencies": rule.dependencies,
            },
        )
    
    def register_rules(self, rules: List[Rule]) -> None:
        """Register multiple rules."""
        for rule in rules:
            self.register_rule(rule)
    
    def _check_dependencies(self, rule_id: str) -> Tuple[bool, List[str]]:
        """Check if rule dependencies are met."""
        rule = self.rules.get(rule_id)
        if not rule or not rule.dependencies:
            return True, []
        
        failed_deps = []
        for dep_id in rule.dependencies:
            # Find result for dependency
            dep_passed = any(
                r[1] == RuleResult.PASS for r in self.results
                if r[0].id == dep_id
            )
            if not dep_passed:
                failed_deps.append(dep_id)
        
        return len(failed_deps) == 0, failed_deps
    
    def evaluate_rule(
        self,
        rule_id: str,
        auto_fix: bool = False,
        skip_dependencies: bool = False,
    ) -> RuleResult:
        """
        Evaluate a single rule with detailed tracking.
        
        Args:
            rule_id: Rule to evaluate
            auto_fix: Whether to attempt auto-fix
            skip_dependencies: Skip dependency checking
            
        Returns:
            Rule evaluation result
        """
        rule = self.rules.get(rule_id)
        if not rule:
            return RuleResult.SKIP
        
        if not rule.enabled:
            return RuleResult.SKIP
        
        # Check dependencies
        if not skip_dependencies:
            deps_met, failed_deps = self._check_dependencies(rule_id)
            if not deps_met:
                error_msg = f"Unmet dependencies: {', '.join(failed_deps)}"
                self.results.append((rule, RuleResult.SKIP, error_msg, 0.0))
                return RuleResult.SKIP
        
        start_time = time.time()
        rule.metrics.execution_count += 1
        
        result = RuleResult.FAIL
        error_msg = None
        
        try:
            passed = rule.condition()
            
            if passed:
                result = RuleResult.PASS
                rule.metrics.pass_count += 1
                error_msg = None
            else:
                result = RuleResult.FAIL
                error_msg = f"Rule violation: {rule.description}"
                rule.metrics.fail_count += 1
                
                # Attempt auto-fix if enabled
                if auto_fix and rule.auto_fix:
                    rule.metrics.auto_fix_attempts += 1
                    try:
                        fix_success = rule.auto_fix()
                        if fix_success:
                            result = RuleResult.PASS
                            error_msg = "Auto-fixed"
                            rule.metrics.auto_fix_successes += 1
                            rule.metrics.pass_count += 1
                            rule.metrics.fail_count -= 1
                        else:
                            error_msg = "Auto-fix attempted but failed"
                    except Exception as e:
                        error_msg = f"Auto-fix exception: {str(e)}"
                        if self.debug_mode:
                            error_msg += f"\n{traceback.format_exc()}"
        
        except Exception as e:
            result = RuleResult.FAIL
            rule.metrics.fail_count += 1
            error_msg = f"Rule exception: {str(e)}"
            if self.debug_mode:
                error_msg += f"\n{traceback.format_exc()}"
        
        elapsed_ms = (time.time() - start_time) * 1000
        rule.metrics.execution_time_ms += elapsed_ms
        
        self.results.append((rule, result, error_msg, elapsed_ms))
        
        # Log the evaluation with performance data
        log_level = AuditLevel.INFO if result == RuleResult.PASS else AuditLevel.WARNING
        
        self.logger.log(
            log_level,
            "enforcement_rules",
            f"rule_evaluated",
            details={
                "rule_id": rule.id,
                "rule_name": rule.name,
                "result": result.value,
                "execution_time_ms": round(elapsed_ms, 2),
                "severity": rule.severity.value,
                "context": rule.context,
            },
            status="success" if result == RuleResult.PASS else "failure",
            error=error_msg,
        )
        
        return result
    
    def evaluate_all(self, auto_fix: bool = False) -> Dict[str, Any]:
        """
        Evaluate all enabled rules with comprehensive reporting.
        
        Args:
            auto_fix: Whether to attempt auto-fix on failures
            
        Returns:
            Evaluation results with metrics
        """
        self.results.clear()
        
        for rule_id in self.rules:
            self.evaluate_rule(rule_id, auto_fix=auto_fix)
        
        # Calculate summary
        passed = sum(1 for _, r, _, _ in self.results if r == RuleResult.PASS)
        failed = sum(1 for _, r, _, _ in self.results if r == RuleResult.FAIL)
        skipped = sum(1 for _, r, _, _ in self.results if r == RuleResult.SKIP)
        total_time = sum(t for _, _, _, t in self.results)
        
        # Check for critical violations
        critical_failures = [
            (rule, error) for rule, result, error, _ in self.results
            if result == RuleResult.FAIL and rule.severity == RuleSeverity.CRITICAL
        ]
        
        return {
            "total": len(self.rules),
            "passed": passed,
            "failed": failed,
            "skipped": skipped,
            "pass_rate": (passed / (passed + failed) * 100) if (passed + failed) > 0 else 100,
            "critical_failures": len(critical_failures),
            "total_execution_time_ms": round(total_time, 2),
            "details": [
                {
                    "rule_id": rule.id,
                    "rule_name": rule.name,
                    "severity": rule.severity.value,
                    "result": result.value,
                    "error": error,
                    "execution_time_ms": round(elapsed_ms, 2),
                    "metrics": {
                        "execution_count": rule.metrics.execution_count,
                        "pass_count": rule.metrics.pass_count,
                        "fail_count": rule.metrics.fail_count,
                        "auto_fix_successes": rule.metrics.auto_fix_successes,
                    },
                }
                for rule, result, error, elapsed_ms in self.results
            ],
        }
    
    def enforce_critical(self, auto_fix: bool = False) -> bool:
        """Enforce critical rules only."""
        critical_rules = {
            rid: r for rid, r in self.rules.items()
            if r.severity == RuleSeverity.CRITICAL and r.enabled
        }
        
        if not critical_rules:
            return True
        
        all_pass = True
        for rule_id in critical_rules:
            result = self.evaluate_rule(rule_id, auto_fix=auto_fix)
            if result == RuleResult.FAIL:
                all_pass = False
        
        return all_pass
    
    def get_rule_metrics(self, rule_id: str) -> Optional[Dict[str, Any]]:
        """Get metrics for specific rule."""
        rule = self.rules.get(rule_id)
        if not rule:
            return None
        
        return {
            "rule_id": rule_id,
            "execution_count": rule.metrics.execution_count,
            "total_time_ms": round(rule.metrics.execution_time_ms, 2),
            "avg_time_ms": round(
                rule.metrics.execution_time_ms / rule.metrics.execution_count, 2
            ) if rule.metrics.execution_count > 0 else 0,
            "pass_count": rule.metrics.pass_count,
            "fail_count": rule.metrics.fail_count,
            "pass_rate": (
                rule.metrics.pass_count / rule.metrics.execution_count * 100
            ) if rule.metrics.execution_count > 0 else 0,
            "auto_fix_successes": rule.metrics.auto_fix_successes,
        }
    
    def get_report(self) -> str:
        """Generate comprehensive enforcement report."""
        summary = self.evaluate_all()
        
        lines = [
            "=== ENFORCEMENT REPORT ===",
            "",
            f"Total Rules:         {summary['total']}",
            f"Passed:              {summary['passed']}",
            f"Failed:              {summary['failed']}",
            f"Skipped:             {summary['skipped']}",
            f"Pass Rate:           {summary['pass_rate']:.1f}%",
            f"Critical Failures:   {summary['critical_failures']}",
            f"Total Execution:     {summary['total_execution_time_ms']:.2f}ms",
            "",
            "=== RULE DETAILS ===",
        ]
        
        for detail in summary["details"]:
            status = "✓" if detail["result"] == "pass" else "✗" if detail["result"] == "fail" else "⊘"
            lines.append(
                f"{status} [{detail['severity'].upper():8}] {detail['rule_name']:30} "
                f"({detail['execution_time_ms']:.1f}ms)"
            )
            if detail["error"]:
                lines.append(f"  → {detail['error'][:70]}")
            if detail['metrics']['auto_fix_successes'] > 0:
                lines.append(f"  → Auto-fixed {detail['metrics']['auto_fix_successes']} times")
        
        return "\n".join(lines)


# Global enforcement engine instance
_engine: Optional[EnforcementEngine] = None


def get_enforcement_engine() -> EnforcementEngine:
    """Get or create global enforcement engine."""
    global _engine
    if _engine is None:
        _engine = EnforcementEngine()
    return _engine


if __name__ == "__main__":
    import os
    
    engine = get_enforcement_engine()
    
    # Example rules
    engine.register_rule(Rule(
        id="test_rule_1",
        name="Basic Test",
        description="Always passes",
        severity=RuleSeverity.WARN,
        condition=lambda: True,
    ))
    
    engine.register_rule(Rule(
        id="test_rule_2",
        name="File Exists",
        description="Check if guard dir exists",
        severity=RuleSeverity.FAIL,
        condition=lambda: os.path.isdir("guard"),
    ))
    
    print(engine.get_report())
