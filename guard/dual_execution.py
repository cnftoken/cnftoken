"""Enhanced dual execution with state comparison and analysis."""
import time
import sys
import traceback
from typing import Callable, Any, Dict, Tuple, Optional, List
from enum import Enum
from dataclasses import dataclass, field
from guard.failure import fail_hard, ExitCode
from guard.audit_logger import get_audit_logger, AuditLevel


class ConsistencyLevel(Enum):
    """Execution consistency levels."""
    STRICT = "strict"          # Exact identical results
    SEMANTIC = "semantic"      # Logically equivalent
    PERMISSIVE = "permissive"  # Similar results allowed


@dataclass
class ExecutionResult:
    """Execution result with metadata."""
    success: bool
    result: Any
    duration_ms: float
    error: Optional[str] = None
    trace: Optional[str] = None
    memory_delta: int = 0
    output: Optional[str] = None


@dataclass
class DualExecutionReport:
    """Dual execution comparison report."""
    consistent: bool
    first_result: ExecutionResult
    second_result: ExecutionResult
    level: ConsistencyLevel
    differences: List[str] = field(default_factory=list)
    performance_delta_ms: float = 0.0
    comparison_details: Dict[str, Any] = field(default_factory=dict)


class DualExecutionValidator:
    """
    Enhanced dual execution validator.
    
    Features:
    - Dual execution with consistency checking
    - Performance analysis (timing comparison)
    - Error detection and reporting
    - State comparison (deep equality)
    - Detailed execution reports
    - Tolerance levels for semantic equivalence
    """
    
    def __init__(self, level: ConsistencyLevel = ConsistencyLevel.STRICT):
        """Initialize validator."""
        self.logger = get_audit_logger()
        self.level = level
        self.last_report: Optional[DualExecutionReport] = None
    
    def _execute_once(
        self,
        func: Callable,
        args: Tuple,
        kwargs: Dict,
        run_number: int,
    ) -> ExecutionResult:
        """Execute function once and capture result."""
        start_time = time.time()
        start_memory = self._get_memory_usage()
        
        result = None
        error = None
        trace = None
        success = True
        
        try:
            result = func(*args, **kwargs)
        except Exception as e:
            success = False
            error = str(e)
            trace = traceback.format_exc()
            
            self.logger.log(
                AuditLevel.WARNING,
                "dual_execution",
                f"run_{run_number}_failed",
                error=error,
                details={"run": run_number},
            )
        
        end_time = time.time()
        end_memory = self._get_memory_usage()
        
        return ExecutionResult(
            success=success,
            result=result,
            duration_ms=(end_time - start_time) * 1000,
            error=error,
            trace=trace,
            memory_delta=end_memory - start_memory,
        )
    
    def _get_memory_usage(self) -> int:
        """Get current memory usage in bytes."""
        try:
            import psutil
            process = psutil.Process()
            return process.memory_info().rss
        except ImportError:
            return 0
    
    def _compare_results(
        self,
        first: ExecutionResult,
        second: ExecutionResult,
    ) -> Tuple[bool, List[str]]:
        """Compare two execution results."""
        differences = []
        
        # Check success status
        if first.success != second.success:
            differences.append(
                f"Success status mismatch: {first.success} vs {second.success}"
            )
        
        if not first.success or not second.success:
            # Already logged, just note the difference
            return False, differences
        
        # Check result equality
        if self.level == ConsistencyLevel.STRICT:
            if first.result != second.result:
                differences.append(
                    f"Result mismatch: {type(first.result).__name__}"
                )
        elif self.level == ConsistencyLevel.SEMANTIC:
            if not self._are_semantically_equal(first.result, second.result):
                differences.append("Results are not semantically equivalent")
        
        # Check performance (allow 50% variance)
        time_variance = abs(first.duration_ms - second.duration_ms) / max(first.duration_ms, second.duration_ms)
        if time_variance > 0.5:
            differences.append(
                f"Performance variance: {first.duration_ms:.1f}ms vs {second.duration_ms:.1f}ms"
            )
        
        consistent = len(differences) == 0
        return consistent, differences
    
    def _are_semantically_equal(self, a: Any, b: Any) -> bool:
        """Check if values are semantically equivalent."""
        if type(a) != type(b):
            return False
        
        if isinstance(a, (list, tuple)):
            return len(a) == len(b) and all(
                self._are_semantically_equal(x, y) for x, y in zip(a, b)
            )
        elif isinstance(a, dict):
            return set(a.keys()) == set(b.keys()) and all(
                self._are_semantically_equal(a[k], b[k]) for k in a.keys()
            )
        else:
            return a == b
    
    def validate_dual_execution(
        self,
        func: Callable,
        *args,
        **kwargs,
    ) -> bool:
        """
        Execute function twice and validate consistency.
        
        Args:
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            True if consistent, raises otherwise
        """
        # Execute twice
        first = self._execute_once(func, args, kwargs, 1)
        second = self._execute_once(func, args, kwargs, 2)
        
        # Compare results
        consistent, differences = self._compare_results(first, second)
        
        # Create report
        self.last_report = DualExecutionReport(
            consistent=consistent,
            first_result=first,
            second_result=second,
            level=self.level,
            differences=differences,
            performance_delta_ms=abs(first.duration_ms - second.duration_ms),
            comparison_details={
                'func_name': func.__name__,
                'args': len(args),
                'kwargs': len(kwargs),
            },
        )
        
        # Log result
        self.logger.log(
            AuditLevel.INFO,
            "dual_execution",
            "validation" + ("_passed" if consistent else "_failed"),
            details={
                'consistent': consistent,
                'duration_1': round(first.duration_ms, 2),
                'duration_2': round(second.duration_ms, 2),
                'level': self.level.value,
            },
            status="success" if consistent else "failure",
        )
        
        if not consistent:
            fail_hard(
                "Dual execution validation failed: results were inconsistent",
                component="dual_execution",
                details={
                    "func": func.__name__,
                    "differences": differences[:3],  # First 3 differences
                    "level": self.level.value,
                },
            )
        
        return True
    
    def get_report(self) -> str:
        """Get detailed execution comparison report."""
        if not self.last_report:
            return "No report available"
        
        r = self.last_report
        
        lines = [
            "=== DUAL EXECUTION REPORT ===",
            "",
            f"Status:           {'✓ CONSISTENT' if r.consistent else '✗ INCONSISTENT'}",
            f"Level:            {r.level.value}",
            f"Function:         {r.comparison_details.get('func_name', 'unknown')}",
            "",
            "First Execution:",
            f"  Success:        {r.first_result.success}",
            f"  Duration:       {r.first_result.duration_ms:.2f}ms",
            f"  Memory Delta:   {r.first_result.memory_delta:,} bytes",
            "",
            "Second Execution:",
            f"  Success:        {r.second_result.success}",
            f"  Duration:       {r.second_result.duration_ms:.2f}ms",
            f"  Memory Delta:   {r.second_result.memory_delta:,} bytes",
            "",
            f"Performance Variance: {r.performance_delta_ms:.2f}ms",
        ]
        
        if r.differences:
            lines.extend(["", "Differences:"])
            for diff in r.differences[:5]:
                lines.append(f"  - {diff}")
            if len(r.differences) > 5:
                lines.append(f"  ... and {len(r.differences) - 5} more")
        
        return "\n".join(lines)


# Global validator instance
_validator: Optional[DualExecutionValidator] = None


def get_validator(level: ConsistencyLevel = ConsistencyLevel.STRICT) -> DualExecutionValidator:
    """Get or create validator instance."""
    global _validator
    if _validator is None or _validator.level != level:
        _validator = DualExecutionValidator(level)
    return _validator


# Backward compatible function
def validate_two_runs(func, *args, **kwargs) -> bool:
    """Validate function returns consistent results on two runs."""
    return get_validator().validate_dual_execution(func, *args, **kwargs)


def validate_with_level(
    level: str,
    func: Callable,
    *args,
    **kwargs,
) -> bool:
    """Validate with specific consistency level."""
    try:
        consistency_level = ConsistencyLevel[level.upper()]
    except KeyError:
        fail_hard(
            f"Invalid consistency level: {level}",
            component="dual_execution",
            details={"valid_levels": [e.value for e in ConsistencyLevel]},
        )
    
    return get_validator(consistency_level).validate_dual_execution(func, *args, **kwargs)


if __name__ == '__main__':
    # Example validation
    def test_func():
        return sum([1, 2, 3, 4, 5])
    
    validator = get_validator()
    validator.validate_dual_execution(test_func)
    print(validator.get_report())
