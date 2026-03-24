"""
Stability Monitoring System

Tracks compression stability metrics and automatically adjusts
compression or triggers rollback if degradation detected.

Key Metrics Tracked:
1. Variance - How much token meaning varies across contexts
2. Failure Rate - % of tokens that fail reconstruction
3. Confidence Score - How confident we are in token quality
4. Anchor Coverage - % of tokens with valid subword anchors
5. Semantic Drift - How much meaning is lost from original

Auto-Adjustment Triggers:
- Variance > 0.4 → Reduce compression
- Failure rate > 0.2 → Reduce compression or rollback
- Confidence < 0.5 → Rollback to previous level
- Semantic similarity < min_accuracy → Rollback
"""

import logging
from typing import List, Dict, Tuple, Optional
from collections import deque
from dataclasses import dataclass, field
from enum import Enum
from advanced_cnf_token.core_structures import (
    CNFToken, CompressionLevel, CompressionMetrics
)

logger = logging.getLogger(__name__)


class StabilityStatus(Enum):
    """Status of compression stability."""
    STABLE = "stable"
    DEGRADING = "degrading"
    UNSTABLE = "unstable"
    CRITICAL = "critical"


@dataclass
class StabilitySnapshot:
    """Snapshot of stability metrics at a point in time."""
    level: CompressionLevel
    timestamp: int
    variance: float
    failure_rate: float
    confidence_mean: float
    anchor_coverage: float
    semantic_similarity: float
    token_count: int
    status: StabilityStatus


