import subprocess
from guard.failure import fail_hard

CORE_DIR = 'core'


def run_git(*args):
    result = subprocess.run(['git', *args], capture_output=True, text=True)
    if result.returncode != 0:
        fail_hard(f'git command failed: {result.stderr.strip()}')
    return result.stdout.strip()


def list_modified_files():
    return [p.strip() for p in run_git('diff', '--name-only').splitlines() if p.strip()]


def check_core_changes():
    modified = list_modified_files()
    forbidden = [p for p in modified if p.startswith(CORE_DIR + '/') or p == CORE_DIR]
    if forbidden:
        fail_hard(f'Core modification detected: {forbidden}')
    return True


if __name__ == '__main__':
    check_core_changes()
    print('no core changes detected')
