# Case 13: saved QT diagnostic fields

This is a **read-only analysis of previously extracted fields**, not a new
CVX solve, a reconstruction of the convex subproblem, or an independent
physical-feasibility or convergence certificate. It examines `QT_info` for
eight recorded AO events from two starts of case 13 (U=1, satellite Rician
factor 20 dB), using the adjacent published lossless event stream and saved
final parameters. An earlier independent check matched the saved QT-begin
parameters to the respective final parameters, subject to the same historical
source limitations.

All eight records report solver and diagnostic status `Solved`; the two status
fields agree in each record. Each contains 15 reported QoS lower bounds. All
120 saved binary64 bounds strictly exceed their corresponding saved binary64
targets; the smallest exact difference is approximately `1.00993347e-9`.
These are *reported vector-QT lower bounds*, not independent recomputation of
the 120 physical QoS inequalities. All eight saved QT-bound violations are
zero; the largest saved tightness error is approximately `5.67525e-10`.
The saved after-rate exceeds the saved before-rate in each of the eight
records, but the intermediate solver history is not supplied here.

The previously reported over-power event, ordinal 1327964, must not be
overlooked: its saved diagnostic reports a maximum relative constraint
violation of about `6.31264e-11`. Its saved binary64 *reported total power*
exceeds 100 by exactly `111053/17592186044416`, approximately `6.3126322e-9`.
That value is computed from the saved total-power scalar. The earlier exact
audit computed approximately `6.3126281e-9` from the separately saved beam
entries; the two values are close but not bit-identical, and their differing
floating-point calculation paths should not be conflated. Solver status or a
small reported violation does not turn strict feasibility into a pass.

The remaining seven recorded relative constraint violations are zero. These
diagnostics are reports from a common historical run; original producer
identity and a whole-event atomic snapshot have not been authenticated. The
records do not establish the original author implementation, complete
internal QT/solver iterations, MATLAB/Python agreement, paper-figure
agreement, or completion of the reproduction. The exact QT-subproblem model
and all solver residuals were not independently reconstructed here.

From the repository root with Python's standard library:

```text
python -I -S -B tools/hotspot-case13-qt-saved-diagnostics-v1/verify_saved_qt.py
python -I -S -B tools/hotspot-case13-qt-saved-diagnostics-v1/test_synthetic.py
```

The first prints the diagnostic report without writing any file. Compare its
JSON output to `recorded-qtdiagnostics.json` for this saved data. The second
uses synthetic records to exercise malformed inputs, solver-status mismatch,
nonpositive bound gaps and an over-power value; it does not run the optimizer.
