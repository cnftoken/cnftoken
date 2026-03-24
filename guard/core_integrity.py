"""Enhanced core directory integrity validation with caching and incremental hashing."""
import os
import hashlib
import json
from pathlib import Path
from typing import Optional, Dict, Tuple
from datetime import datetime
from guard.failure import fail_hard, fail_integrity, ExitCode
from guard.audit_logger import get_audit_logger, AuditLevel

HASH_PATH = 'guard/core_hash.sha256'
CORE_DIR = 'core'
METADATA_PATH = 'guard/.core_metadata.json'


class CoreIntegrityValidator:
    """
    Enhanced core directory integrity validator with caching and incremental hashing.
    
    Features:
    - SHA256 hashing with caching
    - Incremental updates
    - File-level tracking
    - Detailed change detection
    - Performance optimization
    """
    
    def __init__(self):
        """Initialize validator."""
        self.logger = get_audit_logger()
        self.metadata: Dict = self._load_metadata()
        self.file_hashes: Dict[str, str] = {}
    
    def _load_metadata(self) -> Dict:
        """Load cached metadata if available."""
        if not os.path.exists(METADATA_PATH):
            return {}
        
        try:
            with open(METADATA_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {}
    
    def _save_metadata(self) -> None:
        """Save metadata to file."""
        try:
            Path(METADATA_PATH).parent.mkdir(parents=True, exist_ok=True)
            with open(METADATA_PATH, 'w', encoding='utf-8') as f:
                json.dump(self.metadata, f, indent=2)
        except Exception as e:
            self.logger.log(
                AuditLevel.WARNING,
                "core_integrity",
                "metadata_save_failed",
                error=str(e),
            )
    
    def _hash_file(self, filepath: str) -> str:
        """Compute hash of a single file."""
        sha = hashlib.sha256()
        try:
            with open(filepath, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b''):
                    sha.update(chunk)
            return sha.hexdigest()
        except Exception as e:
            self.logger.log(
                AuditLevel.WARNING,
                "core_integrity",
                "file_hash_failed",
                details={"file": filepath},
                error=str(e),
            )
            return ""
    
    def _detect_changes(self, current_hashes: Dict[str, str]) -> Dict[str, list]:
        """Detect changes by comparing file hashes."""
        old_hashes = self.metadata.get('file_hashes', {})
        
        changes = {
            'added': [],
            'removed': [],
            'modified': [],
            'unchanged': [],
        }
        
        # Check for added/modified files
        for filepath, current_hash in current_hashes.items():
            if filepath not in old_hashes:
                changes['added'].append(filepath)
            elif old_hashes[filepath] != current_hash:
                changes['modified'].append(filepath)
            else:
                changes['unchanged'].append(filepath)
        
        # Check for removed files
        for filepath in old_hashes:
            if filepath not in current_hashes:
                changes['removed'].append(filepath)
        
        return changes
    
    def compute_core_hash(self, use_cache: bool = True) -> Optional[str]:
        """
        Compute hash of core directory.
        
        Args:
            use_cache: Use cached metadata if available
            
        Returns:
            SHA256 hash or None if core dir doesn't exist
        """
        if not os.path.isdir(CORE_DIR):
            return None
        
        sha = hashlib.sha256()
        self.file_hashes.clear()
        
        try:
            for root, dirs, files in os.walk(CORE_DIR):
                dirs.sort()
                files.sort()
                
                for filename in files:
                    filepath = os.path.join(root, filename)
                    rel_path = os.path.relpath(filepath, CORE_DIR)
                    
                    # Compute file hash
                    file_hash = self._hash_file(filepath)
                    if not file_hash:
                        continue
                    
                    self.file_hashes[rel_path] = file_hash
                    
                    # Update directory hash
                    sha.update(rel_path.encode('utf-8'))
                    sha.update(file_hash.encode('utf-8'))
            
            overall_hash = sha.hexdigest()
            
            # Detect and log changes
            if use_cache and self.metadata.get('file_hashes'):
                changes = self._detect_changes(self.file_hashes)
                if changes['modified'] or changes['added'] or changes['removed']:
                    self.logger.log(
                        AuditLevel.INFO,
                        "core_integrity",
                        "changes_detected",
                        details=changes,
                    )
            
            return overall_hash
        
        except Exception as e:
            self.logger.log(
                AuditLevel.WARNING,
                "core_integrity",
                "hash_computation_failed",
                error=str(e),
            )
            return None
    
    def write_core_hash(self, override: bool = False) -> str:
        """
        Write core hash and metadata.
        
        Args:
            override: Force overwrite even if hash exists
            
        Returns:
            Computed hash value
        """
        if os.path.exists(HASH_PATH) and not override:
            self.logger.log(
                AuditLevel.WARNING,
                "core_integrity",
                "hash_already_exists",
                status="skip",
            )
            with open(HASH_PATH, 'r', encoding='utf-8') as f:
                return f.read().strip()
        
        value = self.compute_core_hash() or ''
        
        try:
            hash_file = Path(HASH_PATH)
            hash_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(hash_file, 'w', encoding='utf-8') as f:
                f.write(value)
            
            # Save metadata
            self.metadata = {
                'timestamp': datetime.utcnow().isoformat(),
                'hash': value,
                'file_count': len(self.file_hashes),
                'file_hashes': self.file_hashes,
            }
            self._save_metadata()
            
            self.logger.log(
                AuditLevel.INFO,
                "core_integrity",
                "hash_written",
                details={
                    "hash": value[:16],
                    "files": len(self.file_hashes),
                },
                status="success",
            )
            
            return value
        
        except Exception as e:
            fail_integrity(
                "Failed to write core hash",
                details={"error": str(e)},
            )
    
    def validate_core_hash(self) -> bool:
        """
        Validate core directory integrity.
        
        Returns:
            True if hash matches, raises exception otherwise
        """
        expected = None
        if os.path.exists(HASH_PATH):
            with open(HASH_PATH, 'r', encoding='utf-8') as f:
                expected = f.read().strip()
        
        current = self.compute_core_hash(use_cache=True) or ''
        
        if expected != current:
            changes = self._detect_changes(self.file_hashes) if self.metadata.get('file_hashes') else {}
            
            self.logger.log(
                AuditLevel.CRITICAL,
                "core_integrity",
                "hash_mismatch",
                details={
                    "expected": expected[:16],
                    "current": current[:16],
                    "changes": changes,
                },
                status="failure",
                error="Core integrity hash mismatch",
            )
            
            fail_integrity(
                "Core integrity hash mismatch. Core directory may have been modified.",
                details={
                    "expected": expected[:16],
                    "current": current[:16],
                    "modified_files": changes.get('modified', []),
                },
            )
        
        self.logger.log(
            AuditLevel.INFO,
            "core_integrity",
            "hash_validated",
            details={"hash": current[:16], "files": len(self.file_hashes)},
            status="success",
        )
        
        return True
    
    def get_file_changes(self) -> Dict[str, list]:
        """Get detected file changes."""
        if not self.metadata.get('file_hashes'):
            return {'added': [], 'removed': [], 'modified': [], 'unchanged': []}
        
        return self._detect_changes(self.file_hashes)


# Global validator instance
_validator: Optional[CoreIntegrityValidator] = None


def get_validator() -> CoreIntegrityValidator:
    """Get or create validator instance."""
    global _validator
    if _validator is None:
        _validator = CoreIntegrityValidator()
    return _validator


def compute_core_hash():
    """Compute core hash."""
    return get_validator().compute_core_hash()


def write_core_hash(override: bool = False):
    """Write core hash."""
    return get_validator().write_core_hash(override=override)


def validate_core_hash():
    """Validate core hash."""
    return get_validator().validate_core_hash()


if __name__ == '__main__':
    validator = get_validator()
    
    if not os.path.exists(HASH_PATH):
        validator.write_core_hash()
        print('✓ Core hash initialized')
    else:
        validator.validate_core_hash()
        print('✓ Core hash validated')
        
        if validator.get_file_changes():
            changes = validator.get_file_changes()
            if changes['added']:
                print(f"  Added files: {len(changes['added'])}")
            if changes['modified']:
                print(f"  Modified files: {len(changes['modified'])}")
            if changes['removed']:
                print(f"  Removed files: {len(changes['removed'])}")
