# Explicit solver erratum: same original MIS scenes, corrected RCG

This is independent reproduction code, not recovered author code. The printed
block algorithm is preserved; a separately named corrected branch addresses
the coupled constrained solver. Neither branch claims a global optimum or
guaranteed convergence of every nonconvex start within the finite cap.

Equation locators refer to the author-supplied final R1 of *Wireless Sensing with
Movable Intelligent Surface*, [DOI](https://doi.org/10.1109/JSTSP.2026.3681476),
TeX SHA-256 `B0AC3782B11CDB7D2B0D1DFE581BFCFBE17C72C52F64AEF3E55CD0BFCE25592A`.
The private manuscript is not distributed.

## Confirmed source/theory issues

1. **Independent block PR is not standard product conjugacy.** Equations
   (38)-(41) use independent PR coefficients although every block affects the
   same ALM objective. For the independently checked coupled quadratic
   `H=[[4,1],[1,3]]`, `x=[1,2]`, after an exact first joint line minimization,
   one raw product PR coefficient yields H-conjugacy error below `1e-12`.
   Independent block coefficients instead give error `8.432867724867725` and
   an uphill second direction. This does not mean every printed run fails; it
   shows why standard product-CG properties cannot automatically be attributed
   to independent coefficients. The corrected branch uses **one raw product
   inner-product PR coefficient, never PR+ clipping**, with logged feasible
   active-face and non-gradient-related restarts. See the authors'
   [Manopt CG source](https://github.com/NicolasBoumal/manopt/blob/master/manopt/solvers/conjugategradient/conjugategradient.m)
   and [matrix-manifold text](https://sites.uclouvain.be/absil/amsbook/) for the
   geometric distinction; no imported PR+ solver is substituted here.

2. **The open-simplex construction and closed projection conflict.** Section IV
   constructs a positive simplex but Euclidean simplex retraction produces
   zeros. The boundary is not a smooth multinomial manifold; a nonzero row-mean
   gradient there is not necessarily a KKT violation. The corrected branch
   retains the original schedule variable/projection, uses its closed-simplex
   tangent cone, resets memory at active-face changes, and verifies the
   projected-simplex KKT mapping. No scheduling elimination is performed.

3. **Global compactness is not established as written.** The product includes
   `eta in R`, and an open positive simplex is not compact. A bounded-level-set
   argument can instead use bounded SINRs and the fixed ALM's coercive eta
   dependence. That is different from global compactness. This code verifies
   measured residuals; it does not silently supply a stronger theorem.

4. **Finite squared ALM is not automatically an exact penalty.** The Section IV
   inference from feasible ALM stationarity to original KKT needs multiplier
   consistency and complementarity. Counterexample: minimize `-eta` subject to
   `eta<=1`, multiplier `2`, penalty `10`. The squared ALM is stationary at the
   feasible point `.9`, but its effective multiplier `1` has complementarity
   `-.1`. Acceptance now independently evaluates the original constrained
   Lagrangian gradient, primal/dual feasibility and complementarity with final
   multipliers. For PSLR, the certificate is explicitly for published **LSE
   finite-mu/epsilon constrained P3.1**, not the ALM subproblem P3.2,
   an unsmoothed optimum, or a global optimum.

5. **Forced motion from an already stationary initial point is unnecessary.**
   Algorithm 1 forces a first move even if the supplied point meets accuracy;
   floating-point line search may then report a false failure. The corrected
   branch returns immediately only after checking the same actual KKT residual.

6. **Outer indexing and stopping need explicit interpretation.** Algorithm 2
   increments the outer index before a distance expression referring to a
   future point; code compares actual previous/current points. Algorithm 2 has
   OR while the numerical paragraph has AND for **early** termination and a
   fixed 30-outer cap. Both options remain. Completing 30 is valid budget
   termination without triggering early AND; neither event alone proves KKT.

7. **Fixed positive epsilon changes the PSLR smoothing limit.** Section V
   states that its LSE converges to the unregularized PSLR as mu tends to zero.
   With the displayed fixed `epsilon>0`, its actual limit is
   `min_j S_k/(S_j+epsilon)`, not `min_j S_k/S_j`. For example, target and
   opponent echoes both one with epsilon one give `.5` rather than `1`.
   Recovering unregularized PSLR requires epsilon to vanish as well and
   appropriate positive-denominator conditions. This implementation preserves
   the displayed finite-epsilon objective and labels its certificate honestly.

8. **The positive-part ALM expansion needs the active index set.** Section IV's
   expansion after “if any constraint ... is active” sums quadratic terms over
   every k. Section V repeats this for PSLR. The displayed max/positive-part
   objective instead expands only over `A={k:lambda_k+rho*q_k>0}`; inactive
   indices contribute exactly zero. For `q=[-2,1]`, `lambda=[0,0]`, `rho=1`
   and eta zero, the actual ALM is `.5`, while the all-index expansion gives
   `2.5`. The stated gradient using `chi=[lambda+rho*q]_+` and this code's
   positive-part objective are consistent; the all-index intermediate
   expansion is not used to replace them. The correction is to restrict its
   sums to A, not to change any model, penalty or algorithm.

**Not a proven source error:** with orthogonal-projection transport and a
current tangent gradient, `<g_current,g_old>` equals
`<g_current,Proj_current(g_old)>`. The printed numerator's implicit transport is
therefore equivalent under its embedded metric. Regression tests verify this
identity; it is not blamed for the failure.

## Confirmed reproduction/numerical issues

- Subtracting ALM values near `-49.5` reversed signs of genuine decreases at the
  full-size checkpoint. Exact algebraic SINR/ALM increments are independently
  verified against Decimal60. Eleven frozen plain stored-endpoint tests remain.
- Stored normalized complex phases have sub-ULP radial drift. For very small
  circle steps this can dominate the intended tangent decrease.
  `exact_unit_circle_sensing_increment` evaluates the same **mathematical circle
  model**, using `cos(delta)-1=-2*sin(delta/2)^2`. Eleven separate tests compare
  it with independently normalized 60-digit circle endpoints, not slightly
  non-unit stored numbers. Decimal is test-only, never the runtime solver.
- The same exact increment is now available for PSLR over the **entire 3600
  clutter grid**, all nine targets and all 25 positions. Ratio cross terms and
  `-mu*log(1 + sum_j pi_j*expm1(-delta_ratio_j/mu))` avoid close-softmin
  cancellation. Large changes use the new centered exponent directly so an
  old underflowed opponent can become active. Positive new echo denominators
  are evaluated directly instead of `old_echo+delta_echo` cancellation. Ten
  independent 3600-opponent Decimal60 identities include tiny decreases,
  large irrelevant ratios, underflow-to-active changes and large changes;
  full M400/N256/K3609/U25 ALM and analytic-gradient tests are separate.
- Explicit prepared forward bundles reuse the **identical** field arrays in
  the ALM value/gradient and current-iterate difference. This removes redundant
  forward calculations, not any target, opponent, coefficient or scene. Cache
  reuse is guarded against phase-array changes. Cached/uncached identities
  are tested. No test error bound is an optimizer acceptance slack.
- The old acceptance gate wrongly required early AND after completing the fixed
  outer budget. Status now separates `outer_early_stopping_met`,
  `prescribed_outer_budget_execution_complete`, and independent original KKT.
  This was a reproduction metadata bug, not proof of invalid 30-iteration paper
  experiments.
- At the independently computed factor-100 near-stationary diagnostic state,
  `sum_j S_j-S_k` loses small interfering echoes beside the much larger wanted
  echo. Its self-term subtraction in the ratio derivative amplifies this error.
  The old evaluator accepted a false decline: for the same phase-curve trial at
  alpha `1e-9`, the independent normalized Decimal60 ALM increment is
  `+3.64912886954e-18`, but the old increment is `-4.03994077854e-18`.
  Version v4 explicitly sums **every j except k**, also for signed echo
  increments; the target ratio derivative omits its self term before summing,
  and the new denominator uses direct positive new echoes. The corrected
  increment is `+3.64340220683e-18`. This is the same complete SINR formula,
  not changed normalization, a metric/preconditioner, or an algorithm substitute.
  A shared frozen independent-state fixture checks both ascent signs and
  numerical errors in Python/MATLAB. Its test error bounds are never Armijo slack.
- The previous unpublished interpolation upper safeguard `.9` only contracts
  a repeatedly rejected bracket by `.9` in the worst case; 60 evaluations then
  cannot reach a sufficiently short feasible-face step. Version v4 discloses
  upper safeguard `.5` within the same bracketing/secant procedure and the same
  60 evaluation cap. The unpublished minimum descent cosine is now `0`, so
  only non-descent directions are restarted. Raw product PR, Armijo/curvature
  constants, projection/retraction, objective and all stopping tolerances stay
  unchanged. The old source, failed attempts and all bank records are preserved.
  Full cold starts 6 and 10 each satisfy all 30 original inner accuracies and
  the final original constrained KKT gates. Start 8 still hits a genuine inner
  cap although its final constrained KKT passes: failures are not erased or
  certified. These individual runs are not a complete 6000-start bank.

The corrected line search checks canonical Armijo and curvature along the
original normalization/simplex retraction. Unpublished choices are explicitly
declared: `c2=.1`, minimum descent cosine `0`, initial step `1`, safeguarded
interpolation interval `[lo+.1*(hi-lo),lo+.5*(hi-lo)]`.
All failures remain visible. There is no acceptance
slack, relaxed stop, Newton/BB solver, phase-only objective, target deletion,
aperture reduction or hidden cap.

## Branches and unchanged contracts

- `settings.json` and `settings_reference_candidate.json`: printed block-PR
  branch with previously documented numerical guards.
- `settings_corrected.json` and `settings_reference_candidate_corrected.json`:
  explicit corrected raw **product** PR. The latter keeps the separately
  inferred factor-100 reference/noise candidate; its physical origin is still
  not uniquely recovered.
- All preserve **6000 starts, 30 outer, 4000 inner**, targets/displacements,
  epsilon schedule, clipping, penalty updates and `zeta_min=1e-10`. Last used
  inner epsilon is actually `1.2589254117941667e-6`, not falsely reported `1e-6`.
- Rank-one evaluation is exactly the original PSD/quartic identity. A saved
  full-dimension inner test or one complete outer run is **not** a 6000-start
  figure receipt or an original-curve certificate.

Correctness tests:

```text
python test_stable_increment.py
python test_solver_erratum.py
python test_pslr_increment.py
python test_self_excluded_sum.py
MATLAB: run_mis_sensing('unit-circle.json','unit-circle-increment-test')
MATLAB: run_mis_sensing('solver.json','solver-erratum-test')
MATLAB: run_mis_sensing('pslr-increments.json','pslr-increment-test','settings_corrected.json')
MATLAB: run_mis_sensing('self-excluded.json','self-excluded-sum-test','settings_corrected.json')
```

One diagnostic, not a full figure:

```text
python run.py --figure fig3 --diagnostic-start 1 --settings settings_corrected.json --output diagnostic.json
MATLAB: run_mis_sensing('diagnostic.json','full-start:fig3:1','settings_corrected.json')
```

The complete corrected/reference-candidate figure retains all starts:

```text
python run.py --figure fig3 --settings settings_reference_candidate_corrected.json --output full-fig3-python.json
MATLAB: run_mis_sensing('full-fig3-matlab.json','fig3','settings_reference_candidate_corrected.json')
```

Use a new output directory after source/settings changes. Old source digests
are intentionally rejected; source mutation during a start invalidates that
execution rather than certifying mixed code.
