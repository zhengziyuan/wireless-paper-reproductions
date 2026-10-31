"""In-memory U6/K1 GEO-interference second-moment candidate.

The caller must supply the saved inputs and the candidate LOS factors; this
module loads or writes neither.  A fixed signed-axis handedness is a modelling
choice, not a recovered measurement of the physical array orientation.
"""
import numpy as np


def candidate_gt_second(d_mean, gt_second, oriented_ng_los, users, geo_users,
                        user_for_geo, beta_n, *, position_tolerance=1e-6,
                        relative_tolerance=1e-9):
    """Return (candidate, diagnostics), after strictly checking the baseline.

    d_mean: (J,U,N), source-normalized direct-link mean; gt_second: (J,K,N,N),
    E[h_NG h_NG^H] including existing gain and noise normalization;
    oriented_ng_los: (J,K,N), fixed-frame candidate LOS with unit magnitudes.
    users and geo_users are ECEF positions in metres, user_for_geo maps each
    GEO user to a co-located NGSO user. The source's positive Rician ratio beta_n
    determines a baseline identity-plus-rank-one check. The update is D Q D^H
    with D = diag(a_new/a_saved), preserving the entire saved scatter term and
    all eigenvalues without recalculating gains, propagation, or random draws.
    Common propagation phase cancels in the second moment.

    No assertion is made about the historical physical handedness, other
    geometries or any full-channel/optimization/reproduction result.
    """
    d = np.asarray(d_mean, dtype=np.complex128)
    q = np.asarray(gt_second, dtype=np.complex128)
    a = np.asarray(oriented_ng_los, dtype=np.complex128)
    u = np.asarray(users, dtype=float)
    kpos = np.asarray(geo_users, dtype=float)
    mapping = np.asarray(user_for_geo)
    beta = float(beta_n)
    ptol, rtol = float(position_tolerance), float(relative_tolerance)
    if (d.ndim != 3 or q.ndim != 4 or a.ndim != 3 or u.ndim != 2 or
            kpos.ndim != 2 or u.shape[1:] != (3,) or kpos.shape[1:] != (3,)):
        raise ValueError('unexpected array or coordinate dimensions')
    jn, un, n = d.shape
    kn = kpos.shape[0]
    if (u.shape[0] != un or q.shape != (jn, kn, n, n) or
            a.shape != (jn, kn, n) or mapping.shape != (kn,) or
            not np.issubdtype(mapping.dtype, np.integer) or
            np.any(mapping < 0) or np.any(mapping >= un)):
        raise ValueError('incompatible array sizes or user mapping')
    if (not all(np.isfinite(x).all() for x in (d, q, a, u, kpos)) or
            not np.isfinite(beta) or beta <= 0 or
            not np.isfinite(ptol) or ptol < 0 or
            not np.isfinite(rtol) or rtol <= 0):
        raise ValueError('nonfinite input or invalid tolerance/Rician ratio')
    distances = np.linalg.norm(u[mapping] - kpos, axis=1)
    if np.any(distances > ptol):
        raise ValueError('mapped GEO and NGSO users are not co-located')
    old = d[:, mapping, :]
    if np.any(np.abs(old[..., :1]) == 0):
        raise ValueError('zero saved direct LOS reference')
    old = old / old[..., :1]
    if np.max(np.abs(np.abs(old) - 1)) > rtol:
        raise ValueError('saved direct LOS has nonuniform magnitude')
    if np.any(np.abs(a[..., :1]) == 0):
        raise ValueError('zero candidate LOS reference')
    new = a / a[..., :1]
    if np.max(np.abs(np.abs(new) - 1)) > rtol:
        raise ValueError('candidate LOS has nonuniform magnitude')
    # Project only roundoff-level amplitude errors, never a physical scaling.
    phases = (new / old)
    phases = phases / np.abs(phases)
    eye = np.eye(n)
    out = np.empty_like(q)
    checks = []
    for j in range(jn):
        for k in range(kn):
            Q = q[j, k]
            scale = float(np.max(np.abs(Q)))
            if scale <= 0:
                raise ValueError('zero second moment cannot identify Rician components')
            herm_before = float(np.max(np.abs(Q - Q.conj().T)) / scale)
            mu = float(np.trace(Q).real / n)
            expected = mu / (1 + beta) * (eye + beta * np.outer(old[j, k], old[j, k].conj()))
            model_error = float(np.max(np.abs(Q - expected)) / scale)
            if mu <= 0 or herm_before > rtol or model_error > rtol:
                raise ValueError('saved matrix fails Hermitian/source Rician reconstruction')
            eig_before = np.linalg.eigvalsh((Q + Q.conj().T) / 2)
            if eig_before[0] < -rtol * scale:
                raise ValueError('saved matrix is not positive semidefinite')
            D = phases[j, k]
            Qnew = D[:, None] * Q * D[None, :].conj()
            herm_after = float(np.max(np.abs(Qnew - Qnew.conj().T)) / scale)
            eig_after = np.linalg.eigvalsh((Qnew + Qnew.conj().T) / 2)
            if herm_after > rtol or eig_after[0] < -rtol * scale:
                raise ValueError('candidate matrix fails Hermitian/PSD check')
            eig_change = float(np.max(np.abs(eig_before - eig_after)) / scale)
            diagonal_change = float(np.max(np.abs(np.diag(Qnew) - np.diag(Q))) / scale)
            if eig_change > rtol or diagonal_change > rtol:
                raise ValueError('candidate did not preserve saved spectrum or diagonal')
            out[j, k] = Qnew
            checks.append(dict(satellite=j, geo_user=k, mu=mu,
                               source_model_relative_error=model_error,
                               old_hermitian_relative_error=herm_before,
                               new_hermitian_relative_error=herm_after,
                               old_min_eigenvalue=float(eig_before[0]),
                               new_min_eigenvalue=float(eig_after[0]),
                               relative_eigenvalue_change=eig_change,
                               relative_diagonal_change=diagonal_change,
                               relative_matrix_change=float(np.max(np.abs(Qnew-Q))/scale)))
    return out, dict(max_user_separation_m=float(np.max(distances)),
                     mapping=mapping.tolist(), beta_n=beta, arrays=checks)
