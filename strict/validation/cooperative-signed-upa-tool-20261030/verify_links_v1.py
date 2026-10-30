"""One finite author-geometry check and algebraic conjugation checks only."""
from pathlib import Path
import numpy as np
from links_v1 import generate


def ecef(lat, lon, radius):
    lat, lon = np.deg2rad([lat, lon])
    return radius * np.array([np.cos(lat)*np.cos(lon), np.cos(lat)*np.sin(lon), np.sin(lat)])


S = np.array([ecef(lat, 100, 6928e3) for lat in (-2.5, 0, 2.5)])
user_coords = [(-2, 102), (-2, 100), (0, 100), (0, 102), (2, 102), (2, 100)]
U = np.array([ecef(lat, lon, 6378e3) for lat, lon in user_coords])
R = np.array([ecef(lat, lon + .001, 6378e3) for lat, lon in user_coords])
K = np.array([ecef(0, 100, 6378e3)])
G = ecef(0, 100, 42378e3)
Bs = -S / np.linalg.norm(S, axis=1)[:, None]
As = []
for s, b in zip(S, Bs):
    axis_x = (s[2] * b[2] + s[1] * b[1]) / b[0] + s[0]
    a = s - np.array([axis_x, 0, 0]); As.append(a / np.linalg.norm(a))
As = np.array(As)
Br = U - R; Br /= np.linalg.norm(Br, axis=1)[:, None]
# The cited source's exact b_z == 0 branch for these same-latitude points.
assert np.all(Br[:, 2] == 0)
Ar = np.tile([0., 0., 1.], (len(U), 1))
kwargs = dict(wavelength=.025, sat_spacing=.25, ris_spacing=1.,
              sat_shape=(4, 4), ris_shape=(5, 5))
x = generate(S, U, R, K, G, Bs, As, Br, Ar, **kwargs)
assert x['a_N_R'].shape == (3, 6, 16) and x['a_M_S'].shape == (3, 6, 25)
assert x['a_N_U'].shape == (3, 6, 16) and x['a_M_U'].shape == (6, 25)
assert x['a_N_K'].shape == (3, 1, 16) and x['a_M_G'].shape == (6, 25)
assert x['H_NR_LOS'].shape == (3, 6, 16, 25) and x['H_GR_LOS'].shape == (6, 25)
assert all(np.isfinite(v).all() for v in x.values())
for key in ('a_N_R', 'a_M_S', 'a_N_U', 'a_M_U', 'a_N_K', 'a_M_G'):
    np.testing.assert_allclose(np.abs(x[key]), 1, atol=1e-14)
np.testing.assert_allclose(x['H_NR_LOS'], x['a_N_R'][..., :, None] * x['a_M_S'][..., None, :].conj())
np.testing.assert_allclose(x['H_GR_LOS'], x['a_M_G'].conj())
np.testing.assert_allclose(x['a_M_U'] / x['a_M_U'][:, :1], np.ones((6, 25)), atol=1e-11)
# GEO-user K1 and NGSO user 3 are co-located in these source coordinates.
np.testing.assert_allclose(x['a_N_K'][:, 0], x['a_N_U'][:, 2], atol=1e-12)

# A nontrivial independent synthetic RIS phase tests the full outer product,
# including the exact source phase sign, ordering and conjugation.
y = generate([[1, 1, 2]], [[.5, 0, 0]], [[0, 0, 0]], [[0, 1, 0]], [0, 3, 4],
             [[0, 0, -1]], [[1, 0, 0]], [[0, 0, 1]], [[1, 0, 0]],
             wavelength=2, sat_spacing=.5, ris_spacing=.5,
             sat_shape=(2, 2), ris_shape=(2, 2))
np.testing.assert_allclose(y['a_M_U'][0] / y['a_M_U'][0, 0],
                           [1, 1, np.exp(-.5j*np.pi), np.exp(-.5j*np.pi)])
grid_r, grid_c = np.indices((2, 2))
sat_space = np.exp(-.5j*np.pi*(-grid_r + grid_c)/np.sqrt(6)).reshape(-1)
ris_space = np.exp(-.5j*np.pi*(grid_r + grid_c)/np.sqrt(6)).reshape(-1)
expected_nr = np.exp(1j*np.pi*np.sqrt(6)) * np.outer(sat_space, ris_space.conj())
np.testing.assert_allclose(y['H_NR_LOS'][0, 0], expected_nr, atol=1e-14)
geo_space = np.exp(-.5j*np.pi*(.6*grid_c)).reshape(-1)
np.testing.assert_allclose(y['H_GR_LOS'][0], (np.exp(5j*np.pi)*geo_space).conj(), atol=1e-14)

canonical = (Path(__file__).resolve().parent.parent /
             'cooperative-author-U6-final-ground10-dual-full8-20261019-v1' /
             'inputs' / 'canonical-eleven-arrays-and-limits.npz')
with np.load(canonical, allow_pickle=False) as data:
    saved = {name: data[name] for name in ('d_mean', 'G_mean', 'r_mean', 'geo_G_mean')}
def norm(v):
    return v / v.reshape(-1)[0]
def folded(b, a, direction, rows, cols, spacing_ratio):
    direction = direction / np.linalg.norm(direction)
    p, q = a @ direction, np.cross(b, a) @ direction
    return np.exp(-2j*np.pi*spacing_ratio*(np.arange(rows)[:, None]*p +
                                          np.arange(cols)[None, :]*abs(q))).reshape(-1)
fold_nr = folded(Bs[1], As[1], R[1]-S[1], 4, 4, 10)
fold_ms = folded(Br[1], Ar[1], S[1]-R[1], 5, 5, 40)
fold_mg = folded(Br[1], Ar[1], G-R[1], 5, 5, 40)
folded_reference = {
    'direct': folded(Bs[1], As[1], U[1]-S[1], 4, 4, 10),
    'LEO-RIS': np.outer(fold_nr, fold_ms.conj()),
    'RIS-user': np.ones(25),
    'GEO-RIS': fold_mg.conj(),
}
for name, key, ij in [('direct', 'd_mean', (1, 1)), ('LEO-RIS', 'G_mean', (1, 1)),
                      ('RIS-user', 'r_mean', (1,)), ('GEO-RIS', 'geo_G_mean', (1,))]:
    observed = norm(saved[key][ij])
    predicted = norm(x[{'direct':'H_NN_LOS', 'LEO-RIS':'H_NR_LOS',
                        'RIS-user':'H_RU_LOS', 'GEO-RIS':'H_GR_LOS'}[name]][ij])
    source_error = np.max(np.abs(observed-folded_reference[name]))
    assert source_error < 1e-10
    print(f'{name}: saved/oriented max difference {np.max(np.abs(observed-predicted)):.12g}; '
          f'saved/source-fold max difference {source_error:.12g}')
print('PASS: six spatial factors, finite real geometry and synthetic conjugation; no optimization')
