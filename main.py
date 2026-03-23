import sys
from guard.failure import fail_hard
from guard.core_integrity import validate_core_hash, write_core_hash
from guard.change_validator import check_core_changes
from guard.dual_execution import validate_two_runs
from guard.token_drift import validate_token_drift
from guard.auto_stage import auto_stage
from guard.commit_control import check_atomic_commit, generate_semantic_message
from policy.engine import enforce_all


def run_all_checks():
    # 1. policy engine
    rules = enforce_all()

    # 2. guard system
    if rules.get('guard_system'):
        # Initialize core hash if missing, else validate
        from pathlib import Path
        from guard.core_integrity import HASH_PATH

        if not Path(HASH_PATH).exists():
            write_core_hash()
        else:
            validate_core_hash()
        check_core_changes()
        validate_two_runs(validate_core_hash)
        validate_token_drift(1000, 1050, threshold=0.5)

    # 3. auto-stage
    staged = auto_stage()
    print('auto-stage allowed files:', staged)

    # 4. commit control strictness
    check_atomic_commit()
    msg = generate_semantic_message('governance checks passed', 'test', 'governance')
    print('semantic commit template:', msg)

    print('All checks passed. System is compliant.')


if __name__ == '__main__':
    try:
        run_all_checks()
    except Exception as e:
        fail_hard(f'Execution terminated due to failure: {e}')
    sys.exit(0)
