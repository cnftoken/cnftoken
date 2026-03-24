"""Enhanced state management with validation, recovery and snapshots."""
import json
import hashlib
from pathlib import Path
from typing import Any, Dict, Optional, List, Callable, Tuple
from datetime import datetime
from dataclasses import dataclass
from guard.audit_logger import get_audit_logger, AuditLevel


@dataclass
class StateSnapshot:
    """A snapshot of system state."""
    id: str
    timestamp: str
    state: Dict[str, Any]
    hash: str
    metadata: Dict[str, Any]
    validation_status: str = "unknown"


class StateManager:
    """
    Enhanced state manager with validation and recovery.
    
    Features:
    - State snapshots and checkpoints
    - Rollback with validation
    - State transition tracking
    - Recovery mechanisms
    - Consistency checking
    - Snapshot comparison
    """
    
    def __init__(self, state_dir: str = "guard/.state"):
        """Initialize state manager."""
        self.state_dir = Path(state_dir)
        self.state_dir.mkdir(parents=True, exist_ok=True)
        
        self.current_state_file = self.state_dir / "current_state.json"
        self.state_history_file = self.state_dir / "state_history.jsonl"
        self.logger = get_audit_logger()
        
        self._state: Dict[str, Any] = {}
        self._validators: Dict[str, Callable] = {}
        self._snapshots: Dict[str, StateSnapshot] = {}
        
        self._load_current_state()
    
    def _load_current_state(self) -> None:
        """Load current state from file."""
        if self.current_state_file.exists():
            try:
                with open(self.current_state_file, "r", encoding="utf-8") as f:
                    self._state = json.load(f)
            except Exception as e:
                self.logger.log(
                    AuditLevel.WARNING,
                    "state_manager",
                    "state_load_failed",
                    status="failure",
                    error=str(e),
                )
                self._state = {}
    
    def _save_current_state(self) -> None:
        """Save current state to file."""
        try:
            with open(self.current_state_file, "w", encoding="utf-8") as f:
                json.dump(self._state, f, indent=2)
        except Exception as e:
            self.logger.log(
                AuditLevel.CRITICAL,
                "state_manager",
                "state_save_failed",
                status="failure",
                error=str(e),
            )
            raise
    
    def register_validator(
        self,
        key: str,
        validator: Callable[[Any], bool],
    ) -> None:
        """
        Register a validator for state values.
        
        Args:
            key: State key to validate
            validator: Callable that returns True if valid
        """
        self._validators[key] = validator
    
    def _validate_state(self, state: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate state against registered validators."""
        errors = []
        
        for key, validator in self._validators.items():
            if key in state:
                try:
                    if not validator(state[key]):
                        errors.append(f"Validation failed for key: {key}")
                except Exception as e:
                    errors.append(f"Validation exception for {key}: {str(e)}")
        
        return len(errors) == 0, errors
    
    def set(self, key: str, value: Any, validate: bool = True) -> bool:
        """
        Set a state value with optional validation.
        
        Args:
            key: State key
            value: State value
            validate: Whether to validate
            
        Returns:
            True if set successfully
        """
        if validate and key in self._validators:
            try:
                if not self._validators[key](value):
                    self.logger.log(
                        AuditLevel.WARNING,
                        "state_manager",
                        "validation_failed",
                        details={"key": key},
                    )
                    return False
            except Exception as e:
                self.logger.log(
                    AuditLevel.WARNING,
                    "state_manager",
                    "validation_exception",
                    details={"key": key},
                    error=str(e),
                )
                return False
        
        self._state[key] = value
        self._save_current_state()
        
        self.logger.log(
            AuditLevel.DEBUG,
            "state_manager",
            "state_set",
            details={"key": key}
        )
        
        return True
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a state value."""
        return self._state.get(key, default)
    
    def update(self, data: Dict[str, Any], validate: bool = True) -> bool:
        """Update multiple state values."""
        if validate:
            is_valid, errors = self._validate_state(data)
            if not is_valid:
                self.logger.log(
                    AuditLevel.WARNING,
                    "state_manager",
                    "bulk_update_validation_failed",
                    details={"errors": errors[:5]},
                )
                return False
        
        self._state.update(data)
        self._save_current_state()
        
        self.logger.log(
            AuditLevel.DEBUG,
            "state_manager",
            "state_updated",
            details={"keys": list(data.keys())}
        )
        
        return True
    
    def get_all(self) -> Dict[str, Any]:
        """Get entire current state."""
        return dict(self._state)
    
    def create_checkpoint(
        self,
        checkpoint_id: str,
        snapshot: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[str]:
        """
        Create a checkpoint with validation.
        
        Args:
            checkpoint_id: Unique checkpoint identifier
            snapshot: Specific state to checkpoint
            metadata: Additional metadata
            
        Returns:
            Checkpoint hash or None if validation fails
        """
        if snapshot is None:
            snapshot = dict(self._state)
        
        # Validate snapshot
        is_valid, errors = self._validate_state(snapshot)
        
        checkpoint_data = {
            "id": checkpoint_id,
            "timestamp": datetime.utcnow().isoformat(),
            "snapshot": snapshot,
            "metadata": metadata or {},
            "validation_status": "valid" if is_valid else "invalid",
            "validation_errors": errors if errors else [],
        }
        
        # Compute checkpoint hash
        checkpoint_json = json.dumps(checkpoint_data, sort_keys=True)
        checkpoint_hash = hashlib.sha256(checkpoint_json.encode()).hexdigest()
        checkpoint_data["hash"] = checkpoint_hash
        
        # Save checkpoint
        checkpoint_file = self.state_dir / f"checkpoint_{checkpoint_id}.json"
        try:
            with open(checkpoint_file, "w", encoding="utf-8") as f:
                json.dump(checkpoint_data, f, indent=2)
        except Exception as e:
            self.logger.log(
                AuditLevel.CRITICAL,
                "state_manager",
                "checkpoint_save_failed",
                details={"checkpoint_id": checkpoint_id},
                error=str(e),
            )
            return None
        
        # Log to history
        try:
            with open(self.state_history_file, "a", encoding="utf-8") as f:
                f.write(json.dumps({
                    "event": "checkpoint_created",
                    "timestamp": datetime.utcnow().isoformat(),
                    "checkpoint_id": checkpoint_id,
                    "checkpoint_hash": checkpoint_hash,
                    "validation_status": checkpoint_data["validation_status"],
                }) + "\n")
        except Exception:
            pass
        
        # Store snapshot
        self._snapshots[checkpoint_id] = StateSnapshot(
            id=checkpoint_id,
            timestamp=checkpoint_data["timestamp"],
            state=snapshot,
            hash=checkpoint_hash,
            metadata=checkpoint_data["metadata"],
            validation_status=checkpoint_data["validation_status"],
        )
        
        self.logger.log(
            AuditLevel.INFO,
            "state_manager",
            "checkpoint_created",
            details={
                "checkpoint_id": checkpoint_id,
                "hash": checkpoint_hash[:8],
                "valid": is_valid,
            },
        )
        
        return checkpoint_hash
    
    def list_checkpoints(self) -> List[str]:
        """List all available checkpoints."""
        checkpoints = []
        for file in self.state_dir.glob("checkpoint_*.json"):
            checkpoint_id = file.stem.replace("checkpoint_", "")
            checkpoints.append(checkpoint_id)
        return sorted(checkpoints)
    
    def restore_checkpoint(
        self,
        checkpoint_id: str,
        validate: bool = True,
    ) -> bool:
        """
        Restore state from checkpoint with validation.
        
        Args:
            checkpoint_id: Checkpoint to restore
            validate: Whether to validate before restoring
            
        Returns:
            True if successful
        """
        checkpoint_file = self.state_dir / f"checkpoint_{checkpoint_id}.json"
        
        if not checkpoint_file.exists():
            self.logger.log(
                AuditLevel.WARNING,
                "state_manager",
                "checkpoint_not_found",
                details={"checkpoint_id": checkpoint_id},
                status="failure",
            )
            return False
        
        try:
            with open(checkpoint_file, "r", encoding="utf-8") as f:
                checkpoint_data = json.load(f)
            
            snapshot = checkpoint_data.get("snapshot", {})
            
            # Validate before restoring
            if validate:
                is_valid, errors = self._validate_state(snapshot)
                if not is_valid:
                    self.logger.log(
                        AuditLevel.WARNING,
                        "state_manager",
                        "restore_validation_failed",
                        details={"checkpoint_id": checkpoint_id, "errors": errors[:3]},
                    )
                    return False
            
            # Restore state
            self._state = snapshot
            self._save_current_state()
            
            # Log restoration
            try:
                with open(self.state_history_file, "a", encoding="utf-8") as f:
                    f.write(json.dumps({
                        "event": "checkpoint_restored",
                        "timestamp": datetime.utcnow().isoformat(),
                        "checkpoint_id": checkpoint_id,
                    }) + "\n")
            except Exception:
                pass
            
            self.logger.log(
                AuditLevel.INFO,
                "state_manager",
                "checkpoint_restored",
                details={"checkpoint_id": checkpoint_id},
                status="success",
            )
            
            return True
        
        except Exception as e:
            self.logger.log(
                AuditLevel.CRITICAL,
                "state_manager",
                "checkpoint_restore_failed",
                details={"checkpoint_id": checkpoint_id},
                status="failure",
                error=str(e),
            )
            return False
    
    def get_checkpoint_info(self, checkpoint_id: str) -> Optional[Dict[str, Any]]:
        """Get checkpoint information."""
        checkpoint_file = self.state_dir / f"checkpoint_{checkpoint_id}.json"
        
        if not checkpoint_file.exists():
            return None
        
        try:
            with open(checkpoint_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            return {
                "id": data.get("id"),
                "timestamp": data.get("timestamp"),
                "hash": data.get("hash"),
                "validation_status": data.get("validation_status"),
                "metadata": data.get("metadata"),
            }
        except Exception:
            return None
    
    def compare_checkpoints(
        self,
        checkpoint_id_1: str,
        checkpoint_id_2: str,
    ) -> Optional[Dict[str, Any]]:
        """Compare two checkpoints."""
        info1 = self.get_checkpoint_info(checkpoint_id_1)
        info2 = self.get_checkpoint_info(checkpoint_id_2)
        
        if not info1 or not info2:
            return None
        
        snap1 = self._snapshots.get(checkpoint_id_1)
        snap2 = self._snapshots.get(checkpoint_id_2)
        
        if not snap1 or not snap2:
            return {"error": "Snapshots not loaded"}
        
        # Find differences
        all_keys = set(snap1.state.keys()) | set(snap2.state.keys())
        changed = {}
        
        for key in all_keys:
            v1 = snap1.state.get(key)
            v2 = snap2.state.get(key)
            if v1 != v2:
                changed[key] = {"before": v1, "after": v2}
        
        return {
            "checkpoint_1": checkpoint_id_1,
            "checkpoint_2": checkpoint_id_2,
            "changed_keys": len(changed),
            "changes": changed,
        }
    
    def clear_old_checkpoints(self, keep_count: int = 5) -> int:
        """Remove old checkpoints, keeping recent ones."""
        checkpoints = self.list_checkpoints()
        
        if len(checkpoints) <= keep_count:
            return 0
        
        to_remove = checkpoints[:-keep_count]
        removed_count = 0
        
        for checkpoint_id in to_remove:
            checkpoint_file = self.state_dir / f"checkpoint_{checkpoint_id}.json"
            try:
                checkpoint_file.unlink()
                self._snapshots.pop(checkpoint_id, None)
                removed_count += 1
            except Exception:
                pass
        
        return removed_count


# Global state manager instance
_state_manager: Optional[StateManager] = None


def get_state_manager() -> StateManager:
    """Get or create global state manager."""
    global _state_manager
    if _state_manager is None:
        _state_manager = StateManager()
    return _state_manager


if __name__ == "__main__":
    manager = get_state_manager()
    
    # Test state management
    manager.set("test_key", "test_value")
    manager.update({"key1": "value1", "key2": "value2"})
    
    print("Current state:", manager.get_all())
    
    # Create checkpoint
    checkpoint_hash = manager.create_checkpoint("test_checkpoint_1")
    print(f"Created checkpoint: {checkpoint_hash}")
    
    # List checkpoints
    print("Available checkpoints:", manager.list_checkpoints())
    
    # Modify state
    manager.set("key1", "modified_value")
    print("Modified state:", manager.get("key1"))
    
    # Restore checkpoint
    manager.restore_checkpoint("test_checkpoint_1")
    print("Restored state:", manager.get("key1"))
