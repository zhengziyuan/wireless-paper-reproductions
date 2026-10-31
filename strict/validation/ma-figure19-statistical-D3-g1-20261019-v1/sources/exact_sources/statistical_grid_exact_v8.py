"""WORK SAME exact bound: fraction-free integer inverse, no model change."""
from fractions import Fraction as F
from math import lcm, log
import numpy as np
from statistical_grid_exact import add, mul, conj, ZERO
from statistical_grid_exact_v3 import ExactStatisticalGrid as V3, imul, isub
from statistical_grid_exact_v5 import exp_upper
from statistical_grid_exact_v6 import ExactStatisticalGrid as V6
from statistical_grid_exact_v7 import ExactStatisticalGrid as V7


def full_inverse_fraction_free(matrix):
    """Exact Montante/Bareiss elimination on [D*Sigma | I].

    SPD leading pivots are positive real, so no pivot permutation or rounded
    division occurs. At termination the left block is det(A)*I, the right block
    adj(A); Sigma^-1 = D*adj(A)/det(A). Every integer division is asserted exact.
    """
    m = len(matrix); scale = 1
    for row in matrix:
        for z in row:
            scale = lcm(scale, z[0].denominator, z[1].denominator)
    def integer(z):
        assert scale % z[0].denominator == 0 and scale % z[1].denominator == 0
        return (z[0].numerator * (scale // z[0].denominator), z[1].numerator * (scale // z[1].denominator))
    a = [[integer(matrix[i][j]) for j in range(m)] + [(int(i == j), 0) for j in range(m)] for i in range(m)]
    previous = 1
    for k in range(m):
        pivot = a[k][k]; assert pivot[1] == 0 and pivot[0] > 0
        for i in range(m):
            if i == k:
                continue
            off = a[i][k]
            for j in range(2 * m):
                if j == k:
                    continue
                z = isub(imul(pivot, a[i][j]), imul(off, a[k][j]))
                assert z[0] % previous == 0 and z[1] % previous == 0
                a[i][j] = (z[0] // previous, z[1] // previous)
            a[i][k] = (0, 0)
        previous = pivot[0]
    assert all(a[i][j] == (previous if i == j else 0, 0) for i in range(m) for j in range(m))
    return [[(F(scale * a[i][m + j][0], previous), F(scale * a[i][m + j][1], previous)) for j in range(m)] for i in range(m)]


class ExactStatisticalGrid(V7):
    def supporting_upper(self, indices, remaining):
        r = self.n - len(indices); m = self.m
        weights = self.choose_weights(indices, remaining, r); partial = self.partial(indices)
        diagonal = [self.base[u] + sum(self.diagonal[i][u] for i in indices) + sum(w * self.diagonal[i][u] for w, i in zip(weights, remaining)) for u in range(m)]
        off = {pair: (s[0] + sum(w * self.terms[pair][i][0] for w, i in zip(weights, remaining)),
                      s[1] + sum(w * self.terms[pair][i][1] for w, i in zip(weights, remaining))) for pair, s in partial.items()}
        sigma = [[(diagonal[u], F(0)) if u == v else off[u, v] if u < v else conj(off[v, u]) for v in range(m)] for u in range(m)]
        inverse = full_inverse_fraction_free(sigma)
        schur = [1 / inverse[u][u][0] for u in range(m)]
        product = F(1)
        for u in range(m):
            product *= 1 + self.eta[u] * schur[u]
        coefficient = [self.eta[u] * schur[u] ** 2 / (1 + self.eta[u] * schur[u]) for u in range(m)]
        gradient = []
        for u in range(m):
            row = []
            for v in range(m):
                z = ZERO
                for j in range(m):
                    q = mul(inverse[u][j], inverse[j][v]); z = add(z, (coefficient[j] * q[0], coefficient[j] * q[1]))
                row.append(z)
            gradient.append(row)
        scores = []
        for i in remaining:
            value = sum(gradient[u][u][0] * self.diagonal[i][u] for u in range(m))
            for u in range(m):
                for v in range(u + 1, m):
                    value += 2 * mul(gradient[u][v], conj(self.terms[u, v][i]))[0]
            scores.append(value)
        increment = sum(sorted(scores, reverse=True)[:r]) - sum(w * s for w, s in zip(weights, scores))
        assert increment >= 0
        self.support_calls += 1
        return product * exp_upper(increment)

    def upper(self, indices, remaining):
        previous = V3.upper(self, indices, remaining); r = self.n - len(indices)
        if self.mode != 'ZF' or r < 2 or self.best is None or previous <= self.best:
            return previous
        weights = V6.choose_weights(self, indices, remaining, r)
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
