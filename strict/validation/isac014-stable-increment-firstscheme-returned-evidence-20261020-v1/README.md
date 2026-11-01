# ISAC014: one cold stable-increment first scheme, with returned-state MP evidence

This packet preserves the actual new cold `Rot-BS & Rot-RIS` result, all
original absolute-value histories, the exact current configuration/scene,
and 36 returned states: twelve W, twelve RCG/theta and twelve PGA/rotation
returns over twelve AO blocks. The original child naturally returned 0 using
the same held handle. Its 21 watched-source lifetime interval and the entry's
15 source/input interval closed without host errors. The original selected
scheme checks and AO relative stop passed; these facts are kept separate
from the independent scientific results below.

## What the actual independent readback establishes

The exclusive saved-state MP80/MP100 reader actually returned 0, with its
25 source/input identities unchanged. It checked all 36 returned states and
the final own state. Physical values, constraints/feasibility and the
corresponding derivative formulas passed their recorded gates. All twelve
RCG returns and twelve PGA returns met the unchanged strict 1e-6 gradient
threshold at their own block inputs. The maximum MP80/MP100 absolute
difference was 2.07854224249465749565330675831572736924577629036600735387095120689070001632203451268995525199184817095318e-59
against the existing 1e-35 precision bound. The full per-coordinate report is
`evidence/actual-returned-blocks-MP80-MP100.json.gz`.

**Final joint stationarity did not pass.** At the actual final W/theta/r
with final optimal iota, the RCG tangent norm was approximately 3.32394e-4
and the PGA projected-gradient norm 2.81123e-6, both above 1e-6. W's
`g-2lambdaW` Frobenius norm was approximately 2.58062, unit-gradient-step
power-ball residual 0.284587 and complementarity 0.0301759. These W values
are diagnostics: no author absolute W stationarity cutoff was reported,
so a W stationarity PASS is not assigned. Exact decimal strings and the
actual derivative-error checks are preserved in the report and provenance.
W return 1 had a projected residual of about 5.8e-11, but the large residual
already exists at its own returns 2 through 12 (approximately 0.28005 to
0.28450). Their original `relative_objective_tolerance` stops are not W
stationarity certificates. Later joint changes are not the sole origin;
the last-own-W to final increase is only about 0.03035 percent. The
cause within the W update, its relative stop or conditioning has not been
isolated. A multiplier estimated along the W ray is not certified as a KKT
multiplier when complementarity is nonzero. The complete saved-report
[own-W versus final-joint readback](evidence/actual-own-W-versus-final-joint-scope.json)
is included; it does not isolate a new cause or rerun mathematics.

A returned block's strict stop uses that block's actual W/theta/r and
fixed iota. Later updates change the joint point. The final joint diagnostic
is separately identified and uses final optimal iota; an intermediate fixed
iota is never silently tested as if it were optimal. The actual AO relative
improvement 5.756358938687541e-6 met its configured 1e-5 stop after 12 of 500
allowed AO iterations. This does not establish joint KKT or full convergence.

## Sources, controls and reuse boundaries

The twelve executed source files are copied whole-byte, including historical
docstrings. The actual entry is the V2 finish-guard version. The stable PGA
comparison uses the frozen original-utility increment; original absolute
objective evaluation/history is retained. All current 28 configuration members
are saved. Caps 5000, PGA relative tolerance 1e-10 and growth-seed constants
are disclosed reconstruction controls, not recovered author numerical budgets
or initialization parameters. The gradient threshold remains 1e-6. No numerical
budget, parameter, scale or tolerance was fitted to a reference curve here.

`saved/full-result.json.gz` retains the full new result and histories. The
returned-state NPZ is copied exactly, without pickle or dtype conversion.
JSON files are losslessly preserved, optionally gzip-compressed, after
replacing private absolute-path string tokens only. Every numerical token,
integer type and IEEE64 bit is preserved. Original/public digests and exact
projection checks are in `provenance-and-scope.json`. README, provenance,
delivery records and future receipts are outside the mathematical input list.

No new portable executable or repeated MP calculation was introduced for
this package. The actual executed reader has historical local path bindings;
its SHA and complete input/source scope are disclosed. Existing independent
formulas are in [audit_cold_control.py](../../../tools/isac-line-search-replay/audit_cold_control.py),
[mp_physical_reference.py](../../../tools/isac-line-search-replay/mp_physical_reference.py),
[audit_failure.py](../../../tools/isac-line-search-replay/audit_failure.py) and
[audit_stable_derivatives.py](../../../tools/isac-line-search-replay/audit_stable_derivatives.py).
The required stable_metrics source is also included byte-identically.
The public path projection is not presented as a new executed MP invocation,
and returned endpoints are not a public replay of every AO operation.

The [historical fixed15 capsule](../isac014-AO6-fifteen-PGA-trials-stable-increment-20261019-v1/README.md)
is immutable at commit `299a1a139e5a34decb68d77a8be1f34b847a22d8`.
Its original fourteen false rejections, frozen-channel one false rejection
and old strict-PG failure remain historical facts, not relabeled new-trajectory
evidence. A separate native fixed15 receipt found both RHS interpretations
matched existing MP100 at all fifteen fixed points (exact errors and its
receipt digest are quoted in provenance). Native V1's actual interface failure
is retained. That fixed-endpoint native result is not a complete native run
or separately optimized cross-language equality.

No all-six-scheme, original 500-scenario population, complete native trajectory,
original-reference, full-paper or paper-formula-error claim is made.
