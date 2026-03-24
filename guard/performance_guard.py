"""Enhanced performance monitoring with statistical analysis and trending."""
import json
import time
import statistics
from pathlib import Path
from typing import Dict, Any, Optional, Callable, List
from datetime import datetime
from guard.audit_logger import get_audit_logger, AuditLevel


class PerformanceGuard:
    """
    Monitors performance metrics and detects regressions.
    
    Tracks:
    - Execution times
    - Memory usage (if available)
    - Throughput metrics
    - Regression detection (current vs baseline)
    """
    
    def __init__(self, metrics_dir: str = "guard/.metrics"):
        """
        Initialize performance guard.
        
        Args:
            metrics_dir: Directory to store performance metrics
        """
        self.metrics_dir = Path(metrics_dir)
        self.metrics_dir.mkdir(parents=True, exist_ok=True)
        
        self.logger = get_audit_logger()
        self.baseline_file = self.metrics_dir / "baseline.json"
        self.history_file = self.metrics_dir / "history.jsonl"
        
        self.baseline: Dict[str, float] = self._load_baseline()
        self.current_metrics: Dict[str, Dict[str, Any]] = {}
    
    def _load_baseline(self) -> Dict[str, float]:
        """Load baseline metrics from file."""
        if not self.baseline_file.exists():
            return {}
        
        try:
            with open(self.baseline_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    
    def _save_baseline(self) -> None:
        """Save baseline metrics to file."""
        try:
            with open(self.baseline_file, "w", encoding="utf-8") as f:
                json.dump(self.baseline, f, indent=2)
        except Exception as e:
            self.logger.log(
                AuditLevel.WARNING,
                "performance_guard",
                "baseline_save_failed",
                error=str(e),
            )
    
    def measure(
        self,
        metric_name: str,
        func: Callable,
        *args,
        **kwargs,
    ) -> Any:
        """
        Measure execution time of a function.
        
        Args:
            metric_name: Name of the metric
            func: Function to measure
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Function result
        """
        start_time = time.time()
        
        try:
            result = func(*args, **kwargs)
            elapsed = time.time() - start_time
            
            self.record_metric(metric_name, elapsed)
            
            return result
        
        except Exception as e:
            elapsed = time.time() - start_time
            self.logger.log(
                AuditLevel.WARNING,
                "performance_guard",
                "measure_error",
                details={"metric": metric_name, "elapsed": elapsed},
                error=str(e),
            )
            raise
    
    def record_metric(
        self,
        metric_name: str,
        value: float,
        unit: str = "seconds",
        threshold: Optional[float] = None,
    ) -> None:
        """
        Record a performance metric.
        
        Args:
            metric_name: Name of the metric
            value: Metric value
            unit: Unit of measurement
            threshold: Optional threshold for regression detection
        """
        if metric_name not in self.current_metrics:
            self.current_metrics[metric_name] = {
                "values": [],
                "unit": unit,
                "threshold": threshold,
            }
        
        values = self.current_metrics[metric_name]["values"]
        values.append(value)
        avg_value = sum(values) / len(values)
        
        # Check for regression
        if metric_name in self.baseline:
            baseline = self.baseline[metric_name]
            regression_pct = ((avg_value - baseline) / baseline * 100) if baseline > 0 else 0
            
            if regression_pct > 10:  # 10% regression threshold
                self.logger.log(
                    AuditLevel.WARNING,
                    "performance_guard",
                    "regression_detected",
                    details={
                        "metric": metric_name,
                        "baseline": baseline,
                        "current": avg_value,
                        "regression_pct": regression_pct,
                    },
                    status="warning",
                )
            elif threshold and avg_value > threshold:
                self.logger.log(
                    AuditLevel.WARNING,
                    "performance_guard",
                    "threshold_exceeded",
                    details={
                        "metric": metric_name,
                        "value": avg_value,
                        "threshold": threshold,
                    },
                    status="warning",
                )
        
        # Log to history
        try:
            with open(self.history_file, "a", encoding="utf-8") as f:
                event = {
                    "timestamp": datetime.utcnow().isoformat(),
                    "metric": metric_name,
                    "value": avg_value,
                    "unit": unit,
                }
                f.write(json.dumps(event) + "\\n")
        except Exception as e:
            self.logger.log(
                AuditLevel.DEBUG,
                "performance_guard",
                "history_log_failed",
                error=str(e),
            )
    
    def set_baseline(self, metrics: Dict[str, float]) -> None:
        """
        Set performance baselines.
        
        Args:
            metrics: Dictionary of metric_name -> baseline_value
        """
        self.baseline.update(metrics)
        self._save_baseline()
        
        self.logger.log(
            AuditLevel.INFO,
            "performance_guard",
            "baseline_updated",
            details={"metrics_count": len(metrics)},
        )
    
    def get_current_metrics(self) -> Dict[str, Dict[str, Any]]:
        """Get current metrics with averages."""
        result = {}
        
        for metric_name, data in self.current_metrics.items():
            values = data["values"]
            
            if not values:
                continue
            
            avg = sum(values) / len(values)
            regression = None
            
            if metric_name in self.baseline:
                baseline = self.baseline[metric_name]
                regression = ((avg - baseline) / baseline * 100) if baseline > 0 else 0
            
            result[metric_name] = {
                "average": round(avg, 4),
                "min": round(min(values), 4),
                "max": round(max(values), 4),
                "count": len(values),
                "unit": data["unit"],
                "baseline": self.baseline.get(metric_name),
                "regression_pct": round(regression, 2) if regression else None,
            }
        
        return result
    
    def get_report(self) -> str:
        """
        Generate performance report.
        
        Returns:
            Human-readable performance report
        """
        metrics = self.get_current_metrics()
        
        if not metrics:
            return "No performance metrics recorded"
        
        lines = ["=== PERFORMANCE REPORT ===", ""]
        
        for metric_name, data in sorted(metrics.items()):
            lines.append(f"{metric_name}:")
            lines.append(f"  Average: {data['average']} {data['unit']}")
            lines.append(f"  Min: {data['min']}, Max: {data['max']}")
            lines.append(f"  Samples: {data['count']}")
            
            if data["baseline"] is not None:
                regression = data["regression_pct"]
                status = "✓" if regression < 10 else "⚠" if regression < 20 else "✗"
                lines.append(f"  {status} Baseline: {data['baseline']} ({regression:+.1f}%)")
            
            lines.append("")
        
        return "\\n".join(lines)


# Global performance guard instance
_perf_guard: Optional[PerformanceGuard] = None


def get_performance_guard() -> PerformanceGuard:
    """Get or create global performance guard."""
    global _perf_guard
    if _perf_guard is None:
        _perf_guard = PerformanceGuard()
    return _perf_guard


if __name__ == "__main__":
    guard = get_performance_guard()
    
    # Example: measure some operations
    def slow_operation():
        time.sleep(0.1)
        return "done"
    
    # Record some metrics
    for i in range(3):
        guard.measure("test_operation", slow_operation)
    
    # Set baseline
    guard.set_baseline({"test_operation": 0.1})
    
    print(guard.get_report())
