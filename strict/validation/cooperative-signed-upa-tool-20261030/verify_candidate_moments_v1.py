"""Check all saved U6/K1 links in memory; no new optimizer or channel draws."""
from pathlib import Path
import numpy as np
from links_v1 import generate
from candidate_moments_v1 import construct
from verify_links_v1 import S, U, R, K, G, Bs, As, Br, Ar, kwargs, folded

root = Path(__file__).resolve().parent.parent
path = (root / 'cooperative-author-U6-final-ground10-dual-full8-20261019-v1' /
        'inputs' / 'canonical-eleven-arrays-and-limits.npz')
with np.load(path, allow_pickle=False) as f:
    saved = {k: f[k].copy() for k in f.files}
baseline = {k: v.copy() for k, v in saved.items()}

# Source-folded orientations independently reconstructed from the supplied
# initializer's acos convention. Common propagation phases cancel in the
# elementwise ratios used by construct(). This geometry is reconstructed; the
# saved NPZ itself does not bind coordinates.
old_d = np.empty((3, 6, 16), complex)
old_g = np.empty((3, 6, 16, 25), complex)
old_r = np.empty((6, 25), complex)
old_geo_g = np.empty((6, 25), complex)
for j in range(3):
    for u in range(6):
        a = folded(Bs[j], As[j], U[u]-S[j], 4, 4, 10)
        b = folded(Bs[j], As[j], R[u]-S[j], 4, 4, 10)
        c = folded(Br[u], Ar[u], S[j]-R[u], 5, 5, 40)
        old_d[j, u] = a
        old_g[j, u] = np.outer(b, c.conj())
for u in range(6):
    old_r[u] = folded(Br[u], Ar[u], U[u]-R[u], 5, 5, 40)
    old_geo_g[u] = folded(Br[u], Ar[u], G-R[u], 5, 5, 40).conj()
source = {'H_NN_LOS': old_d, 'H_NR_LOS': old_g,
          'H_RU_LOS': old_r, 'H_GR_LOS': old_geo_g}
# Explicit conservative thresholds for this one reconstructed geometry.  In
# particular d and r have near-boresight discrepancies, not exact source
# reconstruction. These thresholds are not paper-accuracy tolerances.
threshold = {'d_mean': 3e-6, 'G_mean': 2e-9,
             'r_mean': 2e-5, 'geo_G_mean': 2e-10}

def rejects(call):
    try:
        call()
    except ValueError:
        return
    raise AssertionError('invalid candidate input was accepted')

for handedness, ris_hand in ((1, 1), (1, -1), (-1, 1), (-1, -1)):
    x = generate(S, U, R, K, G, Bs, As, Br, Ar,
                 sat_handedness=handedness, ris_handedness=ris_hand, **kwargs)
    candidate, info = construct(saved, x, source, U, K, [2], 100,
                                source_tolerances=threshold)
    assert info['coincident_los_relative_max_error'] <= info['coincident_los_tolerance']
    for key in ('d_var', 'G_var', 'r_var', 'geo_d_mean', 'geo_d_var',
                'geo_G_var', 'power_limit', 'interference_limit'):
        assert np.array_equal(candidate[key], saved[key])
        assert not np.shares_memory(candidate[key], saved[key])
    for key in ('d_mean', 'G_mean', 'r_mean', 'geo_G_mean'):
        ndim = 2 if key == 'G_mean' else 1
        n = int(np.prod(saved[key].shape[-ndim:]))
        shape = saved[key].shape[:-ndim] + (n,)
        np.testing.assert_allclose(candidate[key].reshape(shape)[..., 0],
                                   saved[key].reshape(shape)[..., 0], rtol=0, atol=1e-15)
        c = info['source_folded'][key]
        print(f'sat {handedness:+d}/RIS {ris_hand:+d} {key}: max source residual {c["max_residual"]:.9g} '
              f'at {c["max_link_index"]}, threshold {c["tolerance"]:.9g}; '
              f'candidate change {c["max_relative_candidate_change"]:.9g}')
    for k in saved:
        assert np.array_equal(saved[k], baseline[k]), k
    assert np.min(np.linalg.eigvalsh(candidate['gt_second'])) > 0
    # The threshold must reject the actually observed near-axis mismatch.
    tight = dict(threshold, r_mean=1e-6)
    rejects(lambda: construct(saved, x, source, U, K, [2], 100,
                              source_tolerances=tight))
    bad_geo = K.copy(); bad_geo[0, 0] += 1
    rejects(lambda: construct(saved, x, source, U, bad_geo, [2], 100,
                              source_tolerances=threshold))
    bad_src = dict(source); bad_src['H_NN_LOS'] = source['H_NN_LOS'].copy()
    bad_src['H_NN_LOS'][0, 0, 2] *= 1j
    rejects(lambda: construct(saved, x, bad_src, U, K, [2], 100,
                              source_tolerances=threshold))
    bad_var = dict(saved); bad_var['G_var'] = saved['G_var'].copy()
    bad_var['G_var'][0, 0] = -1
    rejects(lambda: construct(bad_var, x, source, U, K, [2], 100,
                              source_tolerances=threshold))
    bad_shape = dict(saved); bad_shape['geo_G_var'] = saved['geo_G_var'][:-1]
    rejects(lambda: construct(bad_shape, x, source, U, K, [2], 100,
                              source_tolerances=threshold))
    bad_los = dict(x); bad_los['a_N_K'] = x['a_N_K'].copy()
    bad_los['a_N_K'][0, 0, 1] *= 1j
    rejects(lambda: construct(saved, bad_los, source, U, K, [2], 100,
                              source_tolerances=threshold))
print('PASS: conditional moments only; no raw stream read and no optimizer run')
