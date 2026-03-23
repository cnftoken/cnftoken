import yaml
import sys
from guard.failure import CriticalFailure


def load_rules(path='policy/rules.yaml'):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except Exception as e:
        raise CriticalFailure(f'Failed to load policy rules: {e}')


def enforce_core_immutability(rules):
    if rules.get('core_immutable'):
        from guard.change_validator import check_core_changes

        check_core_changes()


def enforce_all():
    rules = load_rules()
    enforce_core_immutability(rules)
    return rules


if __name__ == '__main__':
    enforce_all()
    print('policy engine: all rules satisfied')
