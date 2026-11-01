"""WORK exact SAME supporting bound: common-denominator adjugate gradient.

If Sigma=A/D, adj(A)=J, det(A)=delta, then
G=sum_u eta_u*D/[J_uu*(D*J_uu+eta_u*delta)] * J_:u J_u:.
All matrix products and point scores have one common integer denominator;
they need no repeated Fraction normalizations. This is an algebraic identity,
not an approximate bound, new objective, or change to a production engine.
"""
from fractions import Fraction as F
from math import lcm
from statistical_grid_exact_v3 import imul, isub
from statistical_grid_exact_v5 import exp_upper
from statistical_grid_exact_v8 import ExactStatisticalGrid as V8


def adjugate_spd_integer(matrix):
    m = len(matrix)
    a = [row[:] + [(int(i == j), 0) for j in range(m)] for i, row in enumerate(matrix)]
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
    return previous, [row[m:] for row in a]


class ExactStatisticalGrid(V8):
    def supporting_upper(self, indices, remaining):
        r = self.n - len(indices); m = self.m; Q = 1 << 32
        weights = self.choose_weights(indices, remaining, r)
        counts = []
        for weight in weights:
            count = weight * Q; assert count.denominator == 1
            counts.append(count.numerator)
        assert sum(counts) == r * Q and all(0 <= x <= Q for x in counts)
        D = self.integer_scale * Q
        diagonal = [Q * (self.integer_base[u] + sum(self.integer_diagonal[i][u] for i in indices)) +
                    sum(count * self.integer_diagonal[i][u] for count, i in zip(counts, remaining)) for u in range(m)]
        off = {}
        for pair, terms in self.integer_terms.items():
            off[pair] = (Q * sum(terms[i][0] for i in indices) + sum(count * terms[i][0] for count, i in zip(counts, remaining)),
                         Q * sum(terms[i][1] for i in indices) + sum(count * terms[i][1] for count, i in zip(counts, remaining)))
        a = [[(diagonal[u], 0) if u == v else off[u, v] if u < v else (off[v, u][0], -off[v, u][1]) for v in range(m)] for u in range(m)]
        determinant, adjugate = adjugate_spd_integer(a)
        product = F(1); coefficients = []; denominator = 1
        for u in range(m):
            diag = adjugate[u][u]; assert diag[1] == 0 and diag[0] > 0
            product *= 1 + self.eta[u] * F(determinant, D * diag[0])
            coefficient = self.eta[u] * D / (diag[0] * (D * diag[0] + self.eta[u] * determinant))
            coefficients.append(coefficient); denominator = lcm(denominator, coefficient.denominator)
        scaled = [c.numerator * (denominator // c.denominator) for c in coefficients]
        gradient = []
        for u in range(m):
            row = []
            for v in range(m):
                terms = [imul(adjugate[u][j], adjugate[j][v]) for j in range(m)]
                row.append((sum(c * z[0] for c, z in zip(scaled, terms)), sum(c * z[1] for c, z in zip(scaled, terms))))
            gradient.append(row)
        scores = []
        for i in remaining:
            score = sum(gradient[u][u][0] * self.integer_diagonal[i][u] for u in range(m))
            for u in range(m):
                for v in range(u + 1, m):
                    term = self.integer_terms[u, v][i]
                    score += 2 * imul(gradient[u][v], (term[0], -term[1]))[0]
            scores.append(score)
        numerator = Q * sum(sorted(scores, reverse=True)[:r]) - sum(c * s for c, s in zip(counts, scores))
        assert numerator >= 0
        increment = F(numerator, denominator * self.integer_scale * Q)
        self.support_calls += 1
        return product * exp_upper(increment)
