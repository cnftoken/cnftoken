import os
import hashlib
from guard.failure import fail_hard

HASH_PATH = 'guard/core_hash.sha256'
CORE_DIR = 'core'


def compute_core_hash():
    sha = hashlib.sha256()
    if not os.path.isdir(CORE_DIR):
        return None
    for root, dirs, files in os.walk(CORE_DIR):
        dirs.sort()
        files.sort()
        for file in files:
            path = os.path.join(root, file)
            with open(path, 'rb') as f:
                data = f.read()
                sha.update(path.encode('utf-8'))
                sha.update(data)
    return sha.hexdigest()


def write_core_hash():
    value = compute_core_hash() or ''
    with open(HASH_PATH, 'w', encoding='utf-8') as f:
        f.write(value)
    return value


def validate_core_hash():
    expected = None
    if os.path.exists(HASH_PATH):
        with open(HASH_PATH, 'r', encoding='utf-8') as f:
            expected = f.read().strip()
    current = compute_core_hash() or ''
    if expected != current:
        fail_hard('Core integrity hash mismatch. Core directory may have been modified.')
    return True


if __name__ == '__main__':
    # initialize if missing
    if not os.path.exists(HASH_PATH):
        write_core_hash()
        print('core hash initialized')
    else:
        validate_core_hash()
        print('core hash validated')
