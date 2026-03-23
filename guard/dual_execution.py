from guard.failure import fail_hard


def validate_two_runs(func, *args, **kwargs):
    first = func(*args, **kwargs)
    second = func(*args, **kwargs)
    if first != second:
        fail_hard('Dual execution validator failed: inconsistent results between runs.')
    return True


if __name__ == '__main__':
    # Example invocation
    import guard.core_integrity as ci
    validate_two_runs(ci.compute_core_hash)
    print('dual execution validation passed')
