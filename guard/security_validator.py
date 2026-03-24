"""Enhanced security validation with scanning, caching and parallel processing."""
import os
import hashlib
import stat
import threading
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Set
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from guard.audit_logger import get_audit_logger, AuditLevel


@dataclass
class SecurityViolation:
    """Security violation report."""
    filepath: str
    violation: str
    severity: str
    violation_type: str
    details: Dict = field(default_factory=dict)


@dataclass
class ScanResult:
    """Result of security scan."""
    total_files: int = 0
    scanned_files: int = 0
    violations_by_severity: Dict[str, int] = field(default_factory=dict)
    violations: List[SecurityViolation] = field(default_factory=list)
    scan_time_ms: float = 0.0
    cache_hits: int = 0


class SecurityValidator:
    """
    Enhanced security validator with deep scanning and caching.
    
    Features:
    - File permission validation
    - Binary file detection
    - File integrity checking
    - Path traversal prevention
    - Parallel file scanning
    - Hash caching for performance
    - Detailed violation reporting
    - Custom rule support
    """
    
    # Safe file extensions
    SAFE_EXTENSIONS = {
        '.py', '.rs', '.md', '.txt', '.json', '.yaml', '.yml',
        '.toml', '.cfg', '.conf', '.sh', '.bash', '.lock',
    }
    
    # Dangerous extensions
    DANGEROUS_EXTENSIONS = {
        '.exe', '.dll', '.so', '.dylib', '.bin', '.obj',
        '.class', '.pyc', '.pyd', '.o', '.a',
    }
    
    MAX_FILE_SIZE = 10 * 1024 * 1024
    
    def __init__(self, use_cache: bool = True, max_workers: int = 4):
        """
        Initialize security validator.
        
        Args:
            use_cache: Whether to cache file hashes
            max_workers: Number of parallel workers for scanning
        """
        self.logger = get_audit_logger()
        self.violations: List[SecurityViolation] = []
        self.use_cache = use_cache
        self.max_workers = max_workers
        self._hash_cache: Dict[str, str] = {}
        self._lock = threading.Lock()
    
    def _compute_file_hash(self, filepath: str) -> str:
        """Compute SHA256 hash of file."""
        if self.use_cache and filepath in self._hash_cache:
            return self._hash_cache[filepath]
        
        sha = hashlib.sha256()
        try:
            with open(filepath, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b''):
                    sha.update(chunk)
            file_hash = sha.hexdigest()
            
            if self.use_cache:
                with self._lock:
                    self._hash_cache[filepath] = file_hash
            
            return file_hash
        except Exception:
            return "error"
    
    def _is_binary(self, filepath: str) -> bool:
        """Detect binary files."""
        try:
            with open(filepath, 'rb') as f:
                chunk = f.read(512)
                if not chunk:
                    return False
                return b'\x00' in chunk
        except Exception:
            return True
    
    def check_file_permissions(self, filepath: str) -> Tuple[bool, Optional[SecurityViolation]]:
        """Check file permissions."""
        try:
            file_stat = os.stat(filepath)
            mode = file_stat.st_mode
            mode_str = oct(stat.S_IMODE(mode))
            
            # Check world-writable
            if mode & stat.S_IWOTH:
                violation = SecurityViolation(
                    filepath=filepath,
                    violation=f"World-writable: {mode_str}",
                    severity="critical",
                    violation_type="permissions",
                    details={"mode": mode_str},
                )
                return False, violation
            
            # Check group-writable
            if mode & stat.S_IWGRP:
                violation = SecurityViolation(
                    filepath=filepath,
                    violation=f"Group-writable: {mode_str}",
                    severity="warning",
                    violation_type="permissions",
                    details={"mode": mode_str},
                )
                return True, violation
            
            return True, None
        
        except Exception as e:
            violation = SecurityViolation(
                filepath=filepath,
                violation=f"Permission check failed: {str(e)}",
                severity="error",
                violation_type="permissions",
            )
            return False, violation
    
    def check_file_integrity(
        self,
        filepath: str,
        expected_hash: Optional[str] = None,
    ) -> Tuple[bool, str, Optional[SecurityViolation]]:
        """Check file integrity."""
        try:
            file_hash = self._compute_file_hash(filepath)
            
            if expected_hash and file_hash != expected_hash:
                violation = SecurityViolation(
                    filepath=filepath,
                    violation=f"Hash mismatch",
                    severity="critical",
                    violation_type="integrity",
                    details={"expected": expected_hash, "actual": file_hash},
                )
                return False, file_hash, violation
            
            return True, file_hash, None
        
        except Exception as e:
            violation = SecurityViolation(
                filepath=filepath,
                violation=f"Integrity check failed: {str(e)}",
                severity="error",
                violation_type="integrity",
            )
            return False, "error", violation
    
    def check_file_size(self, filepath: str) -> Tuple[bool, Optional[SecurityViolation]]:
        """Check file size."""
        try:
            size = os.path.getsize(filepath)
            
            if size > self.MAX_FILE_SIZE:
                violation = SecurityViolation(
                    filepath=filepath,
                    violation=f"File too large: {size} bytes",
                    severity="warning",
                    violation_type="size",
                    details={"size": size, "max": self.MAX_FILE_SIZE},
                )
                return False, violation
            
            return True, None
        
        except Exception as e:
            violation = SecurityViolation(
                filepath=filepath,
                violation=f"Size check failed: {str(e)}",
                severity="error",
                violation_type="size",
            )
            return False, violation
    
    def check_file_extension(self, filepath: str) -> Tuple[bool, Optional[SecurityViolation]]:
        """Check file extension."""
        _, ext = os.path.splitext(filepath)
        
        if ext in self.DANGEROUS_EXTENSIONS:
            violation = SecurityViolation(
                filepath=filepath,
                violation=f"Dangerous extension: {ext}",
                severity="critical",
                violation_type="extension",
                details={"extension": ext},
            )
            return False, violation
        
        return ext not in self.DANGEROUS_EXTENSIONS, None
    
    def _scan_file(self, filepath: str) -> Tuple[int, List[SecurityViolation]]:
        """Scan single file for violations."""
        violations_found = []
        check_count = 0
        
        # Permission check
        ok, violation = self.check_file_permissions(filepath)
        check_count += 1
        if violation:
            violations_found.append(violation)
        
        # Extension check
        ok, violation = self.check_file_extension(filepath)
        check_count += 1
        if violation:
            violations_found.append(violation)
        
        # Size check
        ok, violation = self.check_file_size(filepath)
        check_count += 1
        if violation:
            violations_found.append(violation)
        
        return check_count, violations_found
    
    def scan_directory(
        self,
        root_dir: str,
        parallel: bool = True,
    ) -> ScanResult:
        """
        Scan directory for security issues.
        
        Args:
            root_dir: Root directory to scan
            parallel: Whether to use parallel processing
            
        Returns:
            ScanResult with detailed findings
        """
        import time
        start_time = time.time()
        
        self.violations.clear()
        result = ScanResult()
        result.total_files = 0
        result.scanned_files = 0
        
        # Collect files to scan
        files_to_scan = []
        skip_dirs = {'.git', '__pycache__', 'node_modules', 'target', '.venv', 'venv'}
        
        for dirpath, dirnames, filenames in os.walk(root_dir):
            dirnames[:] = [d for d in dirnames if d not in skip_dirs]
            
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                files_to_scan.append(filepath)
                result.total_files += 1
        
        # Scan files
        if parallel and len(files_to_scan) > 10:
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                futures = {executor.submit(self._scan_file, f): f for f in files_to_scan}
                
                for future in as_completed(futures):
                    try:
                        _, violations = future.result()
                        result.violations.extend(violations)
                        result.scanned_files += 1
                    except Exception:
                        pass
        else:
            for filepath in files_to_scan:
                _, violations = self._scan_file(filepath)
                result.violations.extend(violations)
                result.scanned_files += 1
        
        # Summarize violations
        for violation in result.violations:
            severity = violation.severity
            if severity not in result.violations_by_severity:
                result.violations_by_severity[severity] = 0
            result.violations_by_severity[severity] += 1
        
        result.scan_time_ms = (time.time() - start_time) * 1000
        self.violations = result.violations
        
        self.logger.log(
            AuditLevel.INFO,
            "security_validator",
            "directory_scan_completed",
            details={
                "total_files": result.total_files,
                "scanned_files": result.scanned_files,
                "violations": len(result.violations),
                "scan_time_ms": round(result.scan_time_ms, 2),
            },
        )
        
        return result
    
    def validate_path(self, filepath: str, base_dir: str) -> bool:
        """Check for path traversal."""
        try:
            real_path = Path(filepath).resolve()
            real_base = Path(base_dir).resolve()
            
            is_safe = str(real_path).startswith(str(real_base))
            
            if not is_safe:
                violation = SecurityViolation(
                    filepath=filepath,
                    violation=f"Path traversal detected",
                    severity="critical",
                    violation_type="path_traversal",
                )
                self.violations.append(violation)
            
            return is_safe
        
        except Exception as e:
            violation = SecurityViolation(
                filepath=filepath,
                violation=f"Path validation failed: {str(e)}",
                severity="error",
                violation_type="path_traversal",
            )
            self.violations.append(violation)
            return False
    
    def clear_cache(self) -> int:
        """Clear hash cache."""
        count = len(self._hash_cache)
        self._hash_cache.clear()
        return count
    
    def get_report(self) -> str:
        """Generate security report."""
        if not self.violations:
            return "✓ No security violations detected"

        lines = ["=== SECURITY VALIDATION REPORT ===", ""]

        by_severity = {}
        for violation in self.violations:
            if violation.severity not in by_severity:
                by_severity[violation.severity] = []
            by_severity[violation.severity].append(violation)

        for severity in ['critical', 'error', 'warning', 'info']:
            if severity in by_severity:
                icon = "✗" if severity in ['critical', 'error'] else "⚠"
                violations = by_severity[severity]
                lines.append(f"{icon} {severity.upper()} ({len(violations)}):")
                for v in violations[:10]:
                    lines.append(f"  - {Path(v.filepath).name}: {v.violation}")

        return "\n".join(lines)

    def get_violations(self) -> List[SecurityViolation]:
        """Return collected violations from the last scan."""
        return self.violations

    def check_file_extension(self, filepath: str) -> bool:
        """
        Check file extension is safe.

        Args:
            filepath: Path to file
            
        Returns:
            True if extension is safe, False if dangerous
        """
        _, ext = os.path.splitext(filepath)
        
        if ext in self.DANGEROUS_EXTENSIONS:
            violation = f"Dangerous file extension: {ext}"
            self.violations.append((filepath, violation, "critical"))
            return False
        
        # Warn about unknown extensions
        if ext and ext not in self.SAFE_EXTENSIONS:
            violation = f"Unknown file extension: {ext}"
            self.violations.append((filepath, violation, "info"))
        
        return ext not in self.DANGEROUS_EXTENSIONS
    
    def check_directory_structure(self, root_dir: str) -> Dict[str, int]:
        """
        Check entire directory structure for security issues.
        
        Args:
            root_dir: Root directory to check
            
        Returns:
            Summary of violations by severity
        """
        self.violations.clear()
        
        for dirpath, dirnames, filenames in os.walk(root_dir):
            # Skip dangerous directories
            dirnames[:] = [d for d in dirnames if d not in {'.git', '__pycache__', 'node_modules', 'target'}]
            


# Global validator instance
_validator: Optional['SecurityValidator'] = None


def get_security_validator() -> 'SecurityValidator':
    """Get or create global security validator."""
    global _validator
    if _validator is None:
        _validator = SecurityValidator()
    return _validator


if __name__ == "__main__":
    validator = get_security_validator()
    result = validator.scan_directory("guard")
    print(validator.get_report())
