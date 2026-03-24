"""Enhanced token drift validation with history and trend detection."""
import json
from pathlib import Path
from typing import Optional, Dict, List, Tuple
from datetime import datetime
from enum import Enum
from guard.failure import fail_hard
from guard.audit_logger import get_audit_logger, AuditLevel

DRIFT_HISTORY_FILE = 'guard/.token_drift_history.jsonl'


class DriftLevel(Enum):
    """Token drift severity levels."""
    NORMAL = "normal"      # < 5%
    WARNING = "warning"    # 5-10%
    CRITICAL = "critical"  # > 10%


class TokenDriftValidator:
    """
    Enhanced token drift validator with statistical analysis.
    
    Features:
    - Drift percentage calculation
    - History tracking with timestamps
    - Trend detection
    - Statistical analysis (mean, std dev, direction)
    - Auto-threshold adjustment
    - Risk assessment
    """
    
    def __init__(self):
        """Initialize validator."""
        self.logger = get_audit_logger()
        self.history: List[Dict] = self._load_history()
        self.recent_drifts: List[float] = []
    
    def _load_history(self) -> List[Dict]:
        """Load drift history from file."""
        if not Path(DRIFT_HISTORY_FILE).exists():
            return []
        
        try:
            history = []
            with open(DRIFT_HISTORY_FILE, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        history.append(json.loads(line))
            return history
        except Exception:
            return []
    
    def _save_history(self) -> None:
        """Save drift history to file."""
        try:
            Path(DRIFT_HISTORY_FILE).parent.mkdir(parents=True, exist_ok=True)
            with open(DRIFT_HISTORY_FILE, 'w', encoding='utf-8') as f:
                for entry in self.history:
                    f.write(json.dumps(entry) + '\n')
        except Exception as e:
            self.logger.log(
                AuditLevel.WARNING,
                "token_drift",
                "history_save_failed",
                error=str(e),
            )
    
    def compute_drift(self, prev: float, current: float) -> float:
        """
        Compute token drift percentage.
        
        Args:
            prev: Previous token count
            current: Current token count
            
        Returns:
            Drift as percentage (0-100)
        """
        if prev <= 0:
            fail_hard(
                "Invalid previous token count for drift detection",
                component="token_drift",
                details={"prev": prev, "current": current},
            )
        
        drift = abs(current - prev) / prev * 100
        return round(drift, 2)
    
    def get_drift_level(self, drift_percentage: float) -> DriftLevel:
        """
        Get drift severity level.
        
        Args:
            drift_percentage: Drift as percentage
            
        Returns:
            DriftLevel enum
        """
        if drift_percentage < 5:
            return DriftLevel.NORMAL
        elif drift_percentage <= 10:
            return DriftLevel.WARNING
        else:
            return DriftLevel.CRITICAL
    
    def validate_token_drift(
        self,
        prev: float,
        current: float,
        threshold: float = 10.0,
        auto_threshold: bool = False,
    ) -> bool:
        """
        Validate token drift against threshold.
        
        Args:
            prev: Previous token count
            current: Current token count
            threshold: Drift threshold percentage
            auto_threshold: Auto-adjust threshold based on history
            
        Returns:
            True if drift is acceptable, raises otherwise
        """
        drift = self.compute_drift(float(prev), float(current))
        direction = "increase" if current > prev else "decrease"
        
        # Auto-adjust threshold if enabled
        if auto_threshold and len(self.history) >= 10:
            adjusted_threshold = self._calculate_adaptive_threshold()
            self.logger.log(
                AuditLevel.INFO,
                "token_drift",
                "threshold_adjusted",
                details={
                    "original_threshold": threshold,
                    "adjusted_threshold": adjusted_threshold,
                },
            )
            threshold = adjusted_threshold
        
        # Record drift
        drift_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'prev': prev,
            'current': current,
            'drift': drift,
            'direction': direction,
            'level': self.get_drift_level(drift).value,
            'threshold': threshold,
        }
        self.history.append(drift_entry)
        self.recent_drifts.append(drift)
        if len(self.recent_drifts) > 100:
            self.recent_drifts.pop(0)
        
        self._save_history()
        
        # Check if drift exceeds threshold
        if drift > threshold:
            # Check for trend
            trend = self._detect_trend()
            
            self.logger.log(
                AuditLevel.WARNING,
                "token_drift",
                "drift_detected",
                details={
                    "drift": drift,
                    "threshold": threshold,
                    "direction": direction,
                    "trend": trend,
                    "prev": prev,
                    "current": current,
                },
                status="failure",
                error=f"Token drift too high: {drift:.2f}% > {threshold}%",
            )
            
            fail_hard(
                f"Token drift too high: {drift:.2f}% > {threshold}%",
                component="token_drift",
                details={
                    "drift": drift,
                    "threshold": threshold,
                    "direction": direction,
                    "trend": trend,
                },
            )
        
        self.logger.log(
            AuditLevel.INFO,
            "token_drift",
            "drift_validated",
            details={
                "drift": drift,
                "threshold": threshold,
                "level": self.get_drift_level(drift).value,
            },
            status="success",
        )
        
        return True
    
    def _detect_trend(self) -> str:
        """Detect if there's an upward or downward trend."""
        if len(self.recent_drifts) < 3:
            return "insufficient_data"
        
        recent = self.recent_drifts[-5:] if len(self.recent_drifts) >= 5 else self.recent_drifts
        avg_recent = sum(recent) / len(recent)
        
        older = self.recent_drifts[:-5] if len(self.recent_drifts) >= 10 else []
        if older:
            avg_older = sum(older[-5:]) / min(5, len(older))
            
            if avg_recent > avg_older * 1.1:
                return "upward_trend"
            elif avg_recent < avg_older * 0.9:
                return "downward_trend"
        
        return "stable"
    
    def _calculate_adaptive_threshold(self) -> float:
        """
        Calculate adaptive threshold based on historical drift.
        
        Returns:
            Suggested threshold percentage
        """
        if not self.recent_drifts:
            return 10.0
        
        import statistics
        
        avg_drift = statistics.mean(self.recent_drifts)
        std_drift = statistics.stdev(self.recent_drifts) if len(self.recent_drifts) > 1 else 0
        
        # Threshold = mean + 2*std_dev (allows normal variation)
        suggested = avg_drift + (2 * std_drift)
        
        # Keep within reasonable bounds
        return max(5.0, min(20.0, suggested))
    
    def get_statistics(self) -> Dict:
        """
        Get drift statistics.
        
        Returns:
            Dictionary with drift statistics
        """
        if not self.recent_drifts:
            return {
                'total_measurements': 0,
                'average_drift': 0,
                'min_drift': 0,
                'max_drift': 0,
                'trend': 'no_data',
            }
        
        import statistics
        
        return {
            'total_measurements': len(self.history),
            'recent_measurements': len(self.recent_drifts),
            'average_drift': round(statistics.mean(self.recent_drifts), 2),
            'min_drift': round(min(self.recent_drifts), 2),
            'max_drift': round(max(self.recent_drifts), 2),
            'std_dev': round(statistics.stdev(self.recent_drifts), 2) if len(self.recent_drifts) > 1 else 0,
            'trend': self._detect_trend(),
            'adaptive_threshold': round(self._calculate_adaptive_threshold(), 2),
        }
    
    def get_report(self) -> str:
        """Get drift analysis report."""
        stats = self.get_statistics()
        
        lines = [
            "=== TOKEN DRIFT ANALYSIS ===",
            "",
            f"Total Measurements: {stats['total_measurements']}",
            f"Recent (last 100):  {stats['recent_measurements']}",
            "",
            f"Average Drift:      {stats['average_drift']:.2f}%",
            f"Min Drift:          {stats['min_drift']:.2f}%",
            f"Max Drift:          {stats['max_drift']:.2f}%",
            f"Std Dev:            {stats['std_dev']:.2f}%",
            "",
            f"Trend:              {stats['trend'].replace('_', ' ').title()}",
            f"Adaptive Threshold: {stats['adaptive_threshold']:.2f}%",
        ]
        
        return "\n".join(lines)


# Global validator instance
_validator: Optional[TokenDriftValidator] = None


def get_validator() -> TokenDriftValidator:
    """Get or create validator instance."""
    global _validator
    if _validator is None:
        _validator = TokenDriftValidator()
    return _validator


def compute_token_drift(prev, current):
    """Compute token drift."""
    return get_validator().compute_drift(prev, current)


def validate_token_drift(prev, current, threshold=10.0, auto_threshold=False):
    """Validate token drift."""
    return get_validator().validate_token_drift(prev, current, threshold, auto_threshold)


if __name__ == '__main__':
    validator = get_validator()
    
    # Test validation
    validator.validate_token_drift(1000, 1050, threshold=10.0)
    print('✓ Token drift validation passed')
    
    # Show report
    print()
    print(validator.get_report())
