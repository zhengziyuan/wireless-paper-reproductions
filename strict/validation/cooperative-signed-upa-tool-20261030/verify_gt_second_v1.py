"""Check saved U6/K1 source covariance and both possible fixed handednesses.

This reads the existing finite NPZ only and uses author-geometry coordinates
reconstructed in verify_links_v1; the NPZ does not bind those coordinates.
No channel realizations or files are created. This is not a paper-level
numerical experiment or model acceptance.
"""
from pathlib import Path
import numpy as np
from gt_second_v1 import candidate_gt_second
# This source-geometry fixture and its previously saved LOS checks run on import.
from verify_links_v1 import S, U, R, K, G, Bs, As, Br, Ar, kwargs
from links_v1 import generate


def rejects(call):
    try:
        call()
    except ValueError:
        return
    raise AssertionError('invalid saved-input contract was accepted')


canonical = (Path(__file__).resolve().parent.parent /
             'cooperative-author-U6-final-ground10-dual-full8-20261019-v1' /
             'inputs' / 'canonical-eleven-arrays-and-limits.npz')
with np.load(canonical, allow_pickle=False) as f:
    d, q = f['d_mean'].copy(), f['gt_second'].copy()
original_d, original_q = d.copy(), q.copy()
assert np.array_equal(U[2], K[0])
for handedness in (1, -1):
    x = generate(S, U, R, K, G, Bs, As, Br, Ar,
                 sat_handedness=handedness, **kwargs)
    a = x['a_N_K']
    q_new, receipt = candidate_gt_second(d, q, a, U, K, [2], 100)
    # Independently reconstruct the candidate, without using the phase-rotation
    # formula. Preserve the saved mu inferred from its actual diagonal.
    for j in range(3):
        mu = np.trace(q[j, 0]).real / q.shape[-1]
        v = a[j, 0] / a[j, 0, 0]
        expected = mu / 101 * (np.eye(16) + 100 * np.outer(v, v.conj()))
        np.testing.assert_allclose(q_new[j, 0], expected, atol=1e-12*mu, rtol=1e-10)
    print(f'handedness {handedness:+d}: co-location error '
          f'{receipt["max_user_separation_m"]:.3g} m; '
          f'model max relative error {max(t["source_model_relative_error"] for t in receipt["arrays"]):.3g}; '
          f'old/new minimum eigenvalues '
          f'{min(t["old_min_eigenvalue"] for t in receipt["arrays"]):.6g}/'
          f'{min(t["new_min_eigenvalue"] for t in receipt["arrays"]):.6g}; '
          f'max relative covariance change '
          f'{max(t["relative_matrix_change"] for t in receipt["arrays"]):.6g}')
assert np.array_equal(d, original_d) and np.array_equal(q, original_q)
# These checks exercise specific scientific input invariants, not a controller.
bad_geo = K.copy(); bad_geo[0, 0] += 1
rejects(lambda: candidate_gt_second(d, q, a, U, bad_geo, [2], 100))
bad_q = q.copy(); bad_q[0, 0, 0, 1] += 0.01
rejects(lambda: candidate_gt_second(d, bad_q, a, U, K, [2], 100))
rejects(lambda: candidate_gt_second(d, q, a, U, K, [2], 10))
print('PASS: original arrays untouched; conditional covariance checks only')
