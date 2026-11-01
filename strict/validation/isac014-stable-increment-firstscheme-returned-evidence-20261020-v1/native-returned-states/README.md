# Native ISAC014 first scheme: returned-state evidence and remaining joint residuals

This is the closed MATLAB counterpart of the [Python first-scheme evidence](../README.md). It contains one actual cold `Rot-BS & Rot-RIS` trajectory, its 36 actual returned inner-block states and final own state, and the already-completed independent saved-state MP80/MP100 audit. It makes no full-six, original-reference, final-joint stationarity, or full-paper PASS claim.

## What actually completed

The original native producer returned naturally with code 0 and closed its source interval. The saved-state reader also returned naturally with code 0, original-handle/birth/exit agreement, 38 watched source/job pins unchanged, and no host errors. These lifecycle facts are separate from its scientific checks.

The first reader attempt is preserved: it returned naturally with code 1 at `ModuleNotFoundError: No module named mpmath`, before any MP formula, objective, gradient, trajectory, or scientific output. The later attempt only restored the complete existing `PYTHONPATH`; it installed nothing and changed no pinned mathematics. Both attempts' actual terminal receipts are included.

The final native trajectory had 12 AO blocks and 36 saved returns (12 W, 12 RCG, 12 PGA). Every applicable own-block RCG/PGA gradient stop passed the disclosed 1e-6 reconstruction check. All 37 scoped states (36 endpoints plus final) passed the retained physical-field/feasibility checks and independent-reference precision checks. MP80 versus MP100 differed by at most 1.4857338752051932e-59. The complete reports retain all digits and actual control values.

## Precise derivative-validation boundary

The native producer did **not** save its per-coordinate analytical gradient vectors. The audit evaluates the frozen common Python binary64 formula provider on each actual native state, then compares those formulas with independent MP references. It also reports the native stored RCG/PGA scalar norms alongside the new MP norms. Those are distinct evidence sources. The common-provider comparison cannot be relabeled a verification of captured native analytical vectors; that vector-level native implementation check remains pending.

The MP rotation reference retains the previously used central difference `h=1e-20`; W/RIS reference formulas retain their previously verified definitions. No new mathematical reference or numerical threshold was introduced for packaging.

## Own-block stops are not final-joint stationarity

| Final joint diagnostic | Native MP100 result (rounded here) | Status |
| --- | ---: | --- |
| RCG normalized tangent norm |3.32356538092610e-4| above 1e-6 |
| PGA projected-gradient norm |2.78912015940713e-6| above 1e-6 |
| W unit-gradient-step power-ball projected residual |0.284586782169305| no author absolute numerical W gate reported |
| W ray-estimated-multiplier gradient residual |2.58062548059009| diagnostic, not a certified KKT multiplier |

W1's own projected residual is about 5.79705e-11, but W2 through W12 already return at roughly 0.28005 to 0.28450 under the original objective-relative branch. Their large residual is therefore present at the W returns and cannot be attributed solely to later variable coupling. The [W2 exact replay and before/QP diagnosis](../W2-exact-replay-before-QP/README.md) provides a separately scoped causal check of that Python state; it is not silently applied to the native trajectory.

The native W multiplier values in this package are ray estimates, with nonzero complementarity diagnostics where applicable. They are not actual frozen-QP `nu` values or independent KKT certificates. W has no reported author absolute numerical stationarity gate; no W or joint stationarity PASS is assigned.

## What the two-language comparison means

The included comparison only reads the two existing scalar JSON results. Both trajectories have 12 AO blocks. Native minus Python final utility is 5.993981915253244e-7, rate 5.999817389579221e-7, NMSE 5.835476546423024e-11, and iota 1628.3155004903674. It preserves actual iteration/stopping differences. Agreement of optimized scalar outputs is not a same-state check, identical trajectory, solution identity, or original-reference PASS. No physics or optimization was rerun for that comparison or this packet.

## Original model, disclosed reconstruction controls

Both languages use the same complete 28-member configuration and source-bound case014 scene. Source/config digests and references to the existing public input files are in `provenance-and-scope.json`. The original problem and algorithm families are kept, with independently assessed explicit-interference/factored-QP arithmetic and the stable equivalent PGA objective difference.

AO 500, W 10000, RCG/PGA 5000, their numerical tolerances, the growing RCG seed (first 1 then twice the last accepted step), and PGA relative 1e-10 are disclosed reconstruction choices or extensions, **not recovered author numerical budgets**. The printed relative-objective/relative-step/iteration-cap OR stopping form remains distinguishable from strict stationarity. Prior capped/failed variants and their evidence are retained in the surrounding published case014 history.

## Stored data and reader scope

- `saved/actual-native-first-scheme-states.mat` is the original 771973-byte MAT file, copied whole-byte. It is authoritative for complex values, signs of zero, classes and shapes. It contains the cold initial state, 36 actual returned states, fixed AO iota values, original statuses, original scene/configuration and result.
- `evidence/actual-native-MAT-typed-binding.json.gz` is the existing 111-array shape/class/IEEE binding receipt. Its `mat_dtype=False` values preserve complex entries. The `mat_dtype=True` load was used only as a class shadow, never as numerical data. 72 shadow warnings and 5 exact compact-double casts are disclosed; they were not suppressed or reinterpreted as new scientific failures.
- `saved/native-full-result.json.gz` retains the full original scalar histories and result. `saved/common-Python64-at-native-endpoints.json.gz` is explicitly the actual common-provider fixture used by the MP audit, not a native recorded gradient vector.
- `evidence/actual-native36-final-MP80-MP100.json.gz` is the complete actual MP report. The compact summary, source/schema inverse, original natural-terminal receipts, first import failure and scalar two-language comparison are also included.
- `sources/executed-native/` holds the three original native executable sources, whole-byte. `sources/executed-MP/` and `sources/independent-reference/` hold the actual independent reader/schema and mathematical reference source bytes. The original MP entry is private-manifest/path bound; this is **not a validated portable MP launcher**.
- `inspect_saved_evidence.py` is a relative, standard-library-only integrity/schema inspector. It reads the manifest and stored summaries; it performs no model, derivative, MP, optimizer, RNG, MC or MAT numeric conversion. Its result must not be called a scientific replay.

JSON publication changes private path metadata strings only. Every numeric token, decoded float64 bit pattern and nonpath MP string is retained. Gzip is lossless; the authoritative MAT and executable sources retain original bytes. `transport-preservation.json` documents this transport scope. It does not turn source hashes, lifecycle, integrity inspection or stored Boolean fields into scientific PASS.
