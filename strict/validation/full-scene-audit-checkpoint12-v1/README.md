# Full-scene investigation checkpoint 12 — not a complete release

These are actual fixed-input audit findings, not a new set of successful
published figures. The six-paper release still has
`full_reproduction_passed: false`. [Evidence identities](evidence.json) distinguish
completed checks from prepared or running work. The original manuscripts,
third-party runtimes and private historical simulation source are not included.

## ISAC: an actual full-size raw-PR non-ascent failure

The earlier [exact algebraic counterexample](../rotatable-isac-raw-pr-scope-v1/README.md)
was not an actual paper-channel cold run. A separate original first-RIS cold
attempt now uses M=4, N=36, K=2, 66 sensing directions, six streams, both paths
and all 14,688 coefficient terms. It starts at the original all-one RIS state,
with the existing original fixed W/rotation/iota context.

There are 19 accepted updates (iterations 0 through 18), followed by the
20th gradient check at iteration 19. The raw PR coefficient is approximately
3.19980315315, but the gradient-direction dot product is approximately
−11.3174949281. Exact reconstruction of the stored finite operands and the
separately saved full Cartesian MP100 terminal gradient both give a dot below
−11. Positive beta means merely clipping negative beta to zero would not fix
this candidate. All 80 original diagnostic alphas fail the stored Armijo
inequality; none is applied, and the next halved alpha is explicitly untested.

The independent terminal normalized gradient is about 1.02122284168, not at
the original 1e-6 stop. A separate read-only audit passes all 83 stored-tape
checks over all 249 events. It checks stored arithmetic and state links; it
does not independently recompute every intermediate physical gradient or
line-search increment. Initial and terminal physical/36-coordinate finite
difference checks are separate actual evidence, not an interval theorem.

This qualifies the supplied R1 source's unconditional description of raw PR
as an ascent direction. It does not refute all conditional RCG convergence
theorems or certify a final-publisher erratum. Diagnostic rejection after the
non-ascent boundary is explicitly not literal pseudocode equivalence.

The inherited first W block was genuinely capped at 10,000 without its original
relative stop. That failure remains. A distinct cold W experiment changes only
this unreported cap, retaining original QT/MM, all six schemes and thresholds.
A separate explicitly labelled direction erratum retains raw PR but requires
`g·d >= ||g||²/10` and `||d||² <= 100||g||²`, otherwise using `d=g` and recording
the direction actually used in PR/BB1 history. Its corrected cold execution is
not yet certified here. No isolated RIS result can certify full AO or a figure.

## Cooperative SatCom: cancellation in our double-precision evaluation

Two retained failed reporting cases contain 91 actual full-size fixed-context
phase endpoints. Computing a variance by subtracting a large squared mean
from a large fourth moment loses precision near stationarity. This is an
implementation numerical issue, not a demonstrated error in the paper's
finite-Rician model.

An algebraically equivalent conditional-positive/Wick expression retains all
paths, stored amplitudes, covariances and derivatives. Actual double-precision
reevaluation passes all 91 endpoints and all 8,190 gradient components against
the existing independent MP80 references, at unchanged absolute 1e-9 plus
relative 1e-10 reporting bounds and original 1e-6 gradient threshold. A separate
read-only audit verifies exact dtype/shape/byte roundtrips of all 3,712 saved
arrays. No covariance clipping, replacement channel, new MC population,
optimizer or new MP reference was used in this component check.

This does not repair or overwrite the old failures, establish a fresh complete
183-point trajectory, certify native MATLAB parity, or recover historical curves.
The complete original 91-input native fixture has separately passed lossless
readback and retained MP-stop checks; actual native physical execution remains
pending and is not inferred from fixture export.

## MA: source qualification and missing benchmark evidence

The complete 200-geometry dual audit passes the declared implemented stopping
contract and full 1,000-draw physical checks. However, the supplied R2 stop
references local SCA minorants, whereas the implementation compares global
design objectives after a full coordinate sweep. Tangency supports this declared
interpretation, but the author's unique historical stopping trajectory has not
been recovered. Existing “source stop” fields must be read with this qualification.

The reported power gain/noise conversions are consistent with the supplied
source; a curve gap alone is not permission to change them. Nr/Nc, initial
positions, the complete joint angle law, counts and convergence-curve aggregation
are incompletely reported. Under the declared independent uniform angles,
swapping a 2-by-3 and 3-by-2 aperture is not distribution-equivalent. No closer
orientation, fitted gain, selected geometry or survivor average has been chosen.

Late trajectory completion and index 0/1 choices do not explain the observed
approximately four-bit/s/Hz gaps. For kappa=100, the native true terminal mean is
14.8421297 for MA-MRT and 28.8713395 for MA-ZF; extracted author-EPS endpoints
are approximately 19.06639 and 32.56491. These are finite evidence comparisons,
not recovered final-publisher results or a universal impossibility claim.

An actual read-only inventory of all 300 Fig. 16 records finds all five families'
1,000 rates, but none of the three FPA families has saved per-draw W/power/leakage,
QT histories, stopping records or KKT residuals. Aggregate zero cap counts cannot
stand in for those missing independent checks. Original MA positions and
coordinate histories do exist. Complete original-model cold recording and a
distinct full-population evaluator are being prepared/run separately; missing
historical states are not manufactured. Printed correlated-ZF dimensional
errata and their corrected Schur/Laplace evaluator remain separately labelled.

## Scope of this checkpoint

No new complete figure, native optimization, rigorous interval certificate or
hardware measurement is certified by this packet. Running/prepare-only work is
never a pass. Source errors, reconstruction errors, numerical repairs and
unresolved historical inputs remain different categories. All previously
retained failures remain available in their original evidence lineages.
