"""Centralized audit logging with search, filtering and analytics."""
import logging
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
from enum import Enum
from typing import Any, Optional, Dict, List, Callable
import re


class AuditLevel(Enum):
    """Audit log severity levels."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"
    FAILURE = "FAILURE"


class AuditLogger:
    """
    Enhanced audit trail for guard operations.
    
    Features:
    - Structured JSONL logging
    - Search and filtering
    - Batch operations
    - Analytics and summaries
    - Event correlation
    - Time-based queries
    """
    
    def __init__(self, log_dir: str = "guard/.logs"):
        """Initialize audit logger."""
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        self.audit_file = self.log_dir / "audit.jsonl"
        self.summary_file = self.log_dir / "summary.log"
        self.events: List[Dict[str, Any]] = []
        
        # Setup Python logging
        self.logger = logging.getLogger("guard")
        self.logger.setLevel(logging.DEBUG)
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stderr)
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter(
            "%(asctime)s [%(levelname)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        console_handler.setFormatter(console_formatter)
        self.logger.addHandler(console_handler)
        
        # Load existing events
        self._load_events()
    
    def _load_events(self) -> None:
        """Load events from audit file."""
        if not self.audit_file.exists():
            return
        
        try:
            with open(self.audit_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        self.events.append(json.loads(line))
        except Exception:
            pass
    
    def log(
        self,
        level: AuditLevel,
        component: str,
        action: str,
        details: Optional[Dict[str, Any]] = None,
        status: str = "success",
        error: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Log an audit event."""
        event = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": level.value,
            "component": component,
            "action": action,
            "status": status,
            "details": details or {},
            "error": error,
        }
        
        self.events.append(event)
        
        # Write to audit file
        try:
            with open(self.audit_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(event) + "\n")
        except Exception:
            pass
        
        # Console output
        msg = f"[{component}] {action} - {status.upper()}"
        if error:
            msg += f": {error}"
        
        if level == AuditLevel.CRITICAL or level == AuditLevel.FAILURE:
            self.logger.critical(msg)
        elif level == AuditLevel.WARNING:
            self.logger.warning(msg)
        elif level == AuditLevel.INFO:
            self.logger.info(msg)
        else:
            self.logger.debug(msg)
        
        return event
    
    def log_validation(
        self,
        component: str,
        checks: List[tuple],
        details: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Log validation results."""
        passed = sum(1 for _, p in checks if p)
        total = len(checks)
        all_passed = passed == total
        
        check_details = {
            "checks": [{"name": name, "passed": p} for name, p in checks],
            "passed": passed,
            "total": total,
            "percentage": (passed / total * 100) if total > 0 else 0,
            **(details or {})
        }
        
        level = AuditLevel.INFO if all_passed else AuditLevel.WARNING
        status = "success" if all_passed else "partial_failure"
        
        self.log(
            level=level,
            component=component,
            action="validation_completed",
            details=check_details,
            status=status,
        )
        
        return all_passed
    
    def log_checkpoint(
        self,
        checkpoint_id: str,
        data: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Log a checkpoint for rollback."""
        checkpoint_file = self.log_dir / f"checkpoint_{checkpoint_id}.json"
        
        checkpoint = {
            "id": checkpoint_id,
            "timestamp": datetime.utcnow().isoformat(),
            "data": data,
            "metadata": metadata or {},
        }
        
        try:
            with open(checkpoint_file, "w", encoding="utf-8") as f:
                json.dump(checkpoint, f, indent=2)
        except Exception:
            pass
        
        self.log(
            level=AuditLevel.INFO,
            component="state_manager",
            action="checkpoint_created",
            details={"checkpoint_id": checkpoint_id},
            status="success",
        )
    
    # === SEARCH AND FILTERING ===
    
    def search(
        self,
        pattern: str,
        field: str = "action",
        use_regex: bool = False,
    ) -> List[Dict[str, Any]]:
        """
        Search events by pattern.
        
        Args:
            pattern: Search pattern
            field: Field to search (action, component, error, etc.)
            use_regex: Use regex matching
            
        Returns:
            Matching events
        """
        results = []
        
        for event in self.events:
            value = str(event.get(field, ""))
            
            if use_regex:
                if re.search(pattern, value):
                    results.append(event)
            else:
                if pattern.lower() in value.lower():
                    results.append(event)
        
        return results
    
    def filter_by_level(self, level: AuditLevel) -> List[Dict[str, Any]]:
        """Filter events by severity level."""
        return [e for e in self.events if e.get("level") == level.value]
    
    def filter_by_component(self, component: str) -> List[Dict[str, Any]]:
        """Filter events by component."""
        return [e for e in self.events if e.get("component") == component]
    
    def filter_by_status(self, status: str) -> List[Dict[str, Any]]:
        """Filter events by status."""
        return [e for e in self.events if e.get("status") == status]
    
    def filter_by_time(
        self,
        since_minutes: Optional[int] = None,
        until_minutes: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Filter events by timestamp."""
        now = datetime.utcnow()
        results = []
        
        for event in self.events:
            try:
                ts = datetime.fromisoformat(event.get("timestamp", ""))
                
                if since_minutes and (now - ts).total_seconds() > since_minutes * 60:
                    continue
                
                if until_minutes and (now - ts).total_seconds() < until_minutes * 60:
                    continue
                
                results.append(event)
            except ValueError:
                pass
        
        return results
    
    def filter(self, predicate: Callable) -> List[Dict[str, Any]]:
        """Filter events with custom predicate."""
        return [e for e in self.events if predicate(e)]
    
    # === BATCH OPERATIONS ===
    
    def log_batch(self, events: List[Dict[str, Any]]) -> int:
        """
        Log multiple events efficiently.
        
        Args:
            events: List of event data dicts
            
        Returns:
            Number of events logged
        """
        count = 0
        
        try:
            with open(self.audit_file, "a", encoding="utf-8") as f:
                for event_data in events:
                    event = {
                        "timestamp": datetime.utcnow().isoformat(),
                        "level": event_data.get("level", AuditLevel.INFO.value),
                        "component": event_data.get("component", "unknown"),
                        "action": event_data.get("action", ""),
                        "status": event_data.get("status", "success"),
                        "details": event_data.get("details", {}),
                        "error": event_data.get("error"),
                    }
                    
                    self.events.append(event)
                    f.write(json.dumps(event) + "\n")
                    count += 1
        except Exception:
            pass
        
        return count
    
    def clear_old_events(self, days: int = 30) -> int:
        """
        Remove events older than specified days.
        
        Args:
            days: Age in days
            
        Returns:
            Number of removed events
        """
        cutoff = datetime.utcnow() - timedelta(days=days)
        initial_count = len(self.events)
        
        self.events = [
            e for e in self.events
            if datetime.fromisoformat(e.get("timestamp", "")) > cutoff
        ]
        
        removed = initial_count - len(self.events)
        
        # Rewrite audit file
        try:
            with open(self.audit_file, "w", encoding="utf-8") as f:
                for event in self.events:
                    f.write(json.dumps(event) + "\n")
        except Exception:
            pass
        
        return removed
    
    # === ANALYTICS ===
    
    def get_summary(self) -> Dict[str, Any]:
        """Get summary of all audit events."""
        if not self.events:
            return {"total_events": 0, "by_level": {}, "by_component": {}}
        
        by_level: Dict[str, int] = {}
        by_component: Dict[str, int] = {}
        by_status: Dict[str, int] = {}
        error_count = 0
        
        for event in self.events:
            level = event.get("level", "UNKNOWN")
            component = event.get("component", "UNKNOWN")
            status = event.get("status", "UNKNOWN")
            
            by_level[level] = by_level.get(level, 0) + 1
            by_component[component] = by_component.get(component, 0) + 1
            by_status[status] = by_status.get(status, 0) + 1
            
            if event.get("error"):
                error_count += 1
        
        return {
            "total_events": len(self.events),
            "error_count": error_count,
            "by_level": by_level,
            "by_component": by_component,
            "by_status": by_status,
            "first_event": self.events[0].get("timestamp") if self.events else None,
            "last_event": self.events[-1].get("timestamp") if self.events else None,
        }
    
    def get_component_stats(self, component: str) -> Dict[str, Any]:
        """Get statistics for a specific component."""
        events = self.filter_by_component(component)
        
        if not events:
            return {"component": component, "events": 0}
        
        levels = {}
        statuses = {}
        
        for event in events:
            level = event.get("level", "UNKNOWN")
            status = event.get("status", "UNKNOWN")
            
            levels[level] = levels.get(level, 0) + 1
            statuses[status] = statuses.get(status, 0) + 1
        
        return {
            "component": component,
            "events": len(events),
            "by_level": levels,
            "by_status": statuses,
        }
    
    def write_summary(self) -> None:
        """Write audit summary to file."""
        summary = self.get_summary()
        
        try:
            with open(self.summary_file, "w", encoding="utf-8") as f:
                f.write("=== GUARD AUDIT SUMMARY ===\n\n")
                f.write(json.dumps(summary, indent=2))
                f.write("\n\n=== RECENT EVENTS ===\n")
                
                for event in self.events[-50:]:
                    f.write(f"[{event['timestamp']}] {event['component']}: {event['action']}\n")
        except Exception:
            pass


# Global audit logger instance
_audit_logger: Optional[AuditLogger] = None


def get_audit_logger() -> AuditLogger:
    """Get or create the global audit logger."""
    global _audit_logger
    if _audit_logger is None:
        _audit_logger = AuditLogger()
    return _audit_logger


if __name__ == "__main__":
    logger = get_audit_logger()
    logger.log(
        AuditLevel.INFO,
        "test_component",
        "test_action",
        details={"test": True},
    )
    print("\nAudit Summary:")
    print(json.dumps(logger.get_summary(), indent=2))
    logger.write_summary()
    print("Audit log written to guard/.logs/")


# Global audit logger instance
_audit_logger: Optional[AuditLogger] = None


def get_audit_logger() -> AuditLogger:
    """Get or create the global audit logger."""
    global _audit_logger
    if _audit_logger is None:
        _audit_logger = AuditLogger()
    return _audit_logger


if __name__ == "__main__":
    logger = get_audit_logger()
    logger.log(
        AuditLevel.INFO,
        "test_component",
        "test_action",
        details={"test": True},
    )
    print("\nAudit Summary:")
    print(json.dumps(logger.get_summary(), indent=2))
    logger.write_summary()
    print("Audit log written to guard/.logs/")
