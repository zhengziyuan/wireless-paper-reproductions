# ISAC014: exact W2 replay and before/QP causal diagnosis

This supplement records one actual W2 update from the closed Python first-scheme run. It explains why the disclosed reconstruction can satisfy the printed objective-relative stopping form while remaining far from joint stationarity. It is not a new full trajectory or a claim that a paper formula is wrong.

The parent evidence is pinned to commit `0da55e1dbf896c6731886f4543e2292a2a407266` on `codex/resume-six-paper-reproductions-20261017`:

- [Closed first scheme and all 36 returned-state evidence](../README.md).
- [Previously completed after-state MP80/MP100 report](../evidence/actual-returned-blocks-MP80-MP100.json.gz).
- [Own-W versus final-joint scope](../evidence/actual-own-W-versus-final-joint-scope.json).

## Actual scope

The source-bound replay made one original `update_w` call, one original structured QCQP solve, and two original metric evaluations. It did not force a one-step stop. Its complete returned W, status, histories, and numeric IEEE bits matched the previously saved W2. Both this replay and the later saved-only MP80/MP100 audit returned naturally with code 0 and closed their source intervals. The latter performed no new QCQP solve, W iteration, after-W2 physical evaluation, optimization, RNG, or MC.

W2 used fixed iota 60348785663.072914. Its original utility changed from 18.763668891224427 to 18.763668897607776; recorded relative objective change was 3.401972715214167e-10, and relative W displacement was 0.12978891263425377. It stopped by `relative_objective_tolerance` after one of the available 10000 iterations. Actual `nu=0`; actual power 0.39166181231512937 was below 0.3981071705534972. All 80 captured numeric arrays were finite, and the original transmit0 calculation equaled actual power; there was no NaN-driven false comparison.

## What the saved arithmetic establishes

| Quantity | MP100 result (rounded here; full digits remain in JSON) |
| --- | ---: |
| Original gradient at Wold, Frobenius norm |5.25681463633324|
| Original gradient at Wnew, actual nu0 residual |5.25680385316655|
| Captured-auxiliary QP residual, absolute |1.09805048848015e-6|
| Same QP residual divided by QW/P scale |2.14152631003886e-16|
| Captured-auxiliary gradient-contact defect |6.12610478143862e-7|
| Exact original-physical theory contact defect |4.20324616241709e-92|
| Norm of2Q DeltaW |5.25681512063440|
| Physical gradient change norm |0.0106418989486985|
| Residual decomposition closure error |9.26149796395313e-93|
| Absolute DeltaW norm |0.0818912676586806|
| Energy fraction in exact-zero communication singular columns |0.9999999999999997967|

The recorded positive QT diagonal spans approximately 3.17e-9 to 2.18e9 at SINR about 4.56e8. That ratio describes the recorded diagonal, not a certified spectrum condition number of the original Q. The large total displacement lies almost entirely in the communication-null singular columns; the strongly curved communication column barely changes. The true original-objective gain is small (the existing after-MP scalar-error bound plus the new before-MP value gives approximately 6.38335e-9 to 6.38337e-9). This is a reference-based bound, not interval arithmetic or recovery of the signed after-state rounding error.

The exact decomposition is `Gafter-2nuWnew = (Gafter-Gbefore) + R_QP + 2Q DeltaW + contact_defect`. The rounding/contact and fixed-QP residual terms are much smaller than the remaining original gradient. At this saved W2, the high-SINR QT curvature and objective-relative stop explain the nonstationary return more directly than an inaccurate frozen-QP solve. This is a one-case causal result; it does not establish a unique remedy or predict every author experiment.

The old own-W report also lists a ray-estimated multiplier 3.6835223460971514 and residual 2.5253097056927085. That estimate has nonzero complementarity and is not the actual QCQP `nu=0`. These are different diagnostics and are not interchangeable.

## Algorithm and numerical-control provenance

Algorithm1 of the locally verified R1 source prints a relative-objective **or** relative-W-step **or** iteration-cap stop. Its tolerance is symbolic. The 10000 W budget and 1e-6 relative tolerance here are disclosed, unreported reconstruction controls. The sensing MM, current-W QT auxiliaries, Q/P expressions and QCQP KKT equations were checked against that source; source anchors and digest are retained in the compact report, without redistributing the private manuscript.

This package therefore preserves an actual nonstationary return allowed by the printed stopping form with these reconstruction values. It does not prove a paper formula error, nor that all reported author experiments fail. The MP80/MP100 difference 3.57e-64 versus 1e-35 only checks arithmetic precision consistency; it is not a W-KKT threshold.

## Files and replay boundary

- `saved/actual-original-W2-operands.npz`: the original 35664-byte capture, unchanged; 80 numeric arrays. Load only with `allow_pickle=False`.
- `saved/original-W2-returned-status.json`: original whole-byte W2 status.
- `evidence/actual-before-QP-MP80-MP100.json.gz`: complete actual before/QP report; after-W2 physics/gradient were reused from the parent report.
- `evidence/compact-causal-conclusion.json`: three-layer residuals, identity, original stop, paper-source anchors, gate matrix, and next-scope boundary.
- The other small evidence files preserve actual replay, finite readback and held natural-terminal facts. Their early pending flags remain historical; they are not silently rewritten.
- `sources/executed/`: whole-byte copies of the two actually executed entries. They require their original private manifests/providers/admissions. **They are not a validated portable entry.** In particular the original replay entry invokes an update and must not be mistaken for a saved-only reader. No new portable mathematical runner is claimed or executed here. Preparation labels in the archived source docstrings are retained whole-byte; actual execution is established by the accompanying original terminal and result receipts.
- `transport-preservation.json`: path-metadata-only JSON projection and 80-array dtype/shape/complex/IEEE conservation. It verifies faithful publication transport, not scientific correctness.

The reused original providers, input scene/config, full previous states and after-MP report are referenced from the parent package, not duplicated. Source/controller hashes and natural code0 establish provenance and lifecycle; they do not establish scientific PASS.

## Remaining scientific boundaries

Original physical values, feasibility, corresponding derivative formulas and actual stopping consistency can be reported separately for subsequent whole-case work. They cannot be promoted to W or final-joint stationarity. The closed first-scheme final joint RCG norm 3.3239395955e-4 and PGA norm 2.8112331162e-6 exceed the reconstruction 1e-6 strict checks; final W projected residual is about 0.2845866. All 12 earlier own-block RCG/PGA gradient stops do not remove these joint residuals. An absolute author W-KKT numerical gate was not reported.

No full-six, native whole-trajectory equivalence, original-reference, joint-stationarity, or full-paper PASS is claimed. No new W10000 run, threshold change or acceleration was made for this evidence assembly.