class StabilityMonitor:
    """
    Monitors compression stability across runs and levels.
    
    Maintains history of metrics and detects degradation patterns.
    Provides automatic adjustment recommendations.
    """
    
    # Thresholds for different status levels
    VARIANCE_THRESHOLD_WARNING = 0.3
    VARIANCE_THRESHOLD_CRITICAL = 0.5
    
    FAILURE_RATE_THRESHOLD_WARNING = 0.1
    FAILURE_RATE_THRESHOLD_CRITICAL = 0.25
    
    CONFIDENCE_THRESHOLD_WARNING = 0.6
    CONFIDENCE_THRESHOLD_CRITICAL = 0.4
    
    ANCHOR_COVERAGE_THRESHOLD_WARNING = 0.7
    ANCHOR_COVERAGE_THRESHOLD_CRITICAL = 0.5
    
    SEMANTIC_SIMILARITY_THRESHOLD_WARNING = 0.92
    SEMANTIC_SIMILARITY_THRESHOLD_CRITICAL = 0.90
    
    def __init__(self, window_size: int = 10):
        """
        Initialize monitor.
        
        Args:
            window_size: Number of recent snapshots to keep
        """
        self.window_size = window_size
        self.snapshots: deque = deque(maxlen=window_size)
        self.adjustment_history: List[Tuple[CompressionLevel, str]] = []
    
    def record_snapshot(
        self,
        level: CompressionLevel,
        metrics: CompressionMetrics,
        tokens: List[CNFToken],
        timestamp: int = None
    ) -> StabilityStatus:
        """
        Record a stability snapshot.
        
        Args:
            level: Compression level
            metrics: Compression metrics
            tokens: Compressed tokens
            timestamp: Optional timestamp (default: auto-increment)
        
        Returns:
            Current stability status
        """
        
        if timestamp is None:
            timestamp = len(self.snapshots)
        
        # Determine status
        status = self._determine_status(metrics)
        
        # Create snapshot
        snapshot = StabilitySnapshot(
            level=level,
            timestamp=timestamp,
            variance=metrics.variance,
            failure_rate=metrics.failure_rate,
            confidence_mean=metrics.confidence_mean,
            anchor_coverage=metrics.anchor_coverage,
            semantic_similarity=metrics.semantic_similarity,
            token_count=len(tokens),
            status=status,
        )
        
        self.snapshots.append(snapshot)
        
        logger.info(f"Stability snapshot: {level.name} - {status.value} "
                   f"(variance={metrics.variance:.2f}, failure_rate={metrics.failure_rate:.1%})")
        
        return status
    
    def _determine_status(self, metrics: CompressionMetrics) -> StabilityStatus:
        """Determine status from metrics."""
        
        critical_indicators = [
            metrics.variance > self.VARIANCE_THRESHOLD_CRITICAL,
            metrics.failure_rate > self.FAILURE_RATE_THRESHOLD_CRITICAL,
            metrics.confidence_mean < self.CONFIDENCE_THRESHOLD_CRITICAL,
            metrics.anchor_coverage < self.ANCHOR_COVERAGE_THRESHOLD_CRITICAL,
            metrics.semantic_similarity < self.SEMANTIC_SIMILARITY_THRESHOLD_CRITICAL,
        ]
        
        warning_indicators = [
            metrics.variance > self.VARIANCE_THRESHOLD_WARNING,
            metrics.failure_rate > self.FAILURE_RATE_THRESHOLD_WARNING,
            metrics.confidence_mean < self.CONFIDENCE_THRESHOLD_WARNING,
            metrics.anchor_coverage < self.ANCHOR_COVERAGE_THRESHOLD_WARNING,
            metrics.semantic_similarity < self.SEMANTIC_SIMILARITY_THRESHOLD_WARNING,
        ]
        
        if sum(critical_indicators) >= 2:
            return StabilityStatus.CRITICAL
        elif any(critical_indicators):
            return StabilityStatus.UNSTABLE
        elif sum(warning_indicators) >= 2:
            return StabilityStatus.DEGRADING
        else:
            return StabilityStatus.STABLE
    
    def get_adjustment_recommendation(
        self,
        current_level: CompressionLevel
    ) -> Tuple[Optional[CompressionLevel], List[str]]:
        """
        Get adjustment recommendation based on stability history.
        
        Returns:
            (recommended_level, reasons)
        
        Strategy:
        - If recent status is CRITICAL → rollback 2 levels
        - If recent status is UNSTABLE → rollback 1 level
        - If recent status is DEGRADING → monitor closely
        - If recent status is STABLE → can try higher compression
        """
        
        if not self.snapshots:
            return None, ["No stability history yet"]
        
        recent = list(self.snapshots)[-3:]  # Last 3 snapshots
        recent_status = [s.status for s in recent]
        
        reasons = []
        adjusted_level = current_level
        
        # Check for degradation pattern
        critical_count = sum(1 for s in recent_status if s == StabilityStatus.CRITICAL)
        unstable_count = sum(1 for s in recent_status if s == StabilityStatus.UNSTABLE)
        degrading_count = sum(1 for s in recent_status if s == StabilityStatus.DEGRADING)
        
        if critical_count >= 1:
            adjusted_level = self._reduce_level(adjusted_level, 2)
            reasons.append(f"Critical stability detected ({critical_count} snapshots)")
        
        if unstable_count >= 2:
            adjusted_level = self._reduce_level(adjusted_level, 1)
            reasons.append(f"Unstable compression ({unstable_count} snapshots)")
        
        if degrading_count >= 3:
            adjusted_level = self._reduce_level(adjusted_level, 1)
            reasons.append(f"Degrading trend detected ({degrading_count} snapshots)")
        
        # Check for improvement to suggest higher compression
        if all(s == StabilityStatus.STABLE for s in recent_status):
            reasons.append("Compression is stable - consider higher level")
        
        if adjusted_level != current_level:
            self.adjustment_history.append((adjusted_level, ", ".join(reasons)))
        
        return adjusted_level if adjusted_level != current_level else None, reasons
    
    def _reduce_level(self, level: CompressionLevel, steps: int = 1) -> CompressionLevel:
        """Reduce compression level by N steps."""
        
        for _ in range(steps):
            if level == CompressionLevel.LEVEL_4:
                level = CompressionLevel.LEVEL_3
            elif level == CompressionLevel.LEVEL_3:
                level = CompressionLevel.LEVEL_2
            elif level == CompressionLevel.LEVEL_2:
                level = CompressionLevel.LEVEL_1
            else:
                break  # Floor at LEVEL_1
        
        return level
    
    def get_risk_assessment(self) -> Dict[str, any]:
        """
        Get overall risk assessment from history.
        
        Returns:
            {
                "current_risk": str,
                "trend": str,
                "recommendations": [str],
                "metrics_summary": {...},
            }
        """
        
        if not self.snapshots:
            return {
                "current_risk": "UNKNOWN",
                "trend": "No data",
                "recommendations": ["Collect baseline metrics"],
                "metrics_summary": None,
            }
        
        recent = list(self.snapshots)[-5:]
        recent_status = [s.status for s in recent]
        
        # Determine current risk
        current_status = recent_status[-1] if recent_status else StabilityStatus.STABLE
        risk_map = {
            StabilityStatus.STABLE: "LOW",
            StabilityStatus.DEGRADING: "MEDIUM",
            StabilityStatus.UNSTABLE: "HIGH",
            StabilityStatus.CRITICAL: "CRITICAL",
        }
        current_risk = risk_map[current_status]
        
        # Determine trend
        status_counts = {
            StabilityStatus.STABLE: sum(1 for s in recent_status if s == StabilityStatus.STABLE),
            StabilityStatus.DEGRADING: sum(1 for s in recent_status if s == StabilityStatus.DEGRADING),
            StabilityStatus.UNSTABLE: sum(1 for s in recent_status if s == StabilityStatus.UNSTABLE),
            StabilityStatus.CRITICAL: sum(1 for s in recent_status if s == StabilityStatus.CRITICAL),
        }
        
        if status_counts[StabilityStatus.CRITICAL] > 0:
            trend = "Deteriorating - Critical issues detected"
        elif status_counts[StabilityStatus.UNSTABLE] >= 2:
            trend = "Worsening - Multiple unstable compressions"
        elif status_counts[StabilityStatus.DEGRADING] >= 2:
            trend = "Mixed - Some degradation signs"
        elif status_counts[StabilityStatus.STABLE] == len(recent_status):
            trend = "Stable - All recent compressions successful"
        else:
            trend = "Improving - Recent improvements detected"
        
        # Recommendations
        recommendations = []
        if current_risk == "CRITICAL":
            recommendations.append("URGENT: Rollback to LEVEL_1")
        elif current_risk == "HIGH":
            recommendations.append("Reduce compression level")
        elif current_risk == "MEDIUM":
            recommendations.append("Monitor closely, consider reducing level")
            recommendations.append("Review token confidence and variance")
        else:  # LOW
            if trend == "Stable - All recent compressions successful":
                recommendations.append("Compression is stable - can consider higher level")
            recommendations.append("Continue monitoring")
        
        # Metrics summary
        latest = recent[-1]
        metrics_summary = {
            "variance": latest.variance,
            "failure_rate": latest.failure_rate,
            "confidence_mean": latest.confidence_mean,
            "anchor_coverage": latest.anchor_coverage,
            "semantic_similarity": latest.semantic_similarity,
            "token_count": latest.token_count,
        }
        
        return {
            "current_risk": current_risk,
            "trend": trend,
            "recommendations": recommendations,
            "metrics_summary": metrics_summary,
            "status_counts": {k.value: v for k, v in status_counts.items()},
        }
    
    def report_snapshot_history(self) -> str:
        """Generate human-readable report of snapshot history."""
        
        if not self.snapshots:
            return "No stability snapshots recorded"
        
        report = "Stability Monitor Report:\n"
        report += "=" * 80 + "\n"
        report += f"{'Time':>5} {'Level':>8} {'Status':>10}\n"
        report += "-" * 80 + "\n"
        
        for snapshot in self.snapshots:
            status_str = snapshot.status.value.upper()
            report += f"{snapshot.timestamp:>5} {snapshot.level.name:>8} {status_str:>10}\n"
        
        report += "-" * 80 + "\n"
        
        # Summary
        risk_assessment = self.get_risk_assessment()
        report += f"Current Risk Level: {risk_assessment['current_risk']}\n"
        report += f"Trend: {risk_assessment['trend']}\n"
        report += "\nRecommendations:\n"
        for rec in risk_assessment['recommendations']:
            report += f"  - {rec}\n"
        
        report += "\nLatest Metrics:\n"
        for key, value in risk_assessment['metrics_summary'].items():
            if isinstance(value, float):
                report += f"  {key}: {value:.3f}\n"
            else:
                report += f"  {key}: {value}\n"
        
        return report


