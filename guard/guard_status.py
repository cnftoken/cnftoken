"""Comprehensive guard system status and reporting."""
import sys
from datetime import datetime
from typing import Dict, Any
from guard.audit_logger import get_audit_logger, AuditLevel
from guard.enforcement_rules import get_enforcement_engine
from guard.state_manager import get_state_manager
from guard.security_validator import get_security_validator
from guard.test_validator import get_test_validator
from guard.performance_guard import get_performance_guard


class GuardStatus:
    """
    Comprehensive guard system status dashboard.
    
    Aggregates status from all guard components and provides
    unified reporting and enforcement.
    """
    
    def __init__(self):
        """Initialize guard status dashboard."""
        self.audit_logger = get_audit_logger()
        self.enforcement_engine = get_enforcement_engine()
        self.state_manager = get_state_manager()
        self.security_validator = get_security_validator()
        self.test_validator = get_test_validator()
        self.performance_guard = get_performance_guard()
        
        self.status_checks: Dict[str, bool] = {}
    
    def check_audit_system(self) -> bool:
        """Check if audit logging is working."""
        try:
            summary = self.audit_logger.get_summary()
            self.status_checks["audit_system"] = True
            return True
        except Exception as e:
            self.audit_logger.log(
                AuditLevel.WARNING,
                "guard_status",
                "audit_system_check_failed",
                error=str(e),
            )
            self.status_checks["audit_system"] = False
            return False
    
    def check_state_system(self) -> bool:
        """Check if state management is working."""
        try:
            state = self.state_manager.get_all()
            self.status_checks["state_system"] = True
            return True
        except Exception as e:
            self.audit_logger.log(
                AuditLevel.WARNING,
                "guard_status",
                "state_system_check_failed",
                error=str(e),
            )
            self.status_checks["state_system"] = False
            return False
    
    def check_enforcement_system(self) -> bool:
        """Check if enforcement rules are working."""
        try:
            results = self.enforcement_engine.evaluate_all()
            pass_rate = results.get("pass_rate", 0)
            
            # System is OK if pass rate >= 80%
            ok = pass_rate >= 80
            self.status_checks["enforcement_system"] = ok
            return ok
        except Exception as e:
            self.audit_logger.log(
                AuditLevel.WARNING,
                "guard_status",
                "enforcement_system_check_failed",
                error=str(e),
            )
            self.status_checks["enforcement_system"] = False
            return False
    
    def check_security_system(self) -> bool:
        """Check for critical security violations."""
        try:
            violations = self.security_validator.get_violations()
            
            # Critical violations are NOT OK
            critical = [v for v in violations if v[2] == "critical"]
            
            ok = len(critical) == 0
            self.status_checks["security_system"] = ok
            
            if not ok:
                for filepath, violation, _ in critical:
                    self.audit_logger.log(
                        AuditLevel.CRITICAL,
                        "guard_status",
                        "security_violation",
                        details={"file": filepath, "violation": violation},
                    )
            
            return ok
        except Exception as e:
            self.audit_logger.log(
                AuditLevel.WARNING,
                "guard_status",
                "security_system_check_failed",
                error=str(e),
            )
            self.status_checks["security_system"] = False
            return False
    
    def check_all(self) -> Dict[str, bool]:
        """
        Run all system checks.
        
        Returns:
            Dictionary of check_name -> passed
        """
        self.status_checks.clear()
        
        self.check_audit_system()
        self.check_state_system()
        self.check_enforcement_system()
        self.check_security_system()
        
        return dict(self.status_checks)
    
    def is_healthy(self) -> bool:
        """
        Check if guard system is healthy.
        
        Returns:
            True if all critical checks pass
        """
        checks = self.check_all()
        
        # All checks must pass for healthy status
        return all(checks.values())
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Get comprehensive status summary.
        
        Returns:
            Summary of all guard system status
        """
        checks = self.check_all()
        
        audit_summary = self.audit_logger.get_summary()
        enforcement_results = self.enforcement_engine.evaluate_all()
        security_violations = self.security_validator.get_violations()
        state = self.state_manager.get_all()
        metrics = self.performance_guard.get_current_metrics()
        
        critical_violations = [v for v in security_violations if v[2] == "critical"]
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "overall_health": "healthy" if self.is_healthy() else "unhealthy",
            "system_checks": checks,
            "audit_events": audit_summary.get("total_events", 0),
            "enforcement_rules": {
                "total": enforcement_results.get("total", 0),
                "passed": enforcement_results.get("passed", 0),
                "failed": enforcement_results.get("failed", 0),
                "pass_rate": enforcement_results.get("pass_rate", 0),
            },
            "security": {
                "total_violations": len(security_violations),
                "critical_violations": len(critical_violations),
                "warning_violations": len([v for v in security_violations if v[2] == "warning"]),
            },
            "state": {
                "checkpoints": len(self.state_manager.list_checkpoints()),
                "keys": len(state),
            },
            "performance": {
                "metrics_tracked": len(metrics),
            },
        }
    
    def get_report(self, verbose: bool = False) -> str:
        """
        Generate comprehensive guard status report.
        
        Args:
            verbose: Include detailed information
            
        Returns:
            Human-readable report
        """
        summary = self.get_summary()
        
        lines = [
            "╔═══════════════════════════════════════╗",
            "║     GUARD SYSTEM STATUS REPORT        ║",
            "╚═══════════════════════════════════════╝",
            "",
            f"Timestamp: {summary['timestamp']}",
            f"Overall Health: {summary['overall_health'].upper()}",
            "",
            "=== SYSTEM CHECKS ===",
        ]
        
        for check_name, passed in summary["system_checks"].items():
            status = "✓" if passed else "✗"
            lines.append(f"{status} {check_name}")
        
        lines.extend([
            "",
            "=== METRICS ===",
            f"Audit Events: {summary['audit_events']}",
            f"Enforcement Rules: {summary['enforcement_rules']['passed']}/{summary['enforcement_rules']['total']} passed",
            f"  Pass Rate: {summary['enforcement_rules']['pass_rate']:.1f}%",
        ])
        
        lines.extend([
            f"Security Violations: {summary['security']['total_violations']}",
            f"  Critical: {summary['security']['critical_violations']}",
            f"  Warnings: {summary['security']['warning_violations']}",
        ])
        
        lines.extend([
            f"State Checkpoints: {summary['state']['checkpoints']}",
            f"Performance Metrics: {summary['performance']['metrics_tracked']}",
        ])
        
        if verbose:
            lines.extend([
                "",
                "=== AUDIT SUMMARY ===",
            ])
            audit_summary = self.audit_logger.get_summary()
            lines.append(f"Total Events: {audit_summary.get('total_events', 0)}")
            
            if "by_level" in audit_summary:
                for level, count in audit_summary["by_level"].items():
                    lines.append(f"  {level}: {count}")
            
            lines.extend([
                "",
                "=== ENFORCEMENT DETAILS ===",
            ])
            results = self.enforcement_engine.evaluate_all()
            for detail in results.get("details", [])[:5]:  # Show first 5
                status = "✓" if detail["result"] == "pass" else "✗"
                lines.append(f"{status} {detail['rule_name']}")
        
        return "\\n".join(lines)
    
    def print_status(self, verbose: bool = False) -> None:
        """Print guard status to console."""
        print(self.get_report(verbose=verbose))
    
    def ensure_health(self) -> bool:
        """
        Ensure guard system is healthy, exit if not.
        
        Returns:
            True if healthy, exits with error if not
        """
        if not self.is_healthy():
            self.print_status(verbose=True)
            print("\\n✗ Guard system is unhealthy. Aborting.", file=sys.stderr)
            sys.exit(1)
        return True


def print_guard_status(verbose: bool = False) -> None:
    """
    Print guard system status.
    
    Args:
        verbose: Include detailed information
    """
    status = GuardStatus()
    status.print_status(verbose=verbose)


def get_status() -> GuardStatus:
    """
    Get guard status instance.
    
    Returns:
        GuardStatus: Guard system status instance
    """
    return GuardStatus()


if __name__ == "__main__":
    status = GuardStatus()
    status.print_status(verbose=True)
    
    print()
    print("Health Check:", "✓ HEALTHY" if status.is_healthy() else "✗ UNHEALTHY")
