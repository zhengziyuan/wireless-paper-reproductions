"""WORK cheaper SPD tangent chooser; the exact bound/candidate set is unchanged.

Two small floating selection rounds pick a tangent point; they do not decide
objective values, prune a node, certify feasibility, or relax an exact gate.
The inherited integer adjugate gradient recomputes the final global upper bound
exactly. A poor rounded chooser only loses possible pruning/performance.
"""
from fractions import Fraction as F
import numpy as np
from statistical_grid_exact_v9 import ExactStatisticalGrid as V9


class ExactStatisticalGrid(V9):
    def choose_weights(self, indices, remaining, r):
        if self._scheduled_weights is not None:
            old_indices, old_remaining, weights = self._scheduled_weights
            assert tuple(indices) == old_indices and tuple(remaining) == old_remaining
            return weights
        terms = self.numeric_terms[list(remaining)]; length = len(remaining)
        fixed = self.numeric_base.astype(complex, copy=True)
        if indices:
            fixed += self.numeric_terms[list(indices)].sum(axis=0)
        weights = np.full(length, r / length)
        def estimate(w):
            sigma = fixed + np.einsum('i,ijk->jk', w, terms)
            inverse = np.linalg.inv((sigma + sigma.conj().T) / 2)
            schur = 1 / np.diag(inverse).real
            coefficient = self.numeric_eta * schur * schur / (1 + self.numeric_eta * schur)
            gradient = (inverse * coefficient[None, :]) @ inverse
            scores = np.einsum('jk,ikj->i', gradient, terms).real
            bound_estimate = np.log1p(self.numeric_eta * schur).sum() + np.sort(scores)[-r:].sum() - w @ scores
            return float(bound_estimate), scores
        try:
            for _ in range(2):
                current, scores = estimate(weights)
                target = np.zeros(length); target[np.argsort(scores)[-r:]] = 1
                best, best_weights = current, weights
                for alpha in [.25, .5, .75, 1.]:
                    trial = (1 - alpha) * weights + alpha * target
                    score, _ = estimate(trial)
                    if np.isfinite(score) and score < best:
                        best, best_weights = score, trial
                if best_weights is weights:
                    break
                weights = best_weights
        except (np.linalg.LinAlgError, FloatingPointError):
            weights = np.full(length, r / length)
        # Exact hypersimplex restoration is a point construction, not a solver
        # convergence assertion. No floating estimate is a pruning certificate.
        Q = 1 << 32; scaled = np.clip(weights, 0, 1) * Q
        counts = [int(np.floor(v)) for v in scaled]; missing = r * Q - sum(counts)
        if missing >= 0:
            order = np.argsort(scaled - np.array(counts))[::-1]
            while missing:
                for i in order:
                    if counts[i] < Q:
                        counts[i] += 1; missing -= 1
                    if missing == 0:
                        break
        else:
            order = np.argsort(counts)[::-1]
            while missing:
                for i in order:
                    if counts[i] > 0:
                        counts[i] -= 1; missing += 1
                    if missing == 0:
                        break
        assert sum(counts) == r * Q and all(0 <= x <= Q for x in counts)
        return [F(v, Q) for v in counts]

    def upper(self, indices, remaining):
        # v8's inherited scheduler invokes V6.choose_weights explicitly. Route
        # only that chooser call to this class; all exact candidate/bound code
        # stays inherited and no source module is monkeypatched.
        from math import log
        from statistical_grid_exact_v3 import ExactStatisticalGrid as V3
        previous = V3.upper(self, indices, remaining); r = self.n - len(indices)
        if self.mode != 'ZF' or r < 2 or self.best is None or previous <= self.best:
            return previous
        weights = self.choose_weights(indices, remaining, r)
        estimate = self.estimate_log_upper(indices, remaining, weights)
        if not np.isfinite(estimate) or estimate >= log(self.best.numerator) - log(self.best.denominator):
            self.float_estimate_skips += 1
            return previous
        self.optional_proof_attempts += 1
        self._scheduled_weights = (tuple(indices), tuple(remaining), weights)
        try:
            candidate = self.supporting_upper(indices, remaining)
        finally:
            self._scheduled_weights = None
        assert isinstance(candidate, F)
        if candidate < previous:
            self.support_improved += 1
        return min(previous, candidate)
