# MA Fig. 5: saved per-sample total-power evidence

This check concerns the saved Python Figure 5, case 7, realization 0: `N=6`,
`M=5`, total power `P_tot=1 W` (30 dBm), and 1,000 fading samples. The
published paper's Eq. (6b) bounds the total transmit power, the sum of squared
beamformer-column norms, by `P_tot`. The retained Python `core.instantaneous`
records `sum(abs(W)**2)` for each MA-MRT and MA-ZF sample. This witness checks
those already-saved scalar powers; it does not reconstruct the saved W, draw
channels, or run an optimizer. It is the same retained case as the [saved
sweep-geometry check](../ma-saved-trajectory-geometry-v1/README.md); historical
loaded-code identity is not independently established by these comparisons.

| Scheme | Saved powers | Above 1 W exactly in saved binary64 | Above 1 W + 1e-6 |
|---|---:|---:|---:|
| MA-MRT | 1,000 | 251 | 0 |
| MA-ZF | 1,000 | 90 | 0 |
| FPA-MRT / FPA-ZF / FPA-OPT | not saved | unknown | unknown |

The highest recorded power in each MA mode is approximately
`1.0000000000000004 W`. Thus the two sets meet the configured numerical
tolerance; strict inequalities on the serialized values do not all hold.
The missing FPA powers cannot be inferred from sample rates or the saved
`nonconverged_samples=0` summaries. The old per-sample FPA convergence
histories were not saved either.

The compact input carries the 5,000 saved rate samples and 2,000 saved MA
power scalars, extracted from the already-retained job, result and run config.
All rates are finite and nonnegative, and the five saved means agree with a
recalculation from those values to relative tolerance `1e-12` (maximum absolute
gap about `3.6e-15`). These tests compare existing scalars and do not constitute
an independent physical SINR, power, or convergence calculation.

From the repository root, with Python 3 and a fresh report path:

```sh
python -B tools/ma-saved-power-evidence-v1/check_saved_power.py \
  tools/ma-saved-power-evidence-v1/saved-input.json /path/to/new-report.json
```

This evidence does not establish FPA power feasibility, MATLAB/Python
agreement, original-curve agreement, a complete figure, or paper reproduction.
The saved native binary64 values and nominal tolerance are not an interval
certificate for physical implementation or mathematical optimization.
