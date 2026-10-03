# All-paper correction and execution ledger

This is an independent MATLAB/Python reconstruction from the supplied author
sources. It is **not a completed release**, recovered private author code, or a
claim that every historical figure is correct. The source inventory contains
85 captioned figures (73 numerical, 12 illustrative/hardware) and two parameter
tables. Every panel, baseline and full declared sample bank is required. Counts
explicitly reported by a source are preserved; unreported Monte Carlo counts
and random seeds are disclosed reconstruction choices, not recovered author data. Full-size
single cases and component tests are recorded separately from complete figures.

## Verified issues and their disposition

| Paper | Source issue versus implementation/numerical issue | Disposition and evidence |
| --- | --- | --- |
| MIS communications | Figure7's printed 2x1 orientation and Eq3 imply azimuth-even patterns, while the original two MIS curves are not even. The user markers also contradict the text's adjacent spacing. | [COMM_ERRATA.md](mis-communications/COMM_ERRATA.md) proves the conflict. The separately labelled 1x2 orientation preserves two elements, two patterns and four users. An unfitted two-element derivation agrees with all three original patterns at approximately 8e-8 absolute linear SNR error. This is not the complete optimizer bank. |
| MIS communications | Subtracting nearly equal LSE costs can reverse a small decrease; a forced move at an already stationary point was a reconstruction bug. A numerically inactive phase block could block other legitimate descent. | Exact LSE increments, initial KKT checks, and a disclosed per-block KKT accuracy-share safeguard preserve objective, gradients, raw PR, full start counts and global tolerances. Independent Decimal tests and actual MATLAB checks are separate from full sweeps. |
| MIS sensing | Independent block PR does not generally possess product-CG conjugacy; the positive-simplex manifold conflicts with a projection that reaches its boundary. The source's compactness/exact-penalty claims require qualifications. | [SOLVER_ERRATUM.md](mis-sensing/SOLVER_ERRATUM.md) provides counterexamples, a separately named raw-product-PR correction, feasible tangent-cone/active-face handling and an independent original constrained KKT check. The printed branch remains selectable. No global-optimum claim is made. |
| MIS sensing | Algorithm2's indexing/OR stopping differs from the numerical paragraph's early-AND rule. Requiring early stopping after the prescribed 30 iterations was a reconstruction metadata error. | Budget termination, early termination, every inner accuracy and original KKT are distinct fields. Last actually used inner epsilon is 1.2589254117941667e-6. Completing 30 alone is not convergence. |
| MIS sensing | Section V's fixed positive denominator epsilon means the LSE limit as mu tends to zero is the epsilon-regularized ratio, not exactly the unregularized PSLR. | Preserve Eq54's regularization and the source's full60x60 opponent grid/guard. Describe computed values and KKT only as finite-mu/epsilon regularized PSLR; recovering the unregularized limit additionally needs epsilon to vanish and positive denominators. |
| MIS sensing | Physical reference/noise units are underspecified; the old unconditional numerical-bound violation claim was unjustified. Finite-aperture chirps previously used inconsistent phase origins. | [Normalization](mis-sensing/SIGNAL_NORMALIZATION.md) and [closed-form convention](mis-sensing/CLOSED_FORM_CONVENTION.md) keep literal and inferred factor100 contracts separate. Shared-origin finite-field identities are checked. Neither a reference fingerprint nor dual agreement proves original Figure2/3 recovery. |
| Rotatable ISAC | The printed BB1 ascent step uses the descent secant sign, producing negative step curvature and clipping. Several numerical controls are not reported. | [Source contract](rotatable-isac/source_contract.json) distinguishes literal BB from the disclosed ascent-sign correction. QT/MM, raw-PR RCG, PGA/BB, all six schemes and 100 channels per point are retained. A larger unpublished W iteration allowance solves the same block; failures under the previous allowance remain preserved. |
| Two-timescale MA | Correlated-ZF products have incompatible N-antenna/M-user dimensions; the row-correlated Gram is not the asserted ordinary Wishart model. | [Exact evaluation](two-timescale-ma/CORRELATED_ZF_EXACT_EVALUATION.md) derives the original-model inverse-Gram expectation using conditional Schur complements and a one-dimensional Laplace integral. Actual full1000-draw MATLAB/Python checks agree. This corrects the bound, not the undefined printed closed form or automatically its historical plots. |
| Two-timescale MA | Generic conic numerical solves failed on valid original coordinate subproblems. | A certified exact two-dimensional convex-subproblem backend preserves original MRT AO/SCA and ZF AO/MM. It verifies each coordinate's box/spacing feasibility and global concavity-gap certificate. It is not a new outer optimizer or a shrunken geometry/NLoS bank. Old failed solves remain preserved. |
| Two-timescale MA | An original-size ZF case actually exhausted the reconstruction's unreported 1500 AO allowance. | A separate same-input cold replay with allowance10000 reached the unchanged5e-5 stop at1599 sweeps. The first1500 objectives,1501 positions and9000 coordinate records are bitwise identical; every accepted position is evaluated using all1000 original draws. The old failure remains a failure. Fresh full200 banks, not relabelled old outputs, are required. |
| Cooperative satellite | Complete original eight-scheme chains and final-publisher source equivalence remain to be verified. No paper error is inferred merely from incomplete execution. | Finite-Rician moments, statistical/two-timescale models, AP/MR QT and original RMO are retained. Original all-scheme execution is underway; capped or unfinished chains are never averaged as successful results. |
| Hotspot satellite | Full-rank average-SINR QoS is not the printed scalar SOC; the interference index omits transmitted streams; imaginary norm factors cannot implement negative squared norms. Normalized-projector expectations and shared-G fourth moments need correct treatment. | [STATISTICAL_ERRATUM.md](hotspot-satcom/STATISTICAL_ERRATUM.md) derives exact vector-QT QoS auxiliaries within the original QT framework, full finite-Rician moments and normalized-projector integrals. The corrected branch is explicit, not silently described as the printed formula. Original instantaneous/LoS substitutions are forbidden. |
| Hotspot satellite | The reconstruction used per-user path loss where the source specifies a common400m ground amplitude; conic epigraph conditioning and unreported RGD initial step lengths also caused numerical failures. | The shared400m amplitude must be restored without altering position-dependent phases, followed by source-matched reruns. Exact epigraph elimination/positive scaling solve the same original convex block. RGD retains its direction, retraction, Armijo and stopping threshold; numerical controls are disclosed rather than called author data. |
| Hotspot satellite | The supplied thesis uses a Bessel expression as antenna power gain without explicitly squaring it or including maximum gain. The literal expression can be negative. | This is an amplitude-versus-power convention or typographical ambiguity in the supplied source, not an established final IEEE version error. The disclosed simulator uses nonnegative Gmax times the square, as in the primary satellite model's Eq3. See [ESA pattern contract audit](hotspot-satcom/audit_esa_pattern_contract.py), [source erratum](hotspot-satcom/SOURCE_ERRATUM.md) and [primary model](https://link.springer.com/article/10.1186/s13638-020-01749-7). No antenna gain is fitted to a figure. |

