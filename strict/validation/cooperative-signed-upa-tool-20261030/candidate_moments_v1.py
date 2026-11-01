"""Conditional in-memory U6/K1 oriented mean/second-moment candidate.

The caller supplies both independently reconstructed source-folded and signed
LOS factors.  No channel samples, optimizer, input file or output file are
created.  Agreement checks do not certify original figure provenance or the
physical array orientation.
"""
import numpy as np
from gt_second_v1 import candidate_gt_second


def construct(saved, oriented, folded, users, geo_users, user_for_geo, beta_n,
              *, source_tolerances, coincident_los_tolerance=1e-10):
    """Return candidate arrays and source-comparison diagnostics.

    Candidate means preserve each saved link's first complex coefficient (the
    existing gain and common phase) and replace only its relative steering.
    Source-folded arrays are explicitly checked for every saved link.  Caller
    must specify absolute complex residual thresholds for every mean category;
    near-axis reconstruction can differ because the original uses acos.
    The mapped co-located signed direct and GEO-user relative steering vectors
    must agree within coincident_los_tolerance before changing the second moment.
    Remaining input arrays are copied, not mutated.
    """
    names = {'d_mean': 'H_NN_LOS', 'G_mean': 'H_NR_LOS',
             'r_mean': 'H_RU_LOS', 'geo_G_mean': 'H_GR_LOS'}
    keys = set(names) | {'d_var', 'G_var', 'r_var', 'gt_second',
                         'geo_d_mean', 'geo_d_var', 'geo_G_var',
                         'power_limit', 'interference_limit'}
    if set(saved) != keys or set(source_tolerances) != set(names):
        raise ValueError('exact saved-array and tolerance contracts required')
    d_shape = np.shape(saved['d_mean'])
    r_shape = np.shape(saved['r_mean'])
    if len(d_shape) != 3 or len(r_shape) != 2:
        raise ValueError('direct and RIS-user arrays must have J,U,N and U,M shapes')
    j, u, n = d_shape
    if r_shape[0] != u or min(j, u, n, r_shape[1]) < 1:
        raise ValueError('incompatible or empty channel dimensions')
    m = r_shape[1]
    expected = {'G_mean': (j, u, n, m), 'd_var': (j, u),
                'G_var': (j, u), 'r_var': (u,), 'geo_d_mean': (u,),
                'geo_d_var': (u,), 'geo_G_mean': (u, m), 'geo_G_var': (u,),
                'power_limit': (j,)}
    k = np.shape(geo_users)[0] if np.ndim(geo_users) == 2 else 0
    expected.update(gt_second=(j, k, n, n), interference_limit=(k,))
    for key, shape in expected.items():
        if np.shape(saved[key]) != shape:
            raise ValueError(f'{key} does not match common channel dimensions')
    for key in ('d_var', 'G_var', 'r_var', 'geo_d_var', 'geo_G_var',
                'power_limit', 'interference_limit'):
        x = np.asarray(saved[key])
        if not np.isrealobj(x) or not np.isfinite(x).all() or np.any(x < 0):
            raise ValueError(f'{key} must be finite real and nonnegative')
    if not np.isfinite(saved['geo_d_mean']).all():
        raise ValueError('geo_d_mean must be finite')
    result = {k: np.array(saved[k], copy=True) for k in keys}
    diag = {}
    for key, los_key in names.items():
        old = np.asarray(saved[key], dtype=np.complex128)
        new = np.asarray(oriented[los_key], dtype=np.complex128)
        reference = np.asarray(folded[los_key], dtype=np.complex128)
        tol = float(source_tolerances[key])
        if old.shape != new.shape or old.shape != reference.shape:
            raise ValueError(f'{key} shape mismatch')
        if (old.ndim not in (2, 3, 4) or not np.isfinite(tol) or tol <= 0 or
                not all(np.isfinite(x).all() for x in (old, new, reference))):
            raise ValueError(f'{key} invalid input or tolerance')
        # Matrix-valued NGSO-RIS has two antenna axes; all others have one.
        element_ndim = 2 if key == 'G_mean' else 1
        link_shape = old.shape[:-element_ndim]
        element_count = int(np.prod(old.shape[-element_ndim:]))
        ov = old.reshape(*link_shape, element_count)
        nv = new.reshape(*link_shape, element_count)
        fv = reference.reshape(*link_shape, element_count)
        if np.any(np.abs(ov[..., :1]) == 0) or np.any(np.abs(nv[..., :1]) == 0) or np.any(np.abs(fv[..., :1]) == 0):
            raise ValueError(f'{key} zero first coefficient')
        old_relative = ov / ov[..., :1]
        new_relative = nv / nv[..., :1]
        fold_relative = fv / fv[..., :1]
        if np.max(np.abs(np.abs(old_relative)-1)) > 1e-9 or np.max(np.abs(np.abs(new_relative)-1)) > 1e-9 or np.max(np.abs(np.abs(fold_relative)-1)) > 1e-9:
            raise ValueError(f'{key} non-unit relative LOS factor')
        per_link = np.max(np.abs(old_relative-fold_relative), axis=-1)
        if np.any(per_link > tol):
            raise ValueError(f'{key} reconstructed source-folded residual exceeds tolerance')
        out = (ov[..., :1] * new_relative).reshape(old.shape)
        result[key] = out
        diag[key] = {'tolerance': tol, 'max_residual': float(np.max(per_link)),
                     'max_link_index': [int(i) for i in np.unravel_index(np.argmax(per_link), link_shape)],
                     'per_link_residual': per_link.tolist(),
                     'max_relative_candidate_change': float(np.max(np.abs(out-old))/np.max(np.abs(old)))}
    mapping = np.asarray(user_for_geo)
    h_nn = np.asarray(oriented['H_NN_LOS'], dtype=np.complex128)
    a_nk = np.asarray(oriented['a_N_K'], dtype=np.complex128)
    ctol = float(coincident_los_tolerance)
    if (mapping.shape != (k,) or not np.issubdtype(mapping.dtype, np.integer)
            or np.any(mapping < 0) or np.any(mapping >= u)
            or h_nn.shape != (j, u, n) or a_nk.shape != (j, k, n)
            or not np.isfinite(h_nn).all() or not np.isfinite(a_nk).all()
            or np.any(np.abs(h_nn[..., 0]) == 0) or np.any(np.abs(a_nk[..., 0]) == 0)
            or not np.isfinite(ctol) or ctol <= 0):
        raise ValueError('invalid coincident GEO/direct LOS input or tolerance')
    hn = h_nn[:, mapping, :] / h_nn[:, mapping, :1]
    nk = a_nk / a_nk[..., :1]
    co_error = float(np.max(np.abs(hn-nk)))
    if co_error > ctol:
        raise ValueError('co-located GEO and direct LOS orientations disagree')
    result['gt_second'], qdiag = candidate_gt_second(
        saved['d_mean'], saved['gt_second'], oriented['a_N_K'],
        users, geo_users, user_for_geo, beta_n)
    return result, {'source_folded': diag, 'gt_second': qdiag,
                    'coincident_los_relative_max_error': co_error,
                    'coincident_los_tolerance': ctol}
