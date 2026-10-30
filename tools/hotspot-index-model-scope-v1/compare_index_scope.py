"""Exact K-only versus J-minus-k counterexample; no original-run claim."""
from fractions import Fraction as F
import json


def check():
    covariance = F(1)
    hu = F(1)
    nhu = F(1)
    noise = F(1)
    target = F(3, 4)
    power_limit = F(2)
    signal = covariance * nhu**2
    printed = signal / noise  # exactly one NHU; K excluding k is empty
    physical = signal / (covariance * hu**2 + noise)
    total = hu**2 + nhu**2
    assert total <= power_limit and printed >= target and physical < target
    return {'scope': 'constructed scalar example, not a historical experiment',
            'printed_K_only_ratio': str(printed),
            'physical_J_minus_k_ratio': str(physical), 'target': str(target),
            'total_power': str(total), 'power_limit': str(power_limit),
            'printed_constraint_met': True, 'physical_constraint_met': False,
            'exact_expectation_of_instantaneous_SINR_claimed': False,
            'full_paper_pass': False}


if __name__ == '__main__':
    print(json.dumps(check(), indent=2))
