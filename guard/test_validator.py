"""Enhanced test validation with parallel execution and retry logic."""
import subprocess
import sys
import time
import statistics
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor, as_completed
from guard.audit_logger import get_audit_logger, AuditLevel


@dataclass
class TestRunResult:
    """Result of a test run."""
    test_type: str
    name: str
    success: bool
    duration_ms: float
    output: str
    retry_count: int = 0
    return_code: int = 0


@dataclass
class TestValidationReport:
    """Overall test validation report."""
    total_tests: int = 0
    passed_tests: int = 0
    failed_tests: int = 0
    total_time_ms: float = 0.0
    results: List[TestRunResult] = field(default_factory=list)
    coverage_percentage: float = 0.0


class TestValidator:
    """
    Enhanced test validator with parallel execution.
    
    Features:
    - Python and Rust test execution
    - Parallel test runs
    - Retry logic for flaky tests
    - Coverage tracking
    - Performance analysis
    - Detailed reporting
    """
    
    def __init__(self, max_workers: int = 4, max_retries: int = 2):
        """Initialize test validator."""
        self.logger = get_audit_logger()
        self.max_workers = max_workers
        self.max_retries = max_retries
        self.results: List[TestRunResult] = []
        self.report: Optional[TestValidationReport] = None
    
    def _run_test_suite(
        self,
        cmd: List[str],
        timeout: int,
        test_name: str,
        test_type: str,
        max_retries: int,
    ) -> TestRunResult:
        """Execute a test suite with retry logic."""
        last_error = None
        last_output = ""
        
        for attempt in range(max_retries + 1):
            start_time = time.time()
            
            try:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                )
                
                duration_ms = (time.time() - start_time) * 1000
                output = result.stdout + result.stderr
                success = result.returncode == 0
                last_output = output
                
                if success:
                    return TestRunResult(
                        test_type=test_type,
                        name=test_name,
                        success=True,
                        duration_ms=duration_ms,
                        output=output[-500:],
                        retry_count=attempt,
                        return_code=0,
                    )
                
                last_error = f"Return code: {result.returncode}"
                
                if attempt < max_retries:
                    time.sleep(0.5 * (attempt + 1))
            
            except subprocess.TimeoutExpired:
                duration_ms = (time.time() - start_time) * 1000
                last_error = "Test timed out"
                
                if attempt == max_retries:
                    return TestRunResult(
                        test_type=test_type,
                        name=test_name,
                        success=False,
                        duration_ms=duration_ms,
                        output=f"Timeout after {timeout}s",
                        retry_count=attempt,
                        return_code=-1,
                    )
            
            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                last_error = str(e)
                last_output = str(e)
        
        # All retries exhausted
        return TestRunResult(
            test_type=test_type,
            name=test_name,
            success=False,
            duration_ms=duration_ms,
            output=last_output[-500:],
            retry_count=max_retries,
            return_code=-1,
        )
    
    def run_python_tests(
        self,
        test_dir: str = "tests",
        verbose: bool = False,
        with_coverage: bool = True,
    ) -> TestRunResult:
        """Run Python tests."""
        cmd = [sys.executable, "-m", "pytest", test_dir]
        if verbose:
            cmd.append("-v")
        if with_coverage:
            cmd.extend(["--cov", "--cov-report=term"])
        
        return self._run_test_suite(
            cmd,
            timeout=300,
            test_name="python_tests",
            test_type="python",
            max_retries=self.max_retries,
        )
    
    def run_rust_tests(
        self,
        workspace: bool = True,
        verbose: bool = False,
    ) -> TestRunResult:
        """Run Rust tests."""
        cmd = ["cargo", "test"]
        if workspace:
            cmd.append("--workspace")
        if verbose:
            cmd.append("-v")
        
        return self._run_test_suite(
            cmd,
            timeout=600,
            test_name="rust_tests",
            test_type="rust",
            max_retries=self.max_retries,
        )
    
    def run_tests_parallel(
        self,
        test_suites: List[Tuple[str, Dict]],
    ) -> TestValidationReport:
        """
        Run multiple test suites in parallel.
        
        Args:
            test_suites: List of (suite_type, config) tuples
            
        Returns:
            ThTestValidationReport
        """
        import time
        start_time = time.time()
        
        self.results.clear()
        
        # Run in parallel
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {}
            
            for suite_type, config in test_suites:
                if suite_type == "python":
                    future = executor.submit(
                        self.run_python_tests,
                        **config
                    )
                elif suite_type == "rust":
                    future = executor.submit(
                        self.run_rust_tests,
                        **config
                    )
                else:
                    continue
                
                futures[future] = (suite_type, config)
            
            for future in as_completed(futures):
                try:
                    result = future.result()
                    self.results.append(result)
                except Exception:
                    pass
        
        # Generate report
        passed = sum(1 for r in self.results if r.success)
        failed = len(self.results) - passed
        total_time = (time.time() - start_time) * 1000
        
        self.report = TestValidationReport(
            total_tests=len(self.results),
            passed_tests=passed,
            failed_tests=failed,
            total_time_ms=total_time,
            results=self.results,
        )
        
        self.logger.log(
            AuditLevel.INFO,
            "test_validator",
            "test_suite_completed",
            details={
                "total": len(self.results),
                "passed": passed,
                "failed": failed,
                "total_time_ms": round(total_time, 2),
            },
            status="success" if failed == 0 else "failure",
        )
        
        return self.report
    
    def get_report(self) -> str:
        """Generate test validation report."""
        if not self.report:
            return "No test report available"
        
        lines = [
            "=== TEST VALIDATION REPORT ===",
            "",
            f"Total Tests:     {self.report.total_tests}",
            f"Passed:          {self.report.passed_tests}",
            f"Failed:          {self.report.failed_tests}",
            f"Pass Rate:       {(self.report.passed_tests/self.report.total_tests*100):.1f}%",
            f"Total Time:      {self.report.total_time_ms:.2f}ms",
        ]
        
        # Calculate avg time
        if self.results:
            times = [r.duration_ms for r in self.results]
            lines.extend([
                "",
                f"Avg Test Time:   {statistics.mean(times):.2f}ms",
                f"Min Test Time:   {min(times):.2f}ms",
                f"Max Test Time:   {max(times):.2f}ms",
            ])
        
        if self.report.failed_tests > 0:
            lines.extend(["", "Failed Tests:"])
            for result in self.results:
                if not result.success:
                    lines.append(f"  ✗ {result.test_path}")
                    if result.error_message:
                        lines.append(f"    {result.error_message[:80]}")
        
        return "\n".join(lines)


# Global validator instance
_validator: Optional[TestValidator] = None


def get_test_validator() -> TestValidator:
    """Get or create validator instance."""
    global _validator
    if _validator is None:
        _validator = TestValidator()
    return _validator


if __name__ == "__main__":
    validator = get_test_validator()
    
    # Example usage
    test_suites = [
        ("python", {"test_dir": "tests"}),
    ]
    
    report = validator.run_tests_parallel(test_suites)
    print(validator.get_report())
