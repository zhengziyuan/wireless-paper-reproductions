# Source conflicts and numerical correctness corrections

Source: supplied final R2 TeX, SHA256
`6e27fb9fd2ba0decc9d7bcfc54bcb73612553f91f6df923ab502e7d561058cb0`.
These corrections are independently derived, not a claim that a publisher has
issued an erratum. Full6000-start figure execution and original-plot agreement
remain separate gates.

## COMM-GEOMETRY-FIG7: the source axis and the original plot disagree

Eq3's array exponent is `r*cos(az)*sin(el)+c*sin(az)*sin(el)`.
For a literal2x1 array, c=0 and cos(az)=cos(-az), so every possible phase/shift
state has an even azimuth beampattern. This is an identity, independent of the
optimizer or parameter tuning.

Original `21simul.eps` has two strongly asymmetric MIS paths: each differs from
its reflection by0.03895558 linear SNR. The text/caption says2x1; both cannot be
correct under the same Eq3 coordinate convention. A consistent correction is
a1x2 array in Eq3's coordinates: the same two elements, same two MS2 positions,
same1x1 movable layer, same four users, same elevation45degrees and spacing.
The alternative editorial repair would swap the row/column axes in the model;
the supplied source does not uniquely identify which label was intended.

`figures.json` selects the original-plot-consistent1x2 orientation and retains
`source_ms1_shape:[2,1]` and this correction ID. No aperture/population reduction
or optimizer substitution occurs. The literal2x1 diagnostics remain preserved.

There is an independent, unfitted closed-form check for this tiny case, not a
replacement for the requested optimizer bank. Let
`b(a)=pi*sin(45degrees)*sin(a)`. Pair the+20/+60 directions and their negative
reflections. Each beam's phase centre is the midpoint of its two b-values.
Then its minimum SNR is
`0.04*cos((b(60)-b(20))/4)^2=0.03670704015`.
Evaluating these derived phases over all360 original EPS samples gives maximum
absolute path errors below8e-8 for both MIS beams and SMS, with no fitted phase,
spacing, reference gain or angular samples. `../audit_communication_geometry.py`
independently checks the complete paths/axis calibration and the structural
symmetry contradiction. This analytic calculation does not count as a6000-start
RCG result.

The same original markers also establish40degrees adjacent user spacing,
not the paragraph's20degrees. Fig11's1x64/1x36 position count is29, not28.

## COMM-OBJECTIVE-SIGN

P2 maximizes the negative softmin. The printed negative-gradient descent
directions for that same objective have the opposite sign. The implementation
minimizes its negative and changes all derivatives consistently. A literal
printed-descent convention remains available for comparison.

## Implementation corrections, not original-paper numerical parameters

- The communication source's `while gradient above threshold` permits an
  initially stationary continuation subproblem to finish immediately. The
  old implementation incorrectly forced a first step, sometimes reporting a
  line-search failure although the actual residual already passed. Initial
  stopping now uses the same unrelaxed global threshold.
- Near the optimum, subtracting two LSE objectives with an unrelated
  `mu*log(K)` offset can reverse an increment's sign. The exact increment uses
  field differences and `log1p(sum(weights*expm1(-dg/mu)))` for small changes;
  shifted LSE is used for large changes. No objective, gradient or Armijo
  tolerance is changed. Nine independent75-digit Decimal field/LSE tests cover
  full original100-element/32-user dimensions and both objective conventions.
- Exhausted raw PR block directions can restart only that block as minus its
  gradient, using the identical Armijo inequality. Raw PR values remain stored.
- A block already below `global_tolerance/sqrt(number_of_blocks)` can remain
  unchanged if its line search is exhausted at floating-point accuracy. The
  actual global KKT norm is always recomputed and must still pass the original
  threshold; no successful stop is inferred from this block safeguard. For
  the simplex this uses its true projected-gradient contribution, not a
  boundary-normal row-mean component. Other blocks can then take real descent
  steps. This explicitly prevents a2e-9 phase block from blocking a1e-6 phase
  block, without relaxing the global1e-6 criterion.

The source's open multinomial manifold and its Euclidean closed-simplex
projection are incompatible at boundary zeros. The projected KKT measure and
active-boundary safeguards remain disclosed as numerical corrections. They
do not eliminate the schedule during optimization or silently introduce a
Fisher metric. All6000 starts and4000 inner caps are retained; these particular
communication counts are inferred settings, not stated paper values.