class FailureDetector:
    """Detects and tracks reconstruction failures."""
    
    def __init__(self):
        self.failures: List[Tuple[int, str, str]] = []  # (timestamp, token_id, reason)
        self.failure_patterns: Dict[str, int] = {}
    
    def record_failure(
        self,
        token_id: int,
        reason: str,
        timestamp: int = None
    ) -> None:
        """Record a reconstruction failure."""
        
        if timestamp is None:
            timestamp = len(self.failures)
        
        self.failures.append((timestamp, token_id, reason))
        
        # Track pattern
        pattern_key = f"{token_id}:{reason}"
        self.failure_patterns[pattern_key] = self.failure_patterns.get(pattern_key, 0) + 1
        
        logger.warning(f"Reconstruction failure: token {token_id} - {reason}")
    
    def get_failure_report(self) -> Dict[str, any]:
        """Get failure analysis report."""
        
        if not self.failures:
            return {
                "total_failures": 0,
                "pattern_analysis": {},
                "recommendations": ["No failures detected"],
            }
        
        # Find most common patterns
        top_patterns = sorted(
            self.failure_patterns.items(),
            key=lambda x: x[1],
            reverse=True
        )[:5]
        
        pattern_analysis = {
            pattern: count
            for pattern, count in top_patterns
        }
        
        recommendations = []
        if len(self.failures) > 5:
            most_common = top_patterns[0] if top_patterns else ("unknown", 0)
            recommendations.append(f"Most common failure: {most_common[0]} ({most_common[1]} times)")
            recommendations.append("Review token anchor selection for failing tokens")
        
        return {
            "total_failures": len(self.failures),
            "pattern_analysis": pattern_analysis,
            "recommendations": recommendations,
        }
