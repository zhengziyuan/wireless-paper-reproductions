# Prepared final-IEEE recorded-convergence evidence gate

This independent Python wrapper is **not integrated into a production runner**
and has not been applied to a real scientific run. It preserves the source
algorithm, its signed relative stop, existing records and budgets. It checks
saved evidence only, returning Python `True`, `False`, or `None` rather than changing
an optimizer's stopping behavior. `false` takes precedence over `null` when
blocks and starts are aggregated. A missing/invalid history, missing stop,
missing prescribed start, or unattested complete capture cannot produce a
passing gate. A recorded negative objective step or invalid negative gradient
norm cannot produce a passing gate even when the original stop flag is true.

The wrapper reflects the current Python `statistical_ensemble.execute_start`
record structure. NoRIS saves QT history and its stop; TwoStage saves both
phase and QT histories and stops. AO saves outer history and each phase stop,
but **discards each inner phase history**. Consequently a current AO record
cannot pass this recorded-history gate: its phase histories are `null`/unknown.
Changing the caller's completeness assertion cannot supply missing histories.
A future source-bound, resumable recorder would need to retain each phase
history together with its matching stop without changing algorithm behavior.
For such a future source, the wrapper can accept `phase_histories` as an
explicitly supplied list in AO block order. Matching the association and the
capture assertion still requires independently authenticated source evidence;
synthetic successful aggregation is not paper acceptance.

For the currently saved blocks, the wrapper requires the stop's iteration
count to agree with the recorded history length, checks the final signed
residual or the reported nonnegative gradient threshold, and records all
negative steps. A `true` block is conditional on the caller's explicit
`complete_history_capture=True` assertion; this code cannot authenticate the
historical source or independently prove that assertion. A history count is
not proof that all original steps were recorded. The caller must also supply
`declared_limits` containing the actual relative/gradient tolerances and
QT/AO/RGD caps; missing limits produce `None`, and a mismatch between the
declared limits and a stop receipt produces `False`. These supplied limits are
not authenticated by this wrapper; a future execution must bind them to its
source/configuration receipt. A rounded negative stored
value is a failed **strict recorded nondecrease gate**, not by itself proof of
a negative high-precision Armijo increment or a physical violation. A single
stored point is treated as insufficient even if a recorded gradient is small.
No physical, solver, reference, MATLAB parity, mathematical convergence or
full-paper acceptance is inferred.

`assess_start` and `assess_case` accept decoded JSON-like Python structures.
The latter requires every start ID `0..U` in each of the three named schemes,
preserves original case checks in its output, and independently aggregates
the recorded evidence. It never promotes the original `convergence_pass` to
this new gate. It only has access to the supplied records and cannot establish
checkpoint, scientific input, source or cross-language provenance. Original
case fields are not edited. The added gate is a prerequisite for later
certification, not a replacement for numerical or physical evidence.

From the repository root, run the isolated synthetic tests:

```text
python -I -B -m unittest discover -s tools/hotspot-final-ieee-convergence-gate-v1 -p test_recorded_gate.py
```

The tests use fabricated data; they exercise decreases, missing/truncated
histories, bad gradient norms, original stop failures, duplicate IDs, AO's
unrecorded inner histories and the false-over-unknown aggregation rule. No
MATLAB or paper-scale numerical run is implied.
