"""Oriented spatial LOS factors with the supplied INIT's algebraic layout.

This module makes only an in-memory candidate. It never loads or writes the
original inputs, random realizations, channel powers, or optimizer results.
"""
import numpy as np
from signed_upa import response


def _points(value, name):
    x = np.asarray(value, dtype=float)
    if x.ndim != 2 or x.shape[1] != 3 or not len(x) or not np.isfinite(x).all():
        raise ValueError(f"{name} must be an array of finite 3-vectors")
    return x


def _propagation(distance, wavelength):
    # The INIT constructs exp(-i*k*distance) in a row then conjugate-transposes.
    return np.exp(2j * np.pi * distance / wavelength)


def generate(satellites, users, reflectors, geo_users, geo_satellite,
             sat_boresights, sat_axes, ris_boresights, ris_axes, *,
             wavelength, sat_spacing, ris_spacing, sat_shape, ris_shape,
             sat_handedness=1, ris_handedness=1):
    """Make six per-endpoint spatial factors and five source-shaped LOS arrays.

    All coordinates have consistent length units; one handedness is chosen per
    array family (never per ray).  Directions point out from the relevant
    array: reflector to satellite for a_M_S and reflector to GEO for a_M_G.
    Source's column steering is spatial sign -1; its H_NR and H_GR then use
    conjugate transpose. `wavelength` and physical spacings use the same unit.
    Returned LOS arrays do not include large-scale factors or fading.
    """
    S = _points(satellites, "satellites")
    U = _points(users, "users")
    R = _points(reflectors, "reflectors")
    K = _points(geo_users, "geo_users")
    Bs, As = _points(sat_boresights, "sat_boresights"), _points(sat_axes, "sat_axes")
    Br, Ar = _points(ris_boresights, "ris_boresights"), _points(ris_axes, "ris_axes")
    G = np.asarray(geo_satellite, dtype=float)
    if G.shape != (3,) or not np.isfinite(G).all():
        raise ValueError("geo_satellite must be one finite 3-vector")
    if len(R) != len(U) or len(Bs) != len(S) or len(As) != len(S) or len(Br) != len(R) or len(Ar) != len(R):
        raise ValueError("one array frame per satellite and one per user/reflector are required")
    wavelength = float(wavelength)
    if not np.isfinite(wavelength) or wavelength <= 0:
        raise ValueError("wavelength must be finite and positive")
    try:
        sr, sc = sat_shape
        rr, rc = ris_shape
    except (ValueError, TypeError) as exc:
        raise ValueError("each array shape must have two dimensions") from exc
    # response validates dimensions, orthogonal frames, spacings and direction.
    ns, nr = sr * sc, rr * rc
    a_NR = np.empty((len(S), len(U), ns), complex)
    a_MS = np.empty((len(S), len(U), nr), complex)
    a_NU = np.empty_like(a_NR)
    a_MU = np.empty((len(U), nr), complex)
    a_NK = np.empty((len(S), len(K), ns), complex)
    a_MG = np.empty_like(a_MU)
    def sat(j, vector):
        return response(Bs[j], As[j], vector, sr, sc, sat_spacing / wavelength, handedness=sat_handedness)
    def ris(u, vector):
        return response(Br[u], Ar[u], vector, rr, rc, ris_spacing / wavelength, handedness=ris_handedness)
    for j, s in enumerate(S):
        for u, (r, user) in enumerate(zip(R, U)):
            a_NR[j, u] = _propagation(np.linalg.norm(r - s), wavelength) * sat(j, r - s)
            a_MS[j, u] = ris(u, s - r)
            a_NU[j, u] = _propagation(np.linalg.norm(user - s), wavelength) * sat(j, user - s)
        for k, user in enumerate(K):
            a_NK[j, k] = _propagation(np.linalg.norm(user - s), wavelength) * sat(j, user - s)
    for u, (r, user) in enumerate(zip(R, U)):
        a_MU[u] = _propagation(np.linalg.norm(user - r), wavelength) * ris(u, user - r)
        a_MG[u] = _propagation(np.linalg.norm(G - r), wavelength) * ris(u, G - r)
    return dict(a_N_R=a_NR, a_M_S=a_MS, a_N_U=a_NU, a_M_U=a_MU,
                a_N_K=a_NK, a_M_G=a_MG,
                H_NN_LOS=a_NU, H_NG_LOS=a_NK,
                H_NR_LOS=a_NR[..., :, None] * a_MS[..., None, :].conj(),
                H_GR_LOS=a_MG.conj(), H_RU_LOS=a_MU)