**Not an established sensing source error:** under the embedded metric,
orthogonal projection transport gives the same current/old gradient inner
product. Tests verify that identity; transport omission is not blamed for
the observed failure.

## Additional execution repairs and remaining precision limits

- The related-ZF v2 full1000-draw aggregate physical metrics agreed, but some
  individual conditional quadratures failed fixed dual tolerances or reported
  error envelopes. A 50/80-digit independent audit confirmed a missed narrow
  integration interval, not a change in the theoretical model. Deterministic
  segmentation of the same original Laplace integral gives fresh v3 Python
  errors at most5.56e-17 at all30 retained outliers. Original dual tolerances
  and error-envelope gates are unchanged. Fresh independent MATLAB/Python
  N6/M5 and N8/M5 runs each use all1000 supplied draws and all5000 conditional
  integrals per channel model; both now pass every original fixed-tolerance,
  reported-error and physical-metric gate. This certifies the checked fixed
  positions, not all geometries or a historical figure. Old failed v2 evidence
  is preserved, not overwritten by v3.
- Cooperative RGD's reconstruction incorrectly upgraded a gradient threshold
  ten times. The actual1e-6 threshold is restored. Exact polynomial increments,
  positive spectral step seeds and disclosed larger unreported safety caps
  retain the original gradient direction/retraction/Armijo and all eight
  schemes. A fresh complete-size base case passes all four gates; all sweeps
  and publisher/reference agreement are separate. Failed old cases are kept.
