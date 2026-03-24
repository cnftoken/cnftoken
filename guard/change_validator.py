"""Enhanced change validation with detailed analysis and staging checks."""
import subprocess
from typing import Dict, List, Tuple, Optional
from enum import Enum
from guard.failure import fail_hard, fail_validation
from guard.audit_logger import get_audit_logger, AuditLevel

CORE_DIR = 'core'


class ChangeType(Enum):
    """Git change types."""
    ADDED = "A"
    DELETED = "D"
    MODIFIED = "M"
    RENAMED = "R"
    COPIED = "C"
    TYPE_CHANGED = "T"
    UNTRACKED = "?"
    IGNORED = "!"
    UNMERGED = "U"


class ChangeValidator:
    """
    Enhanced git change validator with detailed analysis.
    
    Features:
    - Detailed change categorization
    - Staging level detection
    - Untracked file detection
    - Change statistics
    - Risk assessment
    """
    
    def __init__(self):
        """Initialize validator."""
        self.logger = get_audit_logger()
        self.staged_changes: Dict[ChangeType, List[str]] = {ct: [] for ct in ChangeType}
        self.unstaged_changes: Dict[ChangeType, List[str]] = {ct: [] for ct in ChangeType}
        self.core_violations: List[str] = []
    
    def _run_git(self, *args, check: bool = True) -> Tuple[str, str]:
        """
        Run git command.
        
        Args:
            *args: Git command arguments
            check: Raise on error
            
        Returns:
            Tuple of (stdout, stderr)
        """
        result = subprocess.run(
            ['git', *args],
            capture_output=True,
            text=True,
        )
        
        if check and result.returncode != 0:
            stderr = result.stderr.strip()
            if 'Not a git repository' in stderr:
                return '', ''
            
            self.logger.log(
                AuditLevel.WARNING,
                "change_validator",
                "git_command_failed",
                details={"command": ' '.join(args), "error": stderr},
                status="failure",
            )
            fail_validation(
                f"Git command failed",
                details={"command": ' '.join(args), "error": stderr},
            )
        
        return result.stdout.strip(), result.stderr.strip()
    
    def _parse_status(self, status_output: str) -> Dict[ChangeType, List[str]]:
        """
        Parse git status output.
        
        Args:
            status_output: Raw git status output
            
        Returns:
            Dictionary of change type -> file list
        """
        changes: Dict[ChangeType, List[str]] = {ct: [] for ct in ChangeType}
        
        for line in status_output.splitlines():
            if not line or len(line) < 3:
                continue
            
            status_char = line[0]
            filepath = line[3:].strip()
            
            # Try to match change type
            for ct in ChangeType:
                if ct.value == status_char:
                    changes[ct].append(filepath)
                    break
        
        return changes
    
    def analyze_changes(self) -> Dict[str, any]:
        """
        Analyze all staged and unstaged changes.
        
        Returns:
            Dictionary with change analysis
        """
        self.core_violations.clear()
        
        # Get staged changes
        staged_output, _ = self._run_git('diff', '--cached', '--name-status', check=False)
        self.staged_changes = self._parse_status(staged_output)
        
        # Get unstaged changes
        unstaged_output, _ = self._run_git('diff', '--name-status', check=False)
        self.unstaged_changes = self._parse_status(unstaged_output)
        
        # Get untracked files
        untracked_output, _ = self._run_git('ls-files', '--others', '--exclude-standard', check=False)
        untracked_files = [f for f in untracked_output.splitlines() if f.strip()]
        
        # Check for core modifications
        all_modified = []
        for ct, files in self.staged_changes.items():
            all_modified.extend(files)
        for ct, files in self.unstaged_changes.items():
            all_modified.extend(files)
        
        self.core_violations = [
            p for p in all_modified
            if p.startswith(CORE_DIR + '/') or p == CORE_DIR
        ]
        
        # Calculate statistics
        stats = {
            'staged': {
                'total': sum(len(files) for files in self.staged_changes.values()),
                'added': len(self.staged_changes[ChangeType.ADDED]),
                'modified': len(self.staged_changes[ChangeType.MODIFIED]),
                'deleted': len(self.staged_changes[ChangeType.DELETED]),
            },
            'unstaged': {
                'total': sum(len(files) for files in self.unstaged_changes.values()),
                'added': len(self.unstaged_changes[ChangeType.ADDED]),
                'modified': len(self.unstaged_changes[ChangeType.MODIFIED]),
                'deleted': len(self.unstaged_changes[ChangeType.DELETED]),
            },
            'untracked': len(untracked_files),
            'core_violations': len(self.core_violations),
        }
        
        return {
            'staged_changes': self.staged_changes,
            'unstaged_changes': self.unstaged_changes,
            'untracked_files': untracked_files,
            'statistics': stats,
            'core_violations': self.core_violations,
        }
    
    def check_core_changes(self) -> bool:
        """
        Check for modifications to core directory.
        
        Returns:
            True if no core modifications, raises otherwise
        """
        analysis = self.analyze_changes()
        
        if analysis['core_violations']:
            self.logger.log(
                AuditLevel.CRITICAL,
                "change_validator",
                "core_modification_detected",
                details={
                    "violations": analysis['core_violations'],
                    "count": len(analysis['core_violations']),
                },
                status="failure",
                error=f"Core modification detected in {len(analysis['core_violations'])} files",
            )
            
            fail_validation(
                "Core modification detected",
                details={
                    "files": analysis['core_violations'],
                    "count": len(analysis['core_violations']),
                },
            )
        
        self.logger.log(
            AuditLevel.INFO,
            "change_validator",
            "no_core_changes",
            details=analysis['statistics'],
            status="success",
        )
        
        return True
    
    def check_unstaged_changes(self, fail_on_unstaged: bool = False) -> bool:
        """
        Check for unstaged changes.
        
        Args:
            fail_on_unstaged: Fail if there are unstaged changes
            
        Returns:
            False if unstaged changes exist, True otherwise
        """
        analysis = self.analyze_changes()
        unstaged_count = analysis['statistics']['unstaged']['total']
        
        if unstaged_count > 0 and fail_on_unstaged:
            self.logger.log(
                AuditLevel.WARNING,
                "change_validator",
                "unstaged_changes_detected",
                details=analysis['statistics'],
                status="failure",
            )
            
            fail_validation(
                f"Found {unstaged_count} unstaged changes",
                details=analysis['statistics'],
            )
        
        return unstaged_count == 0
    
    def check_untracked_files(self, ignore_patterns: Optional[List[str]] = None) -> bool:
        """
        Check for untracked files.
        
        Args:
            ignore_patterns: File patterns to ignore
            
        Returns:
            False if untracked files exist, True otherwise
        """
        analysis = self.analyze_changes()
        untracked = analysis.get('untracked_files', [])
        
        if ignore_patterns:
            untracked = [
                f for f in untracked
                if not any(pattern in f for pattern in ignore_patterns)
            ]
        
        return len(untracked) == 0
    
    def get_detailed_report(self) -> str:
        """Get detailed change report."""
        analysis = self.analyze_changes()
        stats = analysis['statistics']
        
        lines = [
            "=== GIT CHANGE ANALYSIS ===",
            "",
            f"Staged Changes:  {stats['staged']['total']} files",
            f"  + Added:      {stats['staged']['added']}",
            f"  ~ Modified:   {stats['staged']['modified']}",
            f"  - Deleted:    {stats['staged']['deleted']}",
            "",
            f"Unstaged Changes: {stats['unstaged']['total']} files",
            f"  + Added:      {stats['unstaged']['added']}",
            f"  ~ Modified:   {stats['unstaged']['modified']}",
            f"  - Deleted:    {stats['unstaged']['deleted']}",
            "",
            f"Untracked Files: {stats['untracked']}",
            f"Core Violations: {stats['core_violations']}",
        ]
        
        return "\n".join(lines)


# Global validator instance
_validator: Optional[ChangeValidator] = None


def get_validator() -> ChangeValidator:
    """Get or create validator instance."""
    global _validator
    if _validator is None:
        _validator = ChangeValidator()
    return _validator


def list_modified_files() -> List[str]:
    """List all modified files (staged + unstaged)."""
    analysis = get_validator().analyze_changes()
    result = []
    
    for ct, files in analysis['staged_changes'].items():
        result.extend(files)
    for ct, files in analysis['unstaged_changes'].items():
        if files not in result:
            result.extend(files)
    
    return result


def check_core_changes() -> bool:
    """Check for core modifications."""
    return get_validator().check_core_changes()


if __name__ == '__main__':
    validator = get_validator()
    validator.check_core_changes()
    print(validator.get_detailed_report())
