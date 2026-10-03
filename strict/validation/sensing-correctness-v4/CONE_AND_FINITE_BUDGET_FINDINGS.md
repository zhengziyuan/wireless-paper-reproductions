# MIS sensing: numerical boundary fix and remaining finite-budget limits

This is a compact audit of independently computed reproduction states, not
author simulation code, a fitted reference curve, or a claim that all 6000
starts have converged. The live numerical package remains frozen at
`bf41284cc32086f63e1b340b6f180bd1b1f00507950f55e3ab6df0e9aa4553cb`.
The reported scene remains M=400, N=256, U=25, K=9, with 30 outer calls and
4000 maximum inner iterations. The original 6000-start figure bank is a
separate campaign.

Here, "unchanged stopping thresholds" means the numeric epsilon constants and
iteration budgets. The existing corrected solver measures closed-simplex
projected KKT. It does not claim to satisfy the printed open-manifold row-mean
gradient stopping rule; closing the simplex and using its constrained
stationarity measure are explicit source/implementation errata. A small
physical KKT is not evidence that the printed row-mean gradient is small.

## Established numerical error: the same Euclidean projection

At cold start 132, cancellation in the floating-point threshold mean made the
same active-set equation alternate between two masks and raise an error. Its
exact Euclidean projection is well defined. The corrected evaluation solves
the same finite sorted threshold equation; only an ambiguous row escalates to
exact stored-binary arithmetic. Mandatory positive coordinates stay mandatory.
Twenty-two genuinely positive projected directions of approximately 1e-21
are retained, not deleted by a support tolerance. The metric and raw PR formula
are not changed.

Python checks cover the actual error, 1000 independent exact-rational random
cases, a tiny-coordinate no-pruning case, and 756 row projections from 42
actual full-scene states. The native MATLAB component separately passed all
1010 shared-fixture checks. That first MATLAB result did not record runtime
source hashes; it is not retroactively called source-bound. A fresh wrapper
requires the actual selected helper, component, fixture, and wrapper bytes to
match before and after execution and records the new output hash.

Subsequent exact witnesses identified a separate bug in the MATLAB WORK v1
helper: it inherited the order of rounded centered values in its exact
fallback, whereas distinct raw values can center to the same floating tie.
For mandatory directions +1e12 and -1e12 and optional directions 1e-5 and
4e-5, that inherited order can give the wrong exact threshold. A row-norm
scaled error bound can hide the error in the small coordinate. The Python
exact fallback already re-sorts raw values and is unaffected. A distinct
MATLAB helper v2 re-sorts the original raw binary values and a source-bound
test checks both orders at three scales using per-small-component bounds,
in addition to the unchanged 1010 cases. Actual fresh native execution passed
all 1016 cases with runtime-selected source and input hashes unchanged before
and after execution. The same execution reproduced three original-v1 errors
under the strict small-coordinate checks. The older limited 1010 results
remain historical and are not promoted as universal projection correctness.
Exact validated helpers, the bound wrapper, synthetic fixtures, and native
receipts are available in `components/same-cone-v2/`; this remains a component
certificate, not a MATLAB full-30 trajectory or live-v4 production promotion.

The repaired Python cold start 132 completed all 30 actual inner precision
requirements. Independent Decimal60 original-constrained KKT is
1.1104424790768169e-6, below the actual last-used tolerance
1.2589254117941667e-6. The positive primal residual is 2.003119525e-8 and maximum
complementarity is 2.537722555e-9. This is one separately recorded cold run,
not an overwrite of the earlier fixed-control suite's start-132 error or a
native MATLAB full-trajectory certificate.

## Not fixed by scalar INITIAL step prediction

Two predeclared, fresh, original-size cold runs used uniform initial
multipliers, an a-priori physical SINR ceiling as initial eta, and the
same-retraction scalar curvature only to propose the initial line-search
step. Subsequent directions, metric, acceptance constants, actual allowed
accepted steps, precision schedule, 30 calls, and 4000 cap were retained.
The exact raw-face v3 helper and the same Euclidean cone fix were explicit.

| Cold start / inner | Decimal60 actual ALM KKT at 4000 | Required current epsilon | Result |
| --- | ---: | ---: | --- |
| 28 / outer 6 | 0.00142434750864649 | 0.000316227766016838 | True inner failure |
| 8 / outer 25 | 0.00127301338035894 | 0.000003981071705535 | True inner failure |

Passive captures reproduced both actual stops and every INITIAL step seed
bitwise. Both inners had zero evaluated or accepted generalized simplex kink
events. Every accepted step met ordinary smooth strong curvature and the
unchanged Armijo condition. Neither initial-step guard was reached. The
maximum line-search trial counts were 13 and 23, below the unchanged 60 cap.
Independent local full-657 angular-plus-eta curvature checks show positive
curvature spreads of approximately 129386 and 4823967. These are local
numerical conditioning diagnostics, not global convexity proofs.

The selected final states of both full-30 runs do meet independently checked
original-constrained KKT. That later result cannot make an earlier
current-epsilon inner failure disappear. The required two-start preflight
failed, so no survivor-selected 19-start follow-up, new 6000 campaign, or
production promotion was performed for this scalar-INITIAL variant.

## Certificate boundaries

The earlier fixed-INITIAL-one 19-start suite retains all outcomes: 18 complete
numeric full-30 receipts, of which 16 pass all gates and two have genuine
inner caps (28 and 177), plus the original scientific execution error at 132.
The separate projection repair does not rewrite that suite. Existing v2 face
geometry receipts are not transferred as v3 certificates.

An exact eta conditional root would hold the phases and schedule fixed. None
of the inspected 8000 product directions was pure eta; replacing their mixed
product steps with that root would not be the same RCG line search. No such
update, metric/preconditioner, direction change, hidden tolerance relaxation,
extra inner budget, or physical noise/gain fit was used.

The R1 source (SHA
`b0ac3782b11cdb7d2b0d1dfe581bfcfbe17c72c52f64aef3e55cd0bfce25592a`)
reports the finite budgets at line 934 and makes each current inner precision
conditional at lines 613–616. A conditional/asymptotic stationarity statement
does not supply a finite-4000 guarantee. The separate compactness and printed
forced-first-step issues are documented in
`R1_FINITE_BUDGET_AND_COMPACTNESS_AUDIT.md`; this audit does not assert that
every aspect of the paper's theory is false.

Immutable compact evidence is split into
`SAME_CONE_COMPONENT_COMPACT_v1.json`,
`SAME_CONE_132_FULL30_DECIMAL60_v1.json`, and
`SCALAR_INITIAL_ORIGINAL_BUDGET_CAPS_v1.json`, with hashes in
`CONE_AND_CAP_EVIDENCE_FREEZE_v1.json`. The runtime-bound native rerun will be
a distinct evidence version, never a retrofit of the first unbound result.
The separate repair snapshot's v1 label about an unchanged "theoretical model"
was too broad; a later evidence version narrows this to the physical echo/SINR
formula and numeric thresholds, with the closed-domain stationarity erratum
made explicit. The old frozen snapshot is retained, not rewritten.
