# MA Fig. 5: conditional coordinate-boundary geometry

This witness examines the same saved Python Fig. 5 case 7, realization 0,
used by the [saved sweep geometry check](../ma-saved-trajectory-geometry-v1/README.md).
It reuses that check's saved sweep positions and the [saved geometry/model
parameters](../ma-eq29-saved-witness-v1/saved-input.json); only the recorded
per-coordinate objective transitions are added here. No optimization or
random samples are generated.

The saved history has 39 MRT and 33 ZF sweeps, with six records per sweep in
the order antenna 0 through 5. Each record has before/after objectives but
does **not** save the intermediate coordinate itself. The retained original
`optimize`/`solve_coordinate` implementation updates just the selected antenna
at each step. **Conditional on that implementation behavior having been used**,
the intermediate positions are uniquely inferred from consecutive saved
sweep-boundary positions and the record order. This is a reconstruction, not
an independently saved set of intermediate coordinates; the historical
execution's exact loaded code identity is not independently established here.

For every inferred point, the script checks the original Euclidean separation
and the placement box using exact rational representations of the saved
binary64 positions. It separately recomputes the theoretical MRT or ZF
objective at every before/after point and checks against the saved records
within `1e-10 * max(1, abs(saved objective))`. Adjacent saved objectives and
the sweep endpoints must also match exactly as stored. Observed maximum
absolute objective differences are approximately `7.11e-15` for MRT and zero
for ZF, on the tested Python/NumPy runtime.

| Mode | Inferred updates | Pair checks | Box checks | Spacing failures | Box failures |
|---|---:|---:|---:|---:|---:|
| MRT | 234 | 3,510 | 1,404 | 0 | 0 |
| ZF | 198 | 2,970 | 1,188 | 0 | 0 |

From the repository root, with Python 3 and NumPy, choose a new report path:

```sh
python -B tools/ma-saved-coordinate-geometry-v1/check_coordinates.py \
  tools/ma-saved-trajectory-geometry-v1/saved-input.json \
  tools/ma-eq29-saved-witness-v1/saved-input.json \
  tools/ma-saved-coordinate-geometry-v1/saved-records.json \
  /path/to/new-report.json
```

The numeric input follows the retained `scenario` convention: wavelength 1,
noise `1e-11` per user, minimum separation 0.5, and box `[-2,2] x [-3,3]`.
The saved 432 transition records are verbatim extractions of their indices and
before/after values. The earlier source-bound donor receipt identified the
retained result by SHA-256
`9702fff22545b4526e5a87f754c12380c4b2ff1fdd4bf105810f5ac3300c7fc0`;
its recorded implementation fingerprint is
`b3b8134f4c9be5213dee91930e240792be509003a1b840848131e1f2621ee5ef`.
This fingerprint was not independently recreated from the historical runtime
for this check.

Objective agreement does not uniquely determine coordinates and does not by
itself authenticate the historical loaded implementation. The exact checks
apply to inferred binary64 positions, not forward-error intervals. They do
not verify the optimization, power, complete convergence, MATLAB, original
reference, other cases, full figure, or paper.
