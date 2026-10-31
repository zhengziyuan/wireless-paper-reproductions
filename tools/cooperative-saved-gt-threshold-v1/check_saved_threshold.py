"""Inspect stored GEO interference against saved limits; not a physics rerun.

Read canonical NPZ and both small gzip JSON result files. No state vector,
channel, optimization, sampling or external file is written. Strict comparisons
apply to stored binary64 scalars only; no bound on evaluation roundoff is known.
"""
from pathlib import Path
import argparse
import gzip
import json
import numpy as np

EXPECTED_SCHEMES = frozenset(('AP-NoRIS', 'AP-AO', 'MR-S-NoRIS', 'MR-S-PA',
                              'MR-S-TS', 'MR-TTS-NoRIS', 'MR-TTS-PA', 'MR-TTS-TS'))


def load_result(path):
    with gzip.open(path, 'rt', encoding='utf-8') as f:
        return json.load(f)


def analyze_result(data, limit, power):
    """Check one supplied saved-result object, without writing or recomputing W."""
    limit = np.asarray(limit, dtype=float)
    power = np.asarray(power, dtype=float)
    if limit.shape != (1,) or power.shape != (3,) or not np.isfinite(limit).all() or not np.isfinite(power).all() or np.any(limit <= 0) or np.any(power <= 0):
        raise ValueError('expected finite positive J3/K1 saved limits')
    if len(data['results']) != 1:
        raise ValueError('exactly one stored scenario expected')
    case = data['results'][0]
    tol = float(data['configuration']['tuned_not_reported']['solver_objective_tolerance'])
    schemes = case['schemes']
    names = [s['scheme'] for s in schemes]
    if len(names) != len(EXPECTED_SCHEMES) or len(set(names)) != len(names) or set(names) != EXPECTED_SCHEMES or not np.isfinite(tol) or tol <= 0:
        raise ValueError('eight unique expected schemes and finite positive tolerance required')
    items = []
    all_differences = []
    for s in schemes:
        e = s['evaluation']
        gt = np.asarray(e['gt_interference'], dtype=float).reshape(-1)
        pl = np.asarray(e['satellite_power'], dtype=float).reshape(-1)
        if (gt.shape != limit.shape or pl.shape != power.shape or
                not np.isfinite(gt).all() or not np.isfinite(pl).all() or
                np.any(gt < 0) or np.any(pl < 0)):
            raise ValueError('stored interference/power must be finite nonnegative and correctly shaped')
        delta = gt - limit
        all_differences.extend((pl - power).tolist())
        all_differences.extend(delta.tolist())
        items.append({'scheme': s['scheme'], 'stored_gt': gt.tolist(),
                      'gt_minus_limit': delta.tolist(),
                      'relative_gt_minus_limit': (delta/limit).tolist(),
                      'strict_stored_gt_leq_limit': bool(np.all(delta <= 0))})
    reconstructed_flag = max(all_differences) < tol
    if reconstructed_flag != case['constraint_pass']:
        raise ValueError('source-style aggregate tolerance flag mismatch')
    return {'stored_constraint_pass': case['constraint_pass'],
            'source_style_tolerance_flag_recomputed': reconstructed_flag,
            'source_absolute_solver_objective_tolerance': tol,
            'maximum_stored_constraint_excess': max(0., max(all_differences)),
            'scheme_checks': items}


def review(capsule):
    capsule = Path(capsule)
    with np.load(capsule / 'inputs' / 'canonical-eleven-arrays-and-limits.npz', allow_pickle=False) as f:
        limit = np.asarray(f['interference_limit'], dtype=float)
        power = np.asarray(f['power_limit'], dtype=float)
    lanes = {}
    for lane in ('python', 'native'):
        data = load_result(capsule / 'evidence' / (lane + '-full-result.json.gz'))
        lanes[lane] = analyze_result(data, limit, power)
    return {'scope':'one saved J3/U6/K1 point; stored evaluation scalars only',
            'saved_gt_limit':limit.tolist(), 'saved_power_limit':power.tolist(),
            'lanes':lanes, 'recomputed_from_beamformers':False,
            'strict_physical_infeasibility_established':False,
            'channel_model_roundoff_bound_established':False,
            'original_reference_or_full_paper_pass':False}


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('capsule', type=Path)
    print(json.dumps(review(p.parse_args().capsule), indent=2, allow_nan=False))
