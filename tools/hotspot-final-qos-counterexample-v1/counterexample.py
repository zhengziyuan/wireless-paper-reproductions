"""Exact counterexample to the final paper's printed statistical QoS (36d).

This checks the literal scalar specialization, not a simulation or a fitted
author parameter set. Every comparison is rational and no files are read or
written. Dimensions: J=2, U=1, K=1, N=1; HU beam w1=0, NHU beam w2=2.
"""
from fractions import Fraction as F
import json


def check():
    beta = gamma = mu = noise_variance = F(1)
    hu_beam, nhu_beam = F(0), F(2)
    power_limit = F(4)
    # Eq. (33b), with scalar unit LoS. The 1x1 covariance is exactly one.
    psi = mu * (1 + beta) / (1 + beta)
    original_signal = psi * nhu_beam**2
    original_interference = F(0)  # no other NHU in K
    original_sinr = original_signal / (original_interference + noise_variance)

    # Eq. (36d) and the following augmented definitions. Its left side is
    # sqrt(1+beta/gamma)*hbar^H*w_k = sqrt(left_squared).
    left_squared = (1 + beta/gamma) * nhu_beam**2
    # For each stream: |sqrt(beta) hbar_j^H w_j|^2 + |1_N^T w_j|^2.
    # The final augmented block is |i sqrt(1/gamma+1) 1_N^T w_k|^2;
    # the last b entry is |sigma sqrt((1+beta)/mu)|^2. N=1 and hbar_j=1.
    right_norm_squared = ((beta + 1) * (hu_beam**2 + nhu_beam**2)
                          + (1/gamma + 1) * nhu_beam**2
                          + noise_variance * (1+beta)/mu)
    # Exact comparisons avoid numerical square-root approximations.
    original_feasible = (hu_beam**2 + nhu_beam**2 <= power_limit
                         and original_sinr >= gamma)
    printed_36d_holds = left_squared >= right_norm_squared**2
    hypothetical_unsquared_holds = left_squared >= right_norm_squared
    assert original_feasible and not printed_36d_holds and not hypothetical_unsquared_holds
    return {
        'original_sinr': str(original_sinr), 'target': str(gamma),
        'transmit_power': str(hu_beam**2 + nhu_beam**2),
        'power_limit': str(power_limit), 'left_squared': str(left_squared),
        'printed_right_norm_squared': str(right_norm_squared),
        'original_qos_feasible': original_feasible,
        'printed_36d_holds': printed_36d_holds,
        'unsquaring_rhs_alone_holds': hypothetical_unsquared_holds,
        'full_paper_pass': False,
    }


if __name__ == '__main__':
    print(json.dumps(check(), indent=2))
