from guard.failure import fail_hard


def compute_token_drift(prev, current):
    if prev <= 0:
        fail_hard('Invalid previous token count for drift detection')
    drift = abs(current - prev) / prev
    return drift


def validate_token_drift(prev, current, threshold=0.5):
    drift = compute_token_drift(prev, current)
    if drift > threshold:
        fail_hard(f'Token drift too high: {drift:.2f} > {threshold}')
    return True


if __name__ == '__main__':
    validate_token_drift(1000, 1050, threshold=0.5)
    print('token drift validation passed')