- Hotspot Fig3-9 explicitly says that at fixed M, element count changes only
  aperture gain. Scaling center coordinates with aperture area would change
  propagation phases as well and is a reconstruction error for that sweep.
  The [count-only adapter](hotspot_element_count.py) and independent MATLAB
  counterpart keep declared28000-element reference centers fixed and scale
  both RIS-link fields by sqrt(n/28000), variances by n/28000 and the shared
  cascade field by n/28000 for all seven source counts. No integer shape is
  invented, no ordinate is fitted, and unreported original center coordinates
  are not claimed recovered. Full7000 optimizer samples remain required.
- ISAC's W-only iteration recomputed unchanged channels. A fixed-channel cache
  hoists identical calculations without changing update arithmetic, objective
  or stops. All six schemes and a full2828-step prefix were independently
  checked against preserved uncached code, including independent MATLAB
  checks. The following v3 cache also hoists fixed-rotation h/g/B and their
  derivatives during RIS RCG; actual Python500-step trajectories, all gradient
  fields and a complete six-scheme case are bitwise identical to preserved v2.
  An observed500-step cap remains a cap, not convergence. Old incomplete banks
  are kept; a fresh byte-identical500-input bank restarts every case under a
  distinct source fingerprint. This is an execution repair, not a different
  optimizer. Independent MATLAB fixed-rotation verification is still required.
- The hotspot generator placed HUs on a radius15m circle. The author's
  Section3.6 and Table3-1 specify HU-to-HU distances10-20m, but several pairs
  in that reconstruction exceed20m. This is a confirmed implementation
  scenario error, **not a paper error**. The completed old statistical18 bank
  and its54 schemes retain their actual numerical convergence evidence, but
  are not accepted as a source-conforming scenario or a strict reproduction.
  A separately declared, unreported radius10m regular-polygon geometry meets
  every pairwise source distance for U2-6; it must be independently verified
  and rerun in fresh full banks. It is not claimed to recover private author
  coordinates. An unfitted comparison to all54 original statistical-EPS
  points finds up to8.07955bps/Hz difference for the old geometry; neither
  those ordinates nor a gain fit is used by the simulator.

- MIS sensing's SINR implementation formed interference by subtracting the
  wanted echo from the sum including it. At high signal levels this loses
  enough digits to reverse a tiny exact augmented-Lagrangian increment.
  Explicitly summing every self-excluded nonnegative interferer, with its
  consistent derivative and signed increment, is algebraically the same
  original model, not a reference-gain or algorithm substitution. The v4
  full6000 literal bank starts afresh; all78 old v3 runs (61 passed,17 failed)
  and their immutable source snapshot remain. Genuine early4000-step caps
  in v4 remain failures even if the final original constrained KKT passes.
  The supplied final R1 explicitly reports the4000 inner budget,30 outers,
  6000 starts and geometric accuracy schedule: a higher inner allowance is
  only an extended diagnostic, never original-budget reproduction.
  The independent MATLAB v4 cold start10 actually completes all30 inner
  solves without a cap or failure. Fresh physical evaluation of that saved
  state and the Python bank's actual start10 verifies both original KKT
  and stop records. Their locally stationary eta values differ by0.2067695;
  this is not claimed as identical optimizer trajectories or global optima.
  The [actual state check](validation/sensing-correctness-v4/full30-start10-independent-state-and-stop-check.json)
  is not a certificate for all6000 starts or the original figure.
