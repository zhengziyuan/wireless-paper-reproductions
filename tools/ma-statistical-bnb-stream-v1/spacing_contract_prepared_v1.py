"""Compare the existing binary64 and exact spacing decisions for fixed grids.

Prepared callable only: no real job is opened on import. A guarded caller is
responsible for binding original bounds/config and retaining any mismatches.
This does not test candidate objectives, certify trig inputs or prove a paper.
"""
from fractions import Fraction
import math
import numpy as np


def compare_pairs(grid, minimum_distance, *, witness_limit=16, return_all_indices=False):
    a = np.asarray(grid, dtype=np.float64)
    d = float(minimum_distance)
    if (a.ndim != 2 or a.shape[1] != 2 or len(a) < 2 or len(a) > 1024
            or not np.all(np.isfinite(a)) or not math.isfinite(d) or d <= 0
            or type(witness_limit) is not int or not 0 <= witness_limit <= 100
            or type(return_all_indices) is not bool):
        raise ValueError("invalid grid or spacing")
    if return_all_indices and len(a) * (len(a) - 1) // 2 > 30024:
        raise ValueError("all-mismatch output exceeds prepared bound")
    points = [(Fraction(float(x)), Fraction(float(y))) for x, y in a]
    exact_d2 = Fraction(d) ** 2
    total = mismatch = float_only = exact_only = 0
    examples, all_indices = [], []
    for j in range(1, len(a)):
        # Mirrors exhaustive(): axis-1 norm on an array of point differences.
        norm = np.linalg.norm(a[:j] - a[j], axis=1)
        for i in range(j):
            float_ok = not bool(norm[i] < d)
            dx, dy = points[i][0] - points[j][0], points[i][1] - points[j][1]
            exact_ok = dx * dx + dy * dy >= exact_d2
            total += 1
            if float_ok != exact_ok:
                mismatch += 1
                float_only += int(float_ok)
                exact_only += int(exact_ok)
                if return_all_indices:
                    all_indices.append([i, j, int(float_ok), int(exact_ok)])
                if len(examples) < witness_limit:
                    examples.append({"i": i, "j": j,
                                     "p": [float(x).hex() for x in a[i]],
                                     "q": [float(x).hex() for x in a[j]],
                                     "float_norm_hex": float(norm[i]).hex(),
                                     "float_accepts": float_ok,
                                     "exact_accepts": exact_ok})
    return {"pairs_checked": total, "mismatch_count": mismatch,
            "float_only": float_only, "exact_only": exact_only,
            "examples": examples,
            "all_mismatch_indices": all_indices if return_all_indices else None}


def compare_grid(lower, upper, D, minimum_distance, *, return_all_indices=False):
    if (type(D) is not int or not 2 <= D <= 32 or
            len(lower) != 2 or len(upper) != 2 or
            not all(math.isfinite(float(v)) for v in [*lower, *upper]) or
            not all(float(a) < float(b) for a, b in zip(lower, upper))):
        raise ValueError("invalid grid configuration")
    grid = np.array([[x, y] for x in np.linspace(lower[0], upper[0], D)
                     for y in np.linspace(lower[1], upper[1], D)])
    result = compare_pairs(grid, minimum_distance, return_all_indices=return_all_indices)
    result.update({"D": D, "point_count": len(grid),
                   "float_semantics": "numpy_norm_lt_strictly_excludes",
                   "exact_semantics": "rational_squared_distance_ge"})
    return result
