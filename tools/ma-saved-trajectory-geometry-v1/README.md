# MA Fig. 5: saved AO sweep geometry

This check examines the stored Python Fig. 5, case 7, geometry 0 at 30 dBm,
with six antennas and five users. It uses only the saved MRT and ZF sweep
positions and their associated original job/configuration metadata. It does
not run the optimizer or draw new samples.

The retained `strict/two-timescale-ma/run.py` scenario uses normalized
wavelength 1 and minimum spacing 0.5. For this job, `A=2`, the saved
configuration factorization is 2 by 3, and there are no region or antenna
position-error overrides. The scenario's placement box is therefore
`[-2,2] x [-3,3]`. The witness compares the **original Euclidean distance**,
not the linearized spacing constraint, and checks all antenna pairs and the
box at every stored sweep boundary. JSON numbers are converted back to the
binary64 values saved by Python, then compared as exact rational numbers.

| Saved trajectory | Stored positions including initial | Pair checks | Box checks | Spacing violations | Box violations |
|---|---:|---:|---:|---:|---:|
| MRT | 40 | 600 | 240 | 0 | 0 |
| ZF | 34 | 510 | 204 | 0 | 0 |

Both initial placements have minimum squared spacing 0.25. At the final
boundaries, the minimum squared spacings are about 0.250000000081 for MRT
and 0.250000061738 for ZF. The smallest distances to a box edge across the
stored positions are approximately 1.44346 and 1.67158, respectively.
The final stored positions also match the saved nominal and realized final
positions for this case.

From this directory, with Python 3, use a fresh output path:

```sh
python -B check_saved_geometry.py saved-input.json /path/to/new-report.json
```

The compact input contains actual saved positions and objectives, not the
1000 fading samples or the complete coordinate-update history. This verifies
only the saved sweep boundaries for this one Python case. It does not verify
the intermediate coordinate updates, rate or power, convergence, MATLAB,
original-reference agreement, other points, or the full figure. Exact
comparison of serialized binary64 positions is not an interval certificate
for the underlying numerical optimization.
