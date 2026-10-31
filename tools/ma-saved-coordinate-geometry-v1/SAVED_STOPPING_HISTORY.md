# MA Fig. 5: stopping checks for one saved Python trajectory

This checks the original saved objectives and per-coordinate objective
records for Fig. 5 case 7, realization 0. It reuses the saved geometry and
coordinate records; it does not rerun an optimizer or generate samples. The
small `saved-stop-config.json` contains the stopping threshold and iteration
cap transcribed from the retained run configuration. The earlier source-bound
donor receipt binds the retained configuration and result; it does not establish
the historical loaded-code identity.

All comparisons interpret saved Python binary64 values exactly as rational
numbers. MRT has 234 coordinate updates: 232 increases, 2 equalities, and no
decreases. ZF has 198 updates, all increases. The records chain exactly and
agree with all saved sweep endpoints. For the saved threshold `5e-5`, the
first sweep meeting the fractional-increase test is the final recorded sweep
in both histories: sweep 39 for MRT and sweep 33 for ZF. Their final ratios
are approximately `2.76202288e-5` and `4.90975476e-5`, respectively. Both
histories are below the original 10,000-sweep cap.

From the repository root, with Python 3 and a fresh report path:

```sh
python -B tools/ma-saved-coordinate-geometry-v1/check_saved_stopping.py \
  tools/ma-saved-trajectory-geometry-v1/saved-input.json \
  tools/ma-saved-coordinate-geometry-v1/saved-records.json \
  tools/ma-saved-coordinate-geometry-v1/saved-stop-config.json \
  /path/to/new-stopping-report.json
```

This is a check of the retained objective history and configured stopping
rule, not a proof of mathematical convergence, stationarity, global
optimality, forward error, physical feasibility, MATLAB equivalence, original
paper-reference agreement, or the complete figure. Exact rational comparison
of a ratio is not identical to floating-point comparison at a threshold
boundary. An independent check of the original floating-point expression
also found the same first trigger in these two histories.