- The fresh radius10 statistical bank executed all18 original cases with
  immutable sources and all physical/primal/QT gates passing, but its U6,
  beta0 TwoStage phase solve actually hits the20000 unreported safety cap.
  A separate100000-cap run of the same original RGD reaches the unchanged
  1e-6 gradient stop at39910 steps. That diagnosis cannot retroactively
  certify the old bank. New all-scheme initialization/control experiments
  must retain all starts and use new source-bound full batches.
  Independent MATLAB reaches the same original phase stop at41150 steps,
  residual9.9544906088e-7, under the separately declared100000 cap. It is not
  claimed as a bitwise match to the39910-step Python trajectory. All12 full
  dimension feasible ensemble initializations and three full original NoRIS
  QT chains are independently MATLAB-checked. A fresh uniform all-scheme
  ensemble requires all243 original optimization chains, selects only an
  actually complete feasible design, and evaluates each of the54 selected
  designs on1000 fresh paired draws. A failed required start invalidates its
  point; successful survivors do not erase it. Both full18 language banks
  are distinct actual executions, not re-renderings of one language's data.
- The hotspot source's augmented phase matrix with zero final diagonal and
  nonzero direct/cascade cross block is not generally positive semidefinite:
  its corresponding2x2 principal minor has determinant minus abs(b)^2.
  Nor would restoring the constant and Gram positivity make every unit-circle
  stationary point globally maximal. These are theoretical qualifications,
  not permission to replace the original RGD. The source's physical ESA
  entry-dependent NLoS variance also becomes scalar mu*I in its later
  statistical expression without stating the equal-gain assumption needed
  for that simplification. The original physical covariance and this
  narrower printed convention are distinguished; their mismatch is not
  repaired by fitting a variance to historical reference curves.
- MA's exhaustive-search source really uses D points **per axis** and
  D^(2N) ordered candidate configurations; D10/N4=1e8 is explicit. Its
  numerical text does not uniquely identify the exhaustive objective as
  Eq13/39 statistical design or fixed-draw actual Monte Carlo rate. A
  declared protocol must distinguish those objectives. Row-permutation
  symmetry of a statistical objective cannot be silently applied to a
  fixed per-antenna random-draw objective. No enormous unexecuted grid is
  described as a completed exhaustive figure.
  Figure19 actually extends to per-axis D18, whereas Figure20 ends atD12;
  those original axes cannot be replaced by one shorter common grid.
- Cooperative sweep failures near the original1e-6 gradient stop are
  retained. Independent80-digit evaluation proves that radial floating
  storage drift can make a mathematically improving unit-circle step look
  worse in the old increment evaluation. A stable angle/expm1 evaluation
  of the same exact circle model is under work-only full-chain validation.
  Another work-only broad test detects cancellation in the softmin
  log1p/expm1 form at larger negative increments. These diagnoses do not
  certify the frozen production bank or permit weaker Armijo tests.

## Execution gates that remain mandatory

1. Bind immutable source, configuration, runtime and shared input identities.
2. Execute all original dimensions, starts/Monte Carlo samples, subproblems,
   schemes and panels; never count preparation, timeouts or partial banks as
   complete. Resume only source-identical jobs. An explicitly recorded
   runner-only file-I/O repair may retain the original immutable scientific
   manifest; it cannot accept changed science or parameters.
3. Retain every failed job, physical residual and actual stop reason. Verify
   primal/QT/inner/outer/original-KKT requirements applicable to that algorithm.
4. Run independent MATLAB computations on the same input banks. Nonunique
   conic optimizer vectors need not match bitwise, but objectives and physical
   residuals must pass documented comparisons.
5. Render computed data and compare **all** corresponding original curves,
   grids and panels without fitting gains, copying reference ordinates into a
   simulator, dropping failed points or changing a model to improve overlap.
6. Label a corrected-source result separately when a paper formula is wrong.
   Mathematical correctness and recovery of a possibly erroneous historical
   plot are different requirements, neither inferred from the other.

Architecture drawings are not Monte Carlo tasks. Hardware measurements cannot
be regenerated from a numerical model: original measurement evidence must be
used if available, otherwise that item remains explicitly unavailable rather
than replaced by synthetic data. Final-publisher equivalence is also separate
from correctness of the supplied LaTeX/thesis model.

Machine-readable release status is [status.json](status.json). Complete-figure
plans and independent comparisons are documented in
[FIGURE_REPRODUCTION.md](FIGURE_REPRODUCTION.md). None of the partial evidence
above changes the release's `full_reproduction_passed: false` status.
