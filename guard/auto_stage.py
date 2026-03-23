import subprocess
import pathlib
from guard.failure import fail_hard


def run_git(*args):
    result = subprocess.run(['git', *args], capture_output=True, text=True)
    if result.returncode != 0:
        fail_hard(f'git command failed: {result.stderr.strip()}')
    return result.stdout.strip().splitlines()


def auto_stage():
    changed = run_git('status', '--porcelain')
    staged = []
    for line in changed:
        if not line:
            continue
        status = line[:2]
        path = line[3:]
        if path.startswith('core/'):
            continue
        if path.startswith('.git/'):
            continue
        staged.append(path)
    if staged:
        subprocess.run(['git', 'add', *staged], check=True)
    return staged


if __name__ == '__main__':
    staged = auto_stage()
    print('auto staged files:', staged)
