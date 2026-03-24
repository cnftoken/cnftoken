"""Enhanced auto-staging with validation and safety checks."""
import subprocess
import pathlib
from typing import List, Optional, Dict, Tuple
from enum import Enum
from guard.failure import fail_hard
from guard.audit_logger import get_audit_logger, AuditLevel
from guard.change_validator import get_validator as get_change_validator


class StagingLevel(Enum):
    """Staging safety levels."""
    CONSERVATIVE = "conservative"  # Only safe files
    NORMAL = "normal"              # Most files except core/
    AGGRESSIVE = "aggressive"      # All files including generated


class FileCategory(Enum):
    """File categorization for staging."""
    PROTECTED = "protected"        # Never auto-stage (core/, .git/)
    CORE_CODE = "core_code"        # Source code (careful)
    DOCUMENTATION = "documentation"
    CONFIG = "config"              # Config files
    TESTS = "tests"
    GENERATED = "generated"        # Build artifacts
    DATA = "data"


class AutoStager:
    """
    Enhanced auto-staging validator.
    
    Features:
    - File categorization
    - Safety validation before staging
    - Protected path rules
    - Dry-run support
    - Detailed staging reports
    - Change integration
    """
    
    def __init__(self, level: StagingLevel = StagingLevel.NORMAL):
        """Initialize auto-stager."""
        self.logger = get_audit_logger()
        self.change_validator = get_change_validator()
        self.level = level
        self.staged_files: List[str] = []
        self.skipped_files: Dict[str, str] = {}
        
        # Protected paths (never auto-stage)
        self.protected_patterns = [
            'core/',
            '.git/',
            '.gitignore',
            '.env',
            '.env.local',
            'secrets/',
            'credentials/',
        ]
        
        # File patterns by category
        self.categories = {
            FileCategory.DOCUMENTATION: ['*.md', '*.txt', '*README*'],
            FileCategory.CONFIG: ['*.yaml', '*.yml', '*.toml', '*.json'],
            FileCategory.TESTS: ['test_*.py', '*_test.py'],
            FileCategory.GENERATED: ['*.pyc', '__pycache__', 'build/', 'dist/'],
        }
    
    def _run_git(self, *args) -> Tuple[List[str], bool]:
        """Execute git command safely."""
        try:
            result = subprocess.run(
                ['git', *args],
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.returncode != 0:
                return [], False
            return result.stdout.strip().splitlines(), True
        except Exception as e:
            self.logger.log(
                AuditLevel.ERROR,
                "auto_stage",
                "git_execution_failed",
                error=str(e),
            )
            return [], False
    
    def _is_protected(self, path: str) -> bool:
        """Check if path is protected from auto-staging."""
        for pattern in self.protected_patterns:
            if path.startswith(pattern) or path.endswith(pattern):
                return True
        return False
    
    def _categorize_file(self, path: str) -> FileCategory:
        """Categorize file for staging rules."""
        path_lower = path.lower()
        
        for category, patterns in self.categories.items():
            for pattern in patterns:
                if pattern.startswith('*'):
                    if path_lower.endswith(pattern[1:]):
                        return category
                elif pattern in path_lower:
                    return category
        
        # Default based on content
        if any(x in path for x in ['.py', '.rs', '.ts', '.js']):
            return FileCategory.CORE_CODE
        
        return FileCategory.DATA
    
    def _is_safe_to_stage(self, path: str, category: FileCategory) -> bool:
        """Check if file is safe to stage."""
        if self._is_protected(path):
            return False
        
        # Level-based rules
        if self.level == StagingLevel.CONSERVATIVE:
            # Only docs and tests
            return category in [
                FileCategory.DOCUMENTATION,
                FileCategory.TESTS,
            ]
        elif self.level == StagingLevel.NORMAL:
            # Everything except protected and generated
            return category != FileCategory.GENERATED
        elif self.level == StagingLevel.AGGRESSIVE:
            # Everything except protected
            return True
        
        return False
    
    def prepare_staging(self, dry_run: bool = True) -> Dict:
        """
        Prepare files for staging with validation.
        
        Args:
            dry_run: If True, don't actually stage files
            
        Returns:
            Dictionary with staging results
        """
        # Get current changes
        status_lines, success = self._run_git('status', '--porcelain')
        
        if not success:
            fail_hard(
                "Failed to get git status",
                component="auto_stage",
                details={"level": self.level.value},
            )
        
        self.staged_files = []
        self.skipped_files = {}
        
        for line in status_lines:
            if not line.strip():
                continue
            
            git_status = line[:2]
            path = line[3:]
            
            # Skip unstaged changes
            if git_status[0] == ' ':
                self.skipped_files[path] = "unstaged"
                continue
            
            category = self._categorize_file(path)
            
            if self._is_safe_to_stage(path, category):
                self.staged_files.append(path)
            else:
                skip_reason = "protected" if self._is_protected(path) else f"unsafe_{category.value}"
                self.skipped_files[path] = skip_reason
        
        # Validate before staging
        if self.staged_files and not dry_run:
            self._execute_staging()
        
        # Log staging preparation
        self.logger.log(
            AuditLevel.INFO,
            "auto_stage",
            "staging_prepared",
            details={
                "level": self.level.value,
                "dry_run": dry_run,
                "to_stage": len(self.staged_files),
                "skipped": len(self.skipped_files),
                "files": self.staged_files[:10],  # Log first 10
            },
            status="success"
        )
        
        return {
            "level": self.level.value,
            "dry_run": dry_run,
            "staged_files": self.staged_files,
            "skipped_files": self.skipped_files,
            "count_staged": len(self.staged_files),
            "count_skipped": len(self.skipped_files),
        }
    
    def _execute_staging(self) -> None:
        """Actually stage the files."""
        if not self.staged_files:
            return
        
        try:
            result = subprocess.run(
                ['git', 'add', *self.staged_files],
                capture_output=True,
                text=True,
                timeout=30,
            )
            
            if result.returncode != 0:
                fail_hard(
                    "Git add failed",
                    component="auto_stage",
                    details={"error": result.stderr},
                )
            
            self.logger.log(
                AuditLevel.INFO,
                "auto_stage",
                "files_staged",
                details={
                    "count": len(self.staged_files),
                    "files": self.staged_files[:10],
                },
                status="success"
            )
        except Exception as e:
            fail_hard(
                "Failed to execute git add",
                component="auto_stage",
                details={"error": str(e)},
            )
    
    def get_report(self) -> str:
        """Get detailed staging report."""
        lines = [
            "=== AUTO-STAGING REPORT ===",
            f"Level: {self.level.value}",
            "",
            f"Files to Stage:     {len(self.staged_files)}",
            f"Files Skipped:      {len(self.skipped_files)}",
        ]
        
        if self.staged_files:
            lines.extend(["", "Staged Files:"])
            for f in self.staged_files[:20]:
                lines.append(f"  ✓ {f}")
            if len(self.staged_files) > 20:
                lines.append(f"  ... and {len(self.staged_files) - 20} more")
        
        if self.skipped_files:
            lines.extend(["", "Skipped Files:"])
            for f, reason in list(self.skipped_files.items())[:20]:
                lines.append(f"  ✗ {f} ({reason})")
            if len(self.skipped_files) > 20:
                lines.append(f"  ... and {len(self.skipped_files) - 20} more")
        
        return "\n".join(lines)


# Global stager instance
_stager: Optional[AutoStager] = None


def get_stager(level: StagingLevel = StagingLevel.NORMAL) -> AutoStager:
    """Get or create stager instance."""
    global _stager
    if _stager is None or _stager.level != level:
        _stager = AutoStager(level)
    return _stager


def auto_stage(dry_run: bool = False) -> List[str]:
    """Auto-stage files (backward compatible)."""
    stager = get_stager()
    result = stager.prepare_staging(dry_run=dry_run)
    return result["staged_files"]


def auto_stage_with_level(level: str, dry_run: bool = False) -> Dict:
    """Auto-stage with specific safety level."""
    try:
        staging_level = StagingLevel[level.upper()]
    except KeyError:
        fail_hard(
            f"Invalid staging level: {level}",
            component="auto_stage",
            details={"valid_levels": [e.value for e in StagingLevel]},
        )
    
    stager = get_stager(staging_level)
    return stager.prepare_staging(dry_run=dry_run)


if __name__ == '__main__':
    stager = get_stager(StagingLevel.NORMAL)
    result = stager.prepare_staging(dry_run=True)
    print(stager.get_report())
