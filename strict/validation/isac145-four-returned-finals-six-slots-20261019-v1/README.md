# ISAC145: four returned final states, six retained outcome slots

The original stable-arithmetic cold six-scheme run finished with real process
exit0, exact original held-child identity and a closed14-pin source/input
interval. Its runner catches scheme exceptions. Actual scientific outcomes
are **2 failed without final state,2 returned but not fully converged,2 fully
converged**. Process exit0 is retained; it is not a six-scheme PASS.

| Scheme | Original outcome |
|---|---|
| Rot-BS & Rot-RIS | RCG Armijo failure; no final W/theta/rotation |
| Rot-BS & Fix-RIS | RCG Armijo failure; no final W/theta/rotation |
| Fix-BS & Rot-RIS | Feasible returned state; AO500cap, every RIS block500cap |
| Fix-BS & Fix-RIS | Feasible returned state; AO500cap, every RIS block500cap |
| Rot-BS & No-RIS | Original full-converged flags true; AO390 |
| Fix-BS & No-RIS | Original full-converged flags true; AO5 |

Original controls are W maximum10000, RCG maximum500/gradient1e-6/80Armijo
trials, PGA maximum500, and AO maximum500. Original settings, residuals and
failures are retained. Fixed RIS fixes orientation; its phase remains optimized.

The four actual returned finals passed independent MP80/MP100 physical fields
and feasibility, all W/RIS/rotation derivative comparisons at the last saved
fixed iota, fixed-iota objectives and precision. This was one saved-state audit
with no optimization, RNG, scenario generation or MC. The maximum
cross-precision derivative/objective difference was approximately1.98531e-58.

Only Fix-BS & Fix-RIS had0last rotation updates, so its final state is also its
actual last RIS endpoint. Independent normalized gradient4.752704663e-4 is
above the unchanged1e-6 stop, confirming the retained failure. Fix-BS & Rot-RIS
made55last rotation updates: final gradient0.6395694 and earlier recorded RIS
gradient0.00301635 describe different states and are not equated here.

The two failed Rot-BS slots have no failed-state or80-trial operands. The prior
case145 fixed-state trace and case159 W-QCQP repair do not validate these new
failures. A separately labelled passive capture under this actual stable
provider and each original scheme's bounds is the next missing diagnostic.
No such new capture was executed by packaging.

## Contents and saved-state replay

four-final-state-fixture.json contains the four actual W/theta/rotation states,
all six original outcome slots and saved last-block scalars. The complete MP
report is evidence/four-final-MP80-MP100.json.gz. Exact provider, original core
and mathematical dependencies are included. Historical absolute JSON paths
become nonresolving repository/ or artifacts/ source-reference labels;
original digests remain. The portable plan uses package-relative input names
and current digests. Source-code files are exact byte copies.

From this directory, with Python, NumPy and mpmath installed:

    python -B audit_actual_145_four_returned_finals_keep_six_slots_MP80_MP100_v1.py --plan saved-four-MP-replay-plan.json --output-dir NEW_EMPTY_OUTPUT_DIRECTORY --execute

This performs real saved-state MP calculations. The first use from this public
projection has now actually completed once with natural exit0 (root tool
session85786), using these unchanged reader/provider/math-source bytes,
fixture and numerical values. All four returned-final physical, derivative,
fixed-iota, precision and applicable historical-boundary flags passed, with
source/input closure. Its full report and first-use closure are included under
evidence/public-first-use-*. This update reads that already completed audit;
it does not repeat MP or perform a new optimization. Prepared-only fields in
the unchanged replay plan/provenance describe their earlier preparation epoch.
The original two missing failed finals, two capped returns and two full returns
remain separate: this is a four-state scoped audit, not full-six acceptance.

The127306222-byte original result is excluded; SHA256:
e4904048aa934fe4521312072ae443b284b31e067f3ed0404e92eea60280828b.
The complete saved AO trajectory is absent, and two failed final states do
not exist in that return. Four finals cannot replay or validate all historical
AO/QT/QCQP decisions or missing searches. Full-six, dual-language, author
reference and full-paper acceptance remain false.
