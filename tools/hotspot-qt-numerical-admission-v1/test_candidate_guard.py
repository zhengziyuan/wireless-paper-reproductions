"""Small deterministic in-memory checks, not a solver or reproduction run."""
import numpy as np
from candidate_guard import inspect


def call(q, d, old, new):
    return inspect(q, d, old, new, 1, 1., 10., [1.], covariance_rtol=1e-12,
                   psd_rtol=1e-12, power_rtol=1e-5, qos_atol=1e-5,
                   qt_atol=1e-5, tightness_atol=1e-12, objective_atol=1e-6, surrogate_atol=1e-6)


q = np.stack([np.eye(2), np.eye(2)]).astype(complex)
d = q.copy()
old = np.array([[0, 1], [0, 0]], dtype=complex)
candidate = np.array([[0, 0], [.5, 2]], dtype=complex)
original = old.copy()
good = call(q, d, old, old.copy())
assert good['accepted'] and all(good['checks'].values())
bad = call(q, d, old, candidate)
assert not bad['accepted'] and bad['checks']['candidate_true_qos']
assert bad['checks']['candidate_power'] and bad['checks']['candidate_objective_nondecrease']
assert not bad['checks']['candidate_fixed_auxiliary_qos']
assert abs(bad['candidate_fixed_auxiliary_qos'][0] + 1.25) < 1e-14
assert np.array_equal(old, original)

# A seemingly small relative factor mismatch can matter at high SINR.  The
# old Q-only computation falsely accepted: the CVX lower bound from actual D
# misses the 1e6 target by about 0.01 and is not tight to the supplied Q.
large_old = np.array([[0., 1000.], [0., 0.]], dtype=complex)
large_factor = d.copy(); large_factor[1] *= np.sqrt(1. - 1e-8)
large = inspect(q, large_factor, large_old, large_old.copy(), 1, 1., 1e6, [1e6],
                covariance_rtol=1e-7, psd_rtol=1e-12, power_rtol=0.,
                qos_atol=0., qt_atol=1e-6, tightness_atol=1e-6, objective_atol=0., surrogate_atol=0.)
assert large['checks']['covariance_and_factor'] and large['checks']['candidate_true_qos']
assert not large['checks']['old_auxiliary_tightness']
assert not large['checks']['candidate_fixed_auxiliary_qos'] and not large['accepted']
assert large['old_auxiliary_max_tightness_error'] > .009

# Subtracting 1e16 desired power from a floating sum can drop interference 1.
# The QoS is 1e16/(1+1)=5e15, not 1e16/(0+1).
cancel_old = np.array([[1., 1e8], [0., 0.]], dtype=complex)
cancel = inspect(q, d, cancel_old, cancel_old.copy(), 1, 1., 2e16, [7.5e15],
                 covariance_rtol=0., psd_rtol=0., power_rtol=0.,
                 qos_atol=0., qt_atol=0., tightness_atol=1., objective_atol=0., surrogate_atol=0.)
assert cancel['candidate_true_qos'][0] == 5e15
assert not cancel['checks']['candidate_true_qos'] and not cancel['accepted']

# Flip HU phase: true objective and QoS are unchanged, but fixed-z HU lower
# is -6, so log(1+lower) is undefined and the CVX candidate must be rejected.
old_flip = np.array([[2., 0.], [0., 1.]], dtype=complex)
new_flip = np.array([[-2., 0.], [0., 1.]], dtype=complex)
def special(old_state, new_state, target):
    return inspect(q, d, old_state, new_state, 1, 1., 10., [target],
                   covariance_rtol=0., psd_rtol=0., power_rtol=0., qos_atol=0.,
                   qt_atol=0., tightness_atol=1e-12, objective_atol=0., surrogate_atol=0.)
flipped = special(old_flip, new_flip, .2)
assert flipped['checks']['candidate_true_qos'] and flipped['checks']['candidate_objective_nondecrease']
assert not flipped['checks']['candidate_surrogate_log_domain'] and not flipped['accepted']

# A different candidate improves the true objective while satisfying both
# QoS tests, but lowers the valid fixed-auxiliary surrogate objective.
rotated = np.array([[1.1, 0.], [2., 1.]], dtype=complex)
drop = special(old_flip, rotated, .15)
assert drop['checks']['candidate_true_qos'] and drop['checks']['candidate_fixed_auxiliary_qos']
assert drop['checks']['candidate_objective_nondecrease'] and drop['checks']['candidate_surrogate_log_domain']
assert not drop['checks']['candidate_surrogate_objective_nondecrease'] and not drop['accepted']

# A tiny allowed negative eigenvalue becomes a negative interference power
# after multiplication by a large beam; it must never be silently counted as
# helpful interference even if the relative PSD/factor tolerances permit Q.
bad_q = q.copy(); bad_q[1] = np.diag([1., -1e-8])
bad_d = d.copy(); bad_d[1] = np.diag([1., 0.])
old_neg = np.array([[0., 1.], [0., 0.]], dtype=complex)
new_neg = np.array([[0., 1.], [1e4, 0.]], dtype=complex)
try:
    inspect(bad_q, bad_d, old_neg, new_neg, 1, 2., 2e8, [.5],
            covariance_rtol=1e-7, psd_rtol=1e-7, power_rtol=0., qos_atol=0.,
            qt_atol=0., tightness_atol=1e-12, objective_atol=0., surrogate_atol=0.)
except ValueError:
    pass
else:
    raise AssertionError('negative received interference was accepted')
invalid_qos = np.array([[0, 0], [.5, .5]], dtype=complex)
assert not call(q, d, old, invalid_qos)['checks']['candidate_true_qos']
over_power = old.copy(); over_power[:, 1] *= 4
assert not call(q, d, old, over_power)['checks']['candidate_power']
better_old = np.array([[.25, 1.2], [0, 0]], dtype=complex)
lower_hu = np.array([[0, 1.2], [0, 0]], dtype=complex)
assert not call(q, d, better_old, lower_hu)['checks']['candidate_objective_nondecrease']

inaccurate_factor = d.copy(); inaccurate_factor[1, 0, 0] = .5
assert not call(q, inaccurate_factor, old, old)['checks']['covariance_and_factor']
zero_q = q.copy(); zero_q[1] = 0.
try:
    call(zero_q, d, old, old)
except ValueError:
    pass
else:
    raise AssertionError('nonzero factor for zero covariance was accepted')
# At weak scale a wildly indefinite covariance can pass the old unit-floor
# threshold; the relative covariance/factor check must reject it.
weak = q.copy(); weak[1] = np.diag([1e-12, -9e-11])
clipped = d.copy(); clipped[1] = np.diag([1e-6, 0.])
try:
    result = call(weak, clipped, old, old)
    assert not result['accepted'] and not result['checks']['covariance_and_factor']
except ValueError:
    pass  # Invalid negative physical powers also fail closed.
assert np.array_equal(old, original)

# Direct Frobenius squaring would underflow for these entries. The normalized
# factor comparison must still detect a materially negative covariance.
ultraweak = q.copy(); ultraweak[1] = np.diag([1e-200, -9e-200])
ultra_factor = d.copy(); ultra_factor[1] = np.diag([1e-100, 0.])
try:
    result = call(ultraweak, ultra_factor, old, old)
    assert not result['accepted'] and not result['checks']['covariance_and_factor']
except ValueError:
    pass
print('PASS: fixed-QT, true-QoS, power, factors and immutability; synthetic only')
