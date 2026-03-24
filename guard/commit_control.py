"""Enhanced commit control with templates and validation framework."""
import subprocess
import re
from typing import List, Optional, Dict, Tuple
from enum import Enum
from dataclasses import dataclass
from guard.failure import fail_hard
from guard.audit_logger import get_audit_logger, AuditLevel


class CommitType(Enum):
    """Semantic commit types."""
    FEAT = "feat"       # New feature
    FIX = "fix"         # Bug fix
    TEST = "test"       # Testing
    CHORE = "chore"     # Maintenance
    DOCS = "docs"       # Documentation
    STYLE = "style"     # Code style
    REFACTOR = "refactor"  # Code refactoring
    PERF = "perf"       # Performance


@dataclass
class CommitTemplate:
    """Commit message template."""
    commit_type: CommitType
    scope: str
    description: str
    body: Optional[str] = None
    footer: Optional[str] = None
    breaking: bool = False


class CommitValidator:
    """
    Enhanced commit validation.
    
    Features:
    - Semantic versioning compliance
    - Commit message templates
    - File change validation
    - Atomic commit detection
    - Breaking change tracking
    - Detailed validation reporting
    """
    
    def __init__(self):
        """Initialize validator."""
        self.logger = get_audit_logger()
        self.allowed_types = set(ct.value for ct in CommitType)
        
        # Validation rules
        self.min_description_length = 3
        self.max_description_length = 72
        self.max_body_line_length = 100
    
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
                "commit_control",
                "git_execution_failed",
                error=str(e),
            )
            return [], False
    
    def _get_staged_files(self) -> List[str]:
        """Get list of staged files."""
        lines, success = self._run_git('diff', '--cached', '--name-only')
        return lines if success else []
    
    def check_atomic_commit(self) -> bool:
        """
        Validate that commit is atomic (focused).
        
        Returns:
            True if valid, raises otherwise
        """
        staged = self._get_staged_files()
        
        if not staged:
            fail_hard(
                "No changes staged for commit",
                component="commit_control",
            )
        
        # Check scope consistency
        scopes = self._extract_scopes(staged)
        
        if len(scopes) > 3:
            fail_hard(
                f"Commit touches too many areas ({len(scopes)}). Keep commits atomic.",
                component="commit_control",
                details={"scopes": list(scopes)},
            )
        
        self.logger.log(
            AuditLevel.INFO,
            "commit_control",
            "atomic_check_passed",
            details={
                "files": len(staged),
                "scopes": len(scopes),
            },
        )
        
        return True
    
    def _extract_scopes(self, files: List[str]) -> set:
        """Extract logical scopes from file paths."""
        scopes = set()
        
        for f in files:
            parts = f.split('/')
            if len(parts) > 1:
                scopes.add(parts[0])
            if any(x in f for x in ['.py', 'test', 'spec']):
                scopes.add('code')
            if any(x in f for x in ['.md', 'README', 'readme']):
                scopes.add('docs')
        
        return scopes
    
    def validate_commit_type(self, commit_type: str) -> bool:
        """Validate commit type."""
        if commit_type not in self.allowed_types:
            fail_hard(
                f"Invalid commit type: {commit_type}",
                component="commit_control",
                details={
                    "provided": commit_type,
                    "allowed": list(self.allowed_types),
                },
            )
        return True
    
    def validate_description(self, description: str) -> bool:
        """Validate commit description."""
        if not description or not description.strip():
            fail_hard(
                "Description cannot be empty",
                component="commit_control",
            )
        
        if len(description) < self.min_description_length:
            fail_hard(
                "Description too short",
                component="commit_control",
                details={
                    "length": len(description),
                    "minimum": self.min_description_length,
                },
            )
        
        if len(description) > self.max_description_length:
            fail_hard(
                "Description too long",
                component="commit_control",
                details={
                    "length": len(description),
                    "maximum": self.max_description_length,
                },
            )
        
        return True
    
    def validate_body(self, body: Optional[str]) -> bool:
        """Validate commit body if provided."""
        if not body:
            return True
        
        for line in body.split('\n'):
            if len(line) > self.max_body_line_length:
                fail_hard(
                    "Body line too long",
                    component="commit_control",
                    details={
                        "max_length": self.max_body_line_length,
                        "line_length": len(line),
                    },
                )
        
        return True
    
    def generate_message(
        self,
        commit_type: str,
        scope: str,
        description: str,
        body: Optional[str] = None,
        breaking: bool = False,
    ) -> str:
        """
        Generate semantic commit message.
        
        Args:
            commit_type: Commit type (feat, fix, test, etc.)
            scope: Scope or area (general, core, api, etc.)
            description: Short description
            body: Detailed body (optional)
            breaking: Is breaking change
            
        Returns:
            Formatted commit message
        """
        # Validate inputs
        self.validate_commit_type(commit_type)
        self.validate_description(description)
        self.validate_body(body)
        
        # Build message
        lines = []
        
        # Header
        header = f"{commit_type}({scope}): {description}"
        if breaking:
            header += " BREAKING CHANGE"
        
        lines.append(header)
        
        # Body
        if body:
            lines.append("")
            lines.append(body)
        
        # Footer
        if breaking:
            lines.append("")
            lines.append("BREAKING CHANGE: This commit introduces breaking changes.")
        
        message = "\n".join(lines)
        
        self.logger.log(
            AuditLevel.INFO,
            "commit_control",
            "message_generated",
            details={
                "type": commit_type,
                "scope": scope,
                "breaking": breaking,
                "has_body": body is not None,
            },
        )
        
        return message
    
    def execute_commit(
        self,
        message: str,
        amend: bool = False,
    ) -> str:
        """
        Execute git commit.
        
        Args:
            message: Commit message
            amend: Amend previous commit
            
        Returns:
            Commit hash
        """
        # Validate atomicity
        self.check_atomic_commit()
        
        try:
            args = ['git', 'commit', '-m', message]
            if amend:
                args.insert(2, '--amend')
            
            result = subprocess.run(
                args,
                capture_output=True,
                text=True,
                timeout=30,
            )
            
            if result.returncode != 0:
                fail_hard(
                    "Commit failed",
                    component="commit_control",
                    details={"error": result.stderr},
                )
            
            # Extract commit hash from output
            output = result.stdout + result.stderr
            match = re.search(r'[a-f0-9]{7}', output)
            commit_hash = match.group(0) if match else "unknown"
            
            self.logger.log(
                AuditLevel.INFO,
                "commit_control",
                "commit_executed",
                details={
                    "hash": commit_hash,
                    "amend": amend,
                    "message_lines": len(message.split('\n')),
                },
                status="success",
            )
            
            return commit_hash
        except Exception as e:
            fail_hard(
                "Failed to execute commit",
                component="commit_control",
                details={"error": str(e)},
            )
    
    def get_report(self) -> str:
        """Get commit validation report."""
        staged = self._get_staged_files()
        
        lines = [
            "=== COMMIT VALIDATION REPORT ===",
            "",
            f"Staged Files: {len(staged)}",
            f"Allowed Types: {', '.join(sorted(self.allowed_types))}",
            "",
            "Message Rules:",
            f"  - Description: {self.min_description_length}-{self.max_description_length} chars",
            f"  - Body lines: max {self.max_body_line_length} chars",
            f"  - Format: type(scope): description",
        ]
        
        return "\n".join(lines)


# Global validator instance
_validator: Optional[CommitValidator] = None


def get_validator() -> CommitValidator:
    """Get or create validator instance."""
    global _validator
    if _validator is None:
        _validator = CommitValidator()
    return _validator


# Backward compatible functions
def get_current_files() -> List[str]:
    """Get staged files."""
    return get_validator()._get_staged_files()


def check_atomic_commit() -> bool:
    """Check atomic commit."""
    return get_validator().check_atomic_commit()


def generate_semantic_message(
    description: str,
    commit_type: str = 'chore',
    scope: str = 'general',
) -> str:
    """Generate semantic message."""
    return get_validator().generate_message(commit_type, scope, description)


def commit(
    description: str,
    commit_type: str = 'chore',
    scope: str = 'general',
) -> str:
    """Commit with semantic type."""
    validator = get_validator()
    message = validator.generate_message(commit_type, scope, description)
    return validator.execute_commit(message)


if __name__ == '__main__':
    validator = get_validator()
    print(validator.get_report())
