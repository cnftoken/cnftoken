import subprocess
import re
from guard.failure import fail_hard

ALLOWED_TYPES = {'feat', 'fix', 'test', 'chore'}


def get_current_files():
    result = subprocess.run(['git', 'status', '--porcelain'], capture_output=True, text=True, check=True)
    return [line for line in result.stdout.splitlines() if line]


def check_atomic_commit():
    files = get_current_files()
    if not files:
        fail_hard('No changes staged for commit.')
    return True


def generate_semantic_message(description, commit_type='chore', scope='general'):
    if commit_type not in ALLOWED_TYPES:
        fail_hard(f'Unsupported commit type: {commit_type}')
    if not description:
        fail_hard('Description cannot be empty')
    return f'{commit_type}({scope}): {description}'


def commit(description, commit_type='chore', scope='general'):
    check_atomic_commit()
    cmd = generate_semantic_message(description, commit_type, scope)
    subprocess.run(['git', 'commit', '-m', cmd], check=True)
    return cmd


if __name__ == '__main__':
    # No default commit to avoid accidental commit in automated environment.
    print('commit_control module loaded')
