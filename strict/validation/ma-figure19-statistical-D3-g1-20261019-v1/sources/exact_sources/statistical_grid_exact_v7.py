"""WORK exact Eq39 search: float estimates schedule, never certify, a bound.

Skipping an optional bound computation merely retains the already proved v3
upper bound. Any pruning still compares exact Fractions. A false float estimate
can cost speed/pruning, but cannot eliminate a valid candidate. This is not a
fixed ordered per-antenna MC protocol or a production-engine change.
"""
from fractions import Fraction as F
from math import log
import numpy as np
from statistical_grid_exact_v3 import ExactStatisticalGrid as V3
from statistical_grid_exact_v6 import ExactStatisticalGrid as V6


class ExactStatisticalGrid(V6):
    def __init__(self, c, n, D, mode):
        super().__init__(c, n, D, mode)
        self.optional_proof_attempts = 0
        self.float_estimate_skips = 0
        self._scheduled_weights = None

    def choose_weights(self, indices, remaining, r):
        if self._scheduled_weights is not None:
            old_indices, old_remaining, weights = self._scheduled_weights
            assert tuple(indices) == old_indices and tuple(remaining) == old_remaining
            return weights
        return super().choose_weights(indices, remaining, r)

    def estimate_log_upper(self, indices, remaining, weights):
        """Only decide whether to spend time constructing an exact certificate."""
        fixed = self.numeric_base.astype(complex, copy=True)
        if indices:
            fixed += self.numeric_terms[list(indices)].sum(axis=0)
        terms = self.numeric_terms[list(remaining)]
        w = np.array([float(x) for x in weights])
        sigma = fixed + np.einsum('i,ijk->jk', w, terms)
        try:
            with np.errstate(all='raise'):
                inv = np.linalg.inv((sigma + sigma.conj().T) / 2)
                s = 1 / np.diag(inv).real
                if not np.all(s > 0):
                    return np.inf
                a = self.numeric_eta * s * s / (1 + self.numeric_eta * s)
                g = (inv * a[None, :]) @ inv
                scores = np.einsum('jk,ikj->i', g, terms).real
                r = self.n - len(indices)
                increment = np.sort(scores)[-r:].sum() - w @ scores
                return float(np.log1p(self.numeric_eta * s).sum() + increment)
        except (FloatingPointError, np.linalg.LinAlgError):
            return np.inf

    def upper(self, indices, remaining):
        previous = V3.upper(self, indices, remaining)
        r = self.n - len(indices)
        if self.mode != 'ZF' or r < 2 or self.best is None or previous <= self.best:
            return previous
        weights = V6.choose_weights(self, indices, remaining, r)
        estimate = self.estimate_log_upper(indices, remaining, weights)
        # This gate SKIPS ONLY an optional proof, not a candidate or subtree.
        # Large-int logs are also estimates; their rounding can only affect cost.
        incumbent_estimate = log(self.best.numerator) - log(self.best.denominator)
        if not np.isfinite(estimate) or estimate >= incumbent_estimate:
            self.float_estimate_skips += 1
            return previous
        self.optional_proof_attempts += 1
        self._scheduled_weights = (tuple(indices), tuple(remaining), weights)
        try:
            candidate = V6.supporting_upper(self, indices, remaining)
        finally:
            self._scheduled_weights = None
        assert isinstance(candidate, F)
        if candidate < previous:
            self.support_improved += 1
        return min(previous, candidate)
