"""Enhanced failure handling with context preservation and exit codes."""
import sys
import traceback
from typing import Optional, Dict, Any
from enum import Enum


class ExitCode(Enum):
    """Standard exit codes for guard failures."""
    GENERAL = 1
    VALIDATION = 2
    INTEGRITY = 3
    SECURITY = 4
    PERMISSION = 5
    RESOURCE = 6
    CONFIGURATION = 7
    TIMEOUT = 8
    INCONSISTENCY = 9
    UNKNOWN = 127


class FailureContext:
    """Context information for failures."""
    def __init__(
        self,
        message: str,
        component: str = "unknown",
        exit_code: ExitCode = ExitCode.GENERAL,
        details: Optional[Dict[str, Any]] = None,
        parent_exception: Optional[Exception] = None,
    ):
        self.message = message
        self.component = component
        self.exit_code = exit_code
        self.details = details or {}
        self.parent_exception = parent_exception
        self.stack_trace = traceback.format_exc() if parent_exception else None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert context to dictionary."""
        return {
            "message": self.message,
            "component": self.component,
            "exit_code": self.exit_code.value,
            "exit_code_name": self.exit_code.name,
            "details": self.details,
            "has_parent": self.parent_exception is not None,
            "parent_type": type(self.parent_exception).__name__ if self.parent_exception else None,
        }


class CriticalFailure(Exception):
    """Enhanced critical failure exception with context."""
    
    def __init__(
        self,
        message: str,
        component: str = "unknown",
        exit_code: ExitCode = ExitCode.GENERAL,
        details: Optional[Dict[str, Any]] = None,
        parent_exception: Optional[Exception] = None,
    ):
        self.context = FailureContext(
            message=message,
            component=component,
            exit_code=exit_code,
            details=details,
            parent_exception=parent_exception,
        )
        super().__init__(message)
    
    def get_context(self) -> FailureContext:
        """Get failure context."""
        return self.context
    
    def get_exit_code(self) -> int:
        """Get exit code value."""
        return self.context.exit_code.value


def fail(msg: str, component: str = "unknown") -> None:
    """
    Raise critical failure (with less aggressive output).
    
    Args:
        msg: Error message
        component: Component that failed
    """
    raise CriticalFailure(
        message=msg,
        component=component,
        exit_code=ExitCode.GENERAL,
    )


def fail_hard(
    msg: str,
    component: str = "unknown",
    exit_code: ExitCode = ExitCode.GENERAL,
    details: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Raise critical failure and output to stderr.
    
    Args:
        msg: Error message
        component: Component that failed
        exit_code: Exit code to use (ExitCode enum)
        details: Additional failure details
    """
    # Build error message
    error_lines = [
        f"FATAL [{component.upper()}]: {msg}",
    ]
    
    # Add details if provided
    if details:
        for key, value in details.items():
            if isinstance(value, (dict, list)):
                error_lines.append(f"  {key}: {str(value)[:100]}")
            else:
                error_lines.append(f"  {key}: {value}")
    
    # Output to stderr
    print("\n".join(error_lines), file=sys.stderr)
    
    raise CriticalFailure(
        message=msg,
        component=component,
        exit_code=exit_code,
        details=details,
    )


def fail_validation(msg: str, details: Optional[Dict[str, Any]] = None) -> None:
    """Fail due to validation error."""
    fail_hard(msg, component="validation", exit_code=ExitCode.VALIDATION, details=details)


def fail_integrity(msg: str, details: Optional[Dict[str, Any]] = None) -> None:
    """Fail due to integrity check failure."""
    fail_hard(msg, component="integrity", exit_code=ExitCode.INTEGRITY, details=details)


def fail_security(msg: str, details: Optional[Dict[str, Any]] = None) -> None:
    """Fail due to security violation."""
    fail_hard(msg, component="security", exit_code=ExitCode.SECURITY, details=details)


def fail_permission(msg: str, details: Optional[Dict[str, Any]] = None) -> None:
    """Fail due to permission error."""
    fail_hard(msg, component="permission", exit_code=ExitCode.PERMISSION, details=details)


def fail_resource(msg: str, details: Optional[Dict[str, Any]] = None) -> None:
    """Fail due to resource issue."""
    fail_hard(msg, component="resource", exit_code=ExitCode.RESOURCE, details=details)


def fail_configuration(msg: str, details: Optional[Dict[str, Any]] = None) -> None:
    """Fail due to configuration error."""
    fail_hard(msg, component="configuration", exit_code=ExitCode.CONFIGURATION, details=details)


def fail_timeout(msg: str, details: Optional[Dict[str, Any]] = None) -> None:
    """Fail due to timeout."""
    fail_hard(msg, component="timeout", exit_code=ExitCode.TIMEOUT, details=details)


def fail_inconsistency(msg: str, details: Optional[Dict[str, Any]] = None) -> None:
    """Fail due to inconsistency."""
    fail_hard(msg, component="inconsistency", exit_code=ExitCode.INCONSISTENCY, details=details)
