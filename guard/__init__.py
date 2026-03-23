"""Guard package exports."""
from .core_integrity import compute_core_hash, validate_core_hash, write_core_hash
from .change_validator import check_core_changes
from .dual_execution import validate_two_runs
from .token_drift import validate_token_drift
from .auto_stage import auto_stage
from .commit_control import check_atomic_commit, generate_semantic_message
from .failure import CriticalFailure, fail_hard
