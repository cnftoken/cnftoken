import sys


class CriticalFailure(Exception):
    pass


def fail(msg: str):
    raise CriticalFailure(msg)


def fail_hard(msg: str):
    print(f'FATAL: {msg}', file=sys.stderr)
    raise CriticalFailure(msg)
