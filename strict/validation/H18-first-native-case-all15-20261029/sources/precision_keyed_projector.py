"""Same full finite-CN projector integral with bounded shared-node memoization.

Every original upper-triangle entry still calls the original mp.quad rule,
breakpoints and precision. Only repeated common integrand terms at exactly
the same MP point and active working precision are reused. No approximation,
new quadrature rule, LoS replacement or truncated matrix is introduced.
"""
from collections import OrderedDict


def single_projector(mp, mean, variance, *, max_entries=8192, statistics=None):
    if mp.dps not in (80, 100) or len(mean) != 16 or len(variance) != 16:
        raise ValueError('Full original16 dimensions and MP80/MP100 required')
    if type(max_entries) is not int or not 1 <= max_entries <= 16384:
        raise ValueError('Explicit bounded common-node cache required')
    N = 16
    scale = mp.fsum(abs(mean[n])**2 + variance[n] for n in range(N))
    if not scale > 0:
        raise ValueError('Nonzero complete original finite-CN channel required')
    m = [mp.conj(mean[n])/mp.sqrt(scale) for n in range(N)]
    v = [variance[n]/scale for n in range(N)]
    if not all(a > 0 for a in v):
        raise ValueError('No erased finite variance or LoS replacement')
    common = OrderedDict()
    stat = dict(quad_calls=0, integrand_calls=0, common_evaluations=0,
                exact_common_hits=0, evictions=0, peak_entries=0,
                distinct_active_precisions=set())

    def terms(s):
        # mp.quad raises working precision internally. Nominal dps alone
        # would incorrectly mix values computed at different precisions.
        key = (int(mp.prec), tuple(s._mpf_))
        stat['distinct_active_precisions'].add(key[0])
        if key in common:
            stat['exact_common_hits'] += 1
            return common[key]
        t = s/(1-s)
        iv = [1/(1+t*a) for a in v]
        lap = mp.exp(-mp.fsum(mp.log1p(t*a) for a in v)
                     -t*mp.fsum(abs(m[n])**2*iv[n] for n in range(N)))
        if len(common) == max_entries:
            common.popitem(last=False)
            stat['evictions'] += 1
        common[key] = (iv, lap)
        stat['common_evaluations'] += 1
        stat['peak_entries'] = max(stat['peak_entries'], len(common))
        return iv, lap

    P = mp.matrix(N, N)
    for i in range(N):
        for j in range(i, N):
            def integrand(s):
                stat['integrand_calls'] += 1
                if s == 1:
                    return mp.mpf(0)
                iv, lap = terms(s)
                entry = m[i]*mp.conj(m[j])*iv[i]*iv[j]
                if i == j:
                    entry += v[i]*iv[i]
                return lap*entry/(1-s)**2
            P[i, j] = mp.quad(integrand, [0, mp.mpf('0.5'), mp.mpf('0.9'), mp.mpf('0.99'), 1])
            stat['quad_calls'] += 1
            P[j, i] = mp.conj(P[i, j])
    if statistics is not None:
        stat['distinct_active_precisions'] = sorted(stat['distinct_active_precisions'])
        statistics.update(stat)
    return P
