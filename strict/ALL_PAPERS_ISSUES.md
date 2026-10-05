# All-paper correction and execution ledger

This is an independent MATLAB/Python reconstruction from the supplied author
sources. It is **not a completed release**, recovered private author code, or a
claim that every historical figure is correct. The [5 October full-population checkpoint](validation/communications-full-population-checkpoint-20261005-v1/README.md) records the closed native Fig7 union and closed Python Fig8 workflow, including their resume provenance and still-pending checks. The source inventory contains
85 captioned figures (73 numerical, 12 illustrative/hardware) and two parameter
tables. Every panel, baseline and full declared sample bank is required. Counts
explicitly reported by a source are preserved; unreported Monte Carlo counts
and random seeds are disclosed reconstruction choices, not recovered author data. Full-size
single cases and component tests are recorded separately from complete figures.

## Verified issues and their disposition

| Paper | Source issue versus implementation/numerical issue | Disposition and evidence |
| --- | --- | --- |
| MIS communications | Figure7's printed 2x1 orientation and Eq3 imply azimuth-even patterns, while the original two MIS curves are not even. The user markers also contradict the text's adjacent spacing. | [COMM_ERRATA.md](mis-communications/COMM_ERRATA.md) proves the conflict. The separately labelled 1x2 orientation preserves two elements, two patterns and four users. The complete actual Python12000-start bank has independent final physical/KKT and230400 recorded-stop checks. All1080 unfitted original vector samples agree within2.572838263652233e-7 linear SNR. The native12000 saved-endpoint union and230400 independent own-mu checks are now closed; single-new-cold execution, unsaved historical inner replay and complete portable native plots are not claimed. See the [5 October checkpoint](validation/communications-full-population-checkpoint-20261005-v1/README.md). |
| MIS communications | Subtracting nearly equal LSE costs can reverse a small decrease; a forced move at an already stationary point was a reconstruction bug. A numerically inactive phase block could block other legitimate descent. | Exact LSE increments, initial KKT checks, and a disclosed per-block KKT accuracy-share safeguard preserve objective, gradients, raw PR, full start counts and global tolerances. Independent Decimal tests and actual MATLAB checks are separate from full sweeps. |
| MIS communications/sensing | Legacy MATLAB and Python aggregate `overall_full_success` can be derived from the selected best start rather than every start's convergence. This is a reconstruction metadata limitation, not a paper-algorithm error. | The public full-figure renderer now checks every original start identifier, stored domain/stop field and required baseline bank before producing output; selected-best-only success, capped/missing slots and RIS aggregate-only flags are rejected. It also binds maximum-score/earliest-exact-tie selection, plotted scalars and declared final tolerances; generic curve scope cannot bypass full MIS coverage. Analytical panels still require full numerical comparator banks; RIS scalar arrays cover every target. The [actual complete Python Fig7 replay](validation/mis-summary-population-gate-v2/README.md) passes all12000 summaries and a fresh render; fifteen corrupted controls are rejected. Summary checks are not independent endpoint/source/RNG or quantized-RIS physical certificates. The [actual recording-v2 preflight](validation/mis-communications-native-fig7-preflight-v2/README.md) retains both fixed starts and all34 own-mu endpoints, with unchanged numerical trajectories and independent source-bound Decimal physical checks passing. The complete12000 native saved-endpoint union and complete-population audit are now closed, with11330+670 execution and11329+671 audit provenance; this is not one new cold campaign. The [portable17-file runtime subset](validation/mis-communications-native-runtime-subset-v3/README.md) is actually reconstructed and rechecked, but is not the complete42-file historical source snapshot or a new native full-bank execution. The earlier row/column checker failure and its false receipts remain unchanged. |
| MIS sensing | Independent block PR does not generally possess product-CG conjugacy; the positive-simplex manifold conflicts with a projection that reaches its boundary. The source's compactness/exact-penalty claims require qualifications. | [SOLVER_ERRATUM.md](mis-sensing/SOLVER_ERRATUM.md) provides counterexamples, a separately named raw-product-PR correction, feasible tangent-cone/active-face handling and an independent original constrained KKT check. The printed branch remains selectable. No global-optimum claim is made. |
| MIS sensing | Algorithm2's indexing/OR stopping differs from the numerical paragraph's early-AND rule. Requiring early stopping after the prescribed 30 iterations was a reconstruction metadata error. | Budget termination, early termination, every inner accuracy and original KKT are distinct fields. Last actually used inner epsilon is 1.2589254117941667e-6. Completing 30 alone is not convergence. |
| MIS sensing | Section V's fixed positive denominator epsilon means the LSE limit as mu tends to zero is the epsilon-regularized ratio, not exactly the unregularized PSLR. | Preserve Eq54's regularization and the source's full60x60 opponent grid/guard. Describe computed values and KKT only as finite-mu/epsilon regularized PSLR; recovering the unregularized limit additionally needs epsilon to vanish and positive denominators. |
| MIS sensing | Physical reference/noise units are underspecified; the old unconditional numerical-bound violation claim was unjustified. Finite-aperture chirps previously used inconsistent phase origins. | [Normalization](mis-sensing/SIGNAL_NORMALIZATION.md) and [closed-form convention](mis-sensing/CLOSED_FORM_CONVENTION.md) keep literal and inferred factor100 contracts separate. Both Fig3 and the remaining stale Fig15 plan wording explicitly withdraw the unconditional impossibility claim: numerical bounds apply only to declared reference-unit/processing assumptions. Public Fig15 map metadata is corrected without changing any live scientific digest or immutable old source/receipt. Shared-origin finite-field identities are checked. Neither a reference fingerprint nor dual agreement proves original Figure2/3 recovery. |
| Rotatable ISAC | The printed BB1 ascent step uses the descent secant sign, producing negative step curvature and clipping. Several numerical controls are not reported. | [Source contract](rotatable-isac/source_contract.json) distinguishes literal BB from the disclosed ascent-sign correction. QT/MM, raw-PR RCG, PGA/BB, all six schemes and 100 channels per point are retained. A larger unpublished W iteration allowance solves the same block; failures under the previous allowance remain preserved. |
| Rotatable ISAC | The title-matched supplied R1 calls raw PR an ascent direction and states stationarity without conditions maintaining sufficiently ascending, gradient-related directions. | The [portable exact source-NMSE counterexample](validation/rotatable-isac-raw-pr-scope-v1/README.md) proves an accepted first original Armijo step followed by a strictly negative raw-PR slope using integer/rational inequalities. All six exact component tests actually pass. This is a mathematical negative control, not a reduced physical simulation, an observed non-ascent historical channel, or a final IEEE-version audit. Existing literal and explicitly disclosed restart branches stay separate. The captured positive-slope iteration4614 is a distinct numerical unit-state problem, not classified as non-ascent by this counterexample. |
| Two-timescale MA | Correlated-ZF products have incompatible N-antenna/M-user dimensions; the row-correlated Gram is not the asserted ordinary Wishart model. | [Exact evaluation](two-timescale-ma/CORRELATED_ZF_EXACT_EVALUATION.md) derives the original-model inverse-Gram expectation using conditional Schur complements and a one-dimensional Laplace integral. Actual full1000-draw MATLAB/Python checks agree. This corrects the bound, not the undefined printed closed form or automatically its historical plots. |
| Two-timescale MA | Generic conic numerical solves failed on valid original coordinate subproblems. | A certified exact two-dimensional convex-subproblem backend preserves original MRT AO/SCA and ZF AO/MM. It verifies each coordinate's box/spacing feasibility and global concavity-gap certificate. It is not a new outer optimizer or a shrunken geometry/NLoS bank. Old failed solves remain preserved. |
| Two-timescale MA | An original-size ZF case actually exhausted the reconstruction's unreported 1500 AO allowance. | A separate same-input cold replay with allowance10000 reached the unchanged5e-5 stop at1599 sweeps. The first1500 objectives,1501 positions and9000 coordinate records are bitwise identical; every accepted position is evaluated using all1000 original draws. The old failure remains a failure. Fresh full200 banks, not relabelled old outputs, are required. |
| Two-timescale MA | The supplied source's energy footnote writes half a wavelength as25mm at12GHz, inconsistent with its own approximately1.28J/42-fold energy figures. | [Exact SI unit audit](validation/two-timescale-ma-energy-units-v1/README.md) binds supplied source SHA/line178. Half a wavelength is12.4913524167mm; the same stated motor model gives1.2757125872J and42.5237529078 times0.03J. Literal25mm instead gives2.5531914894J/85.1063829787. No simulation result is altered; final IEEE-version conformance and a causal explanation of historical-curve discrepancies are not claimed. |
| Cooperative satellite | All183 original eight-scheme computations now finished, but two independent floating gradient comparisons fail. The final aggregate also encountered a reconstruction JSON array-encoding defect. Final-publisher source equivalence is still unverified. | All four stored original implementation gates pass183/183; independent saved-state checks pass181/183, retaining failures56/65. A metadata-only recovery assembles every original durable record and creates only the missing final JSON; it does not reoptimize or relabel failures. The recovered aggregate remains overallfalse. Separate full183 high-precision/all-coordinate, matrix/QT and stored1000-draw checks are running, not certified. No source-paper error is inferred from this reconstruction storage defect or a floating component discrepancy. |
| Hotspot satellite | Full-rank average-SINR QoS is not the printed scalar SOC; the interference index omits transmitted streams; imaginary norm factors cannot implement negative squared norms. Normalized-projector expectations and shared-G fourth moments need correct treatment. | [STATISTICAL_ERRATUM.md](hotspot-satcom/STATISTICAL_ERRATUM.md) derives exact vector-QT QoS auxiliaries within the original QT framework, full finite-Rician moments and normalized-projector integrals. The corrected branch is explicit, not silently described as the printed formula. Original instantaneous/LoS substitutions are forbidden. |
| Hotspot satellite | The reconstruction used per-user path loss where the source specifies a common400m ground amplitude; conic epigraph conditioning and unreported RGD initial step lengths also caused numerical failures. | The shared400m amplitude must be restored without altering position-dependent phases, followed by source-matched reruns. Exact epigraph elimination/positive scaling solve the same original convex block. RGD retains its direction, retraction, Armijo and stopping threshold; numerical controls are disclosed rather than called author data. |
| Hotspot satellite | The supplied thesis uses a Bessel expression as antenna power gain without explicitly squaring it or including maximum gain. The literal expression can be negative. | This is an amplitude-versus-power convention or typographical ambiguity in the supplied source, not an established final IEEE version error. The disclosed simulator uses nonnegative Gmax times the square, as in the primary satellite model's Eq3. See [ESA pattern contract audit](hotspot-satcom/audit_esa_pattern_contract.py), [source erratum](hotspot-satcom/SOURCE_ERRATUM.md) and [primary model](https://link.springer.com/article/10.1186/s13638-020-01749-7). No antenna gain is fitted to a figure. |

**Not an established sensing source error:** under the embedded metric,
orthogonal projection transport gives the same current/old gradient inner
product. Tests verify that identity; transport omission is not blamed for
the observed failure.

## Additional execution repairs and remaining precision limits

### New verified checkpoint, with unfinished scopes kept separate

- The [actual recorded cooperative Python pair](validation/cooperative-recording-v4-python-two-fullcases-v1/README.md)
  supplies what v3 did not save: all eight final phi/W/p states, every fixed
  phase context/returned gradient, every actual QT input/candidate and every
  original1000 channel draw. Independent scalar-coordinate phase gradients,
  matrix physical constraints, QT auxiliaries/surrogate/monotonicity and bitwise
  RNG/sample replay pass for M30(48phases/32QT) and N48(45/24). The public NPZ
  [portable replay actually passes](validation/cooperative-recording-v4-python-two-fullcases-v1/portable-replay-actual-v1/README.md)
  without a solver run. These are double-precision gradient checks, not MP80
  gradient certification, native-v4,183-point performance/figure execution,
  or historical geometry recovery. The [versioned configured input boundary](validation/cooperative-configured-v3-inputs-v1/README.md)
  forwards the exact same frozen-v3 numerical call; its AST/mock checks are
  distinguished from the actual recorded fullcase executions, not fabricated
  as another heavy run.
- The [fixed labelled-MC D3 component](validation/two-timescale-ma-labelled-mc-components-v1/README.md)
  retains all3024 feasible original N4/M3 labelled layouts and all1000 samples
  for geometry0. Exact integer Schur/rational outward-log bounds and all301
  actual prune certificates cover the complete D3 candidate set. The stronger
  all3610 feasible-prefix audit compares each bound to every descendant exact
  leaf upper interval. It is not the complete D3:18/100-geometry Figure19,
  MRT, native parity, practical acceleration or recovery of the source's
  ambiguous historical exhaustive-search objective. Displayed floating rates
  are approximations; the actual rational interval endpoints are stored.
- MIS sensing's arithmetic projection failure and all379 saved old starts are
  preserved in [failed-v4 evidence](validation/sensing-correctness-v4/failed-bank-v4-v1/README.md).
  The [distinct same-cone v5](validation/sensing-same-cone-v5-components-v1/README.md)
  passes actual1025 shared components in each language and the failed377 cold
  full30 original4000 solves plus original KKT in both languages. The default
  scientific package now has exactly the executed25-file source/runtime digest;
  the [promotion record](validation/sensing-same-cone-v5-main-promotion-v1.json)
  distinguishes this from the still-running6000 bank and its genuine caps.
  The orchestration now retains each exception without fabricating a completed
  sample or setting full success from a selected successful incumbent.
- The sensing compactness qualification is narrowed correctly: eta in R does
  not itself defeat fixed-rho/lambda closed-domain ALM sublevel compactness,
  because bounded SINRs and the coercive eta dependence supply it. This is not
  global compactness of the printed open domain or a4000-step raw-PR guarantee.
- The [partial MA dual88 snapshot](validation/two-timescale-ma-partial-dual-v1/README.md)
  checks all5x1000 physical samples and346896 ordered coordinate records at
  fixed kappa6, with no source/imported-solver oracle. It is not all200 or
  kappa100. [Corrected MATLAB source-v2 initial N6/N8 components](validation/two-timescale-ma-corrected-source-v2-position-components/README.md)
  actually use the new native schema and1000 draws. The full300 gate now routes
  that schema, but these two fixed positions are not complete correlated-ZF
  figures or recovery of undefined printed formulas. Existing old source-only
  proofs remain unchanged; runtime evidence is a separately identified supplement.
- The [native cooperative N48 full-eight case](validation/cooperative-native-N48-full8-v3/README.md)
  joins the actual M30 case. Original stops, saved margins and selected CVX/
  backend source intervals pass independent checks. Old v3 did not save final
  matrices or all1000 raw draws: no final-gradient/sample-replay certification
  is inferred, nor a new183-point-bank certificate. The extra raw-dual MP80
  checks still reject all four SDPT3 fixed attempts while passing SeDuMi;
  the original1e-5 pass and this stricter failure are separately reported.
- [Five native before-ONE1000 components](validation/hotspot-native-before-one1000-components-v1/README.md)
  actually select scale1 and execute one original1000 randomization batch each,
  with independent post-hoc MP80 checks of saved SDP/candidate states. No later
  scale was executed. Complete candidate replay, an independent live precision
  gate before production selection, runtime inventory and fullCDF remain
  uncertified; a correct post-hoc component is not a production-policy certificate.
- [Fixed ISAC spectral/control diagnostics](validation/rotatable-isac-correctness-v2/SPECTRAL_CAP_AND_NATURAL_INITIAL_DIAGNOSTICS.md)
  retain every predefined result: BB1/BB2 across two original scenes at10000
  only yield one true phase-gradient stop; three fail. Natural alternating
  initial-step controls at500 fail both cases. MP50/MP80 checks confirm actual
  gradients and accepted increments, not a loosened tolerance or a new optimizer.
  The unreported caps/initial step controls are diagnostics, not recovered
  author settings or complete six-scheme/channel-average figures.

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
  optimizer. Independent MATLAB fixed-rotation and full500-step verification
  actually passed; complete figure-bank convergence is still required.
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

Native cooperative v3 has now actually completed the full M30 physical scene
(J3/U2/N16/K1/M30), all8 original chains and1000 moment draws. All original
implementation gates and actual selected CVX/SDPT3 source/binary interval
bindings pass. This does not erase the old v2 M30 numerical failure. The
M30 independent saved-record audit now also passes every retained stop,
physical margin, QT acceptance and outer residual. The N48 full-scene run
has also actually completed all8 chains with the original gates passing;
its independent record audit remains a distinct requirement.
Final phase/precoder matrices were not retained
by this old recording schema, so no independent final-gradient certificate is
claimed from its boolean flags. The new183-point bank remains unexecuted.

The complete analytical MIS sensing Fig2 has now actually run in both
languages. A third independent finite-array evaluator, importing neither
production solver, checks all nine 91x361 hemisphere gain/SINR maps, all
400/256 phases, all25 possible overlaps, the source nearest-grid schedule
and every target metric under the declared literal inverse-W/single-PRI
normalization. [The actual full-map receipt](validation/sensing-correctness-v4/figure02-all9-full-map-independent-matlab-python-check.json)
passes the fixed1e-10 relative/absolute gate. This is numerical correctness
of the declared analytical convention, **not recovery of the original
unpublished phase/noise convention or historical Fig2**. In particular the
second target's coarse nearest displacement gives2.8050dB; that discrepancy
is not hidden by optimizing a replacement schedule.

ISAC's RCG/PGA500 caps and1e-6/1e-8 controls are reconstructed, not values
assigned in the author manuscript. Its100-channel count and physical
dimensions are reported and remain fixed. Separate10000-cap work replays
preserve all500 original trajectory/evaluation records bitwise but still
fail the true gradient/step criteria. A second complete live scenario also
retains four RIS line-search failures. See [the direct source-control audit](rotatable-isac/SOURCE_BUDGET_AUDIT.md).
Neither larger budgets alone nor exact-cache equivalence establishes a remedy.

Cooperative-satellite v2's72 broad exact-increment components have now passed
independent MATLAB evaluation, but its actual full M30 MATLAB preflight is
**failed**: the unchanged original QT physical/primal/monotonicity gates
reject the backend solution. That full raw failure is retained and is not
replaced by the successful Python preflight. Hotspot CDF samples12 and22
have work-only same-SDP positive-scaling diagnostics with independently
80-digit PSD-dual/feasible-primal gap checks below the unchanged1e-5 gate;
MATLAB and a new complete source-bound CDF chain remain to be checked.

The first independent MATLAB Fig3 AO10000 batch fails before the numerical
optimization: an empty zero-field struct array rejects the first populated
coordinate record. All200 startup-error receipts are preserved;200 output
files do **not** mean200 numerical cases were executed. A separately versioned
MATLAB recording-container repair must be tested on a complete original
input before a fresh full batch. The original Python numerical engine is not
changed by this MATLAB serialization fix. The surrounding execution wrapper
also expanded a cell-valued source identity into a struct array; that invalid
receipt is rejected, and the scalar-wrapper correction does not retrofit
an old successful execution certificate. These are reconstruction/serialization
errors, not errors in the paper's physical model or algorithms.
The separately versioned production MATLAB-full-v2 entry has now actually
completed the same full first N6/M5 input with all five1000-sample schemes,
both original stops and all132/240 coordinate records present. The source
body is unchanged except the recording-container repair; this one-case
check does not retroactively validate the old200 startup receipts. The
outer/inner start bindings now use distinct files. The fresh MATLAB-full-v2
bank has since actually completed200/200 numerical cases with no recorded
failure. Its actual BEFORE/AFTER source, runtime, input and result identities
pass; all five1000-draw scheme populations, original stops, physical domains
and coordinate certificates are checked before rendering the complete Fig3.
Fresh independent no-solver replay now passes all200 cases' full1000-draw
physical metrics at every accepted MRT/ZF design. A second independent audit
also passes all200 cases' original concave coordinate global-gap certificates,
reconstructing the derivatives and complete linearized-spacing polygons
without importing the production coordinate solver. The same-input full
Python bank remains incomplete. Unfitted original Fig3 comparison fails:
maximum rate error is about4.35 bit/s/Hz under the retained v1 indexing
convention; neither of the two predeclared v2 indexing conventions recovers
the reference. The source does not specify the historical convergence-curve
ensemble size or aggregation. A reference lying inside the individual-scene
range does not establish a recovered historical protocol and does not permit
selecting the nearest scene, weights, gain or ordinate.

### Completed runs do not erase source discrepancies

The sensing v4 campaign was found to have actually stopped after376 durable
progress records on the known floating active-threshold projection exception.
It is no longer described as running. Additional completed raw files are
preserved and will be inventoried separately; this is not6000 numerical cases
or a final full-result receipt. The same exact Euclidean-projection numerical
repair has independent component proofs, but a fresh version, cold full30
checks and a complete6000 population are still required. The paper-reported
4000 inner cap remains unchanged, and capped outcomes remain capped.

The original hotspot sample41 TwoStage chain now has actual native MATLAB
and independent saved-state MP80 checks, in addition to the separately
completed Python cold chain. Native phase converges at6819 updates with
gradient3.6573737951e-7; the original QT stop is met after3 updates. Its own
old5000 prefix is bitwise identical, and all16 transmitted streams remain.
An independent physical evaluation of the actual native final state agrees
within1.4210854715e-14. Native/Python iterates are not claimed bitwise equal.
Two earlier source-hash metadata startup failures did not execute the phase
and are not numerical cases; only their source snapshots and observed tool
errors exist, not fabricated machine receipts. See [the native full-chain
supplement](validation/hotspot-cdf41-native-full-TS-v3/README.md). This is not
the complete1000-sample CDF or the other schemes for this realization.

Subsequent prospective cooperative v3 preflights actually complete all10
previous phase-failed physical scenes, all80 original algorithm chains and
all10000 finite-Rician moment draws. An independent audit verifies every
recorded stop/history and replays the full moment population bitwise. The
old154/29 result is not overwritten. This is not a complete183-point bank,
native MATLAB full-scene certificate, or a historical-curve agreement claim.
Final phase matrices were not retained by that runner; their gradients are
not independently reevaluated from saved states. See [the frozen full10
preflight](validation/cooperative-v3-full10-preflight-python-v1/README.md).

Native MATLAB same-MR-QT components now construct and solve both an original
N48 failure input and the actual full-M30 call20 failure input under allfour
fixed SDPT3/SeDuMi high/best controls. The right-side CVX dual annotation on
a CVX-valued RHS caused a construction-only MATLAB colon-dispatch exception;
operation-level probes isolate it, and the documented left-side annotation
constructs the same inequalities. Integer fixture conversion and provider-
scope exception cleanup are interface repairs, not new mathematical updates.
All8 original physical/primal/QT/monotonicity gates pass. All4 SeDuMi results
also pass the stricter MP80 raw-primal/feasible-dual checks. All4 SDPT3 raw
gap checks still fail because the raw objective exceeds the independently
feasible dual upper by only1.43e-11 or6.23e-11; these failures are retained,
not hidden by the tiny positive true-feasible gaps. The original1e-5 gates
and the extra stricter audit gates are explicitly distinct. See [the native
component scope](validation/cooperative-native-mr-components-v6/README.md).

The old complete cooperative-satellite183-point bank actually finishes with
154 valid and29 failed points:10 phase line-search and19 MR QT failures.
Every failure is retained. A mathematical representation of the **same** QT
term factors the exact positive constant out of its square root, improving
numerical cone scaling without changing its variables, subproblem or gates.
All19 actual failed inputs have fresh full-dimension WORK component runs with
the original physical/primal/QT gates and independent80-digit PSD-dual gaps
passing (maximum3.2004347974e-9). See [the frozen19-input evidence](validation/cooperative-mr-precision19-python-v1/README.md).
This is not a new successful183-point bank or native MATLAB19-input proof;
the10 full phase failures and original-reference agreement remain unresolved.

Communication Fig7's actual Python6000-MIS/6000-SMS bank has now completed
with all recorded stops and domains passing. Independent selected-state
physical reconstruction and all1080 original EPS vector samples pass, with
maximum linear-SNR error2.572838263652233e-7 and no ordinate fitting. The
fresh no-solver independent audit now also checks all12000 actual final
states and230400 recorded continuation-stop records. Every final domain,
binary physical score and smoothed KKT passes; maximum final KKT is
9.99994305807773e-7 against the original declared1e-6 gate. Its maximum
independent KKT disagreement is4.2180518252356576e-16. Intermediate
inner-state gradients were not saved and are not claimed replayed.
explicit2x1-to1x2 axis erratum remains necessary and visible. The native full
12000-start saved-endpoint union and all230400 independent own-mu checks have
now closed successfully; its11330+670 execution and11329+671 audit provenance
is explicit, not a claimed new uninterrupted cold campaign. Portable native
plots, unsaved historical inner replay, other figures and publisher approval
are not established.

Communication Fig8's frozen partial snapshot contains14 actual capped
starts. Every one has a fresh same-original-RCG cold replay, changing only
the **unreported**4000 safety cap to100000. All original1e-6 stops and domains
pass, and every old record through the first4000 cap is bitwise identical.
The largest actually used stage contains10840 records. This is all failures
in one partial snapshot, not all12000 inputs or a new complete figure bank;
the old running bank, its failed flags and original parameter provenance
remain unchanged. MIS sensing's4000 cap is explicitly reported and cannot
be extended under this argument.

The separate original-size Fig8 Python workflow has now returned with all
12000 unique starts, source-reported12000 converged/feasible and zero errors.
Its same-source I/O-only resume preserved5543 existing starts; no failed
4000-cap attempt was erased. All declared source bytes and closed metadata
identities match. This workflow closure is not a fresh independent physical
audit, a full native12000 execution or agreement with the original1800 EPS
samples. See the [scoped checkpoint](validation/communications-full-population-checkpoint-20261005-v1/README.md);
those figure-certification gates remain false.

The source R2 does not specify6000 starts per scheme, the seed, initial-mu
grid or final-mu cutoff. These are disclosed reconstruction controls, not a
reported paper budget or a global-optimum guarantee. The actual selected
MIS3018/SMS53 states now have full361-point cuts and all1800 unfitted EPS
samples evaluated separately in Python and MATLAB. All7945 corresponding
SNR scalars agree within the existing5e-14 metric gate, with maximum language
difference9.71445146547012e-17. Original-reference comparison is nevertheless
false: the four MIS path errors reach0.0574853,0.1489260,0.1339543 and0.1172647
absolute linear SNR; SMS reaches1.03322e-6. No normalization, curve fitting,
label permutation or reference-selected winner was used. This diagnoses the
selected-state evaluators, not the full native12000 optimizer population.
The separate Python independent230400-endpoint audit has now genuinely closed
with all12000 original auditor returns/starts passing, no exception and
source/raw/journal/runtime/callable B_A unchanged. It does not upgrade the
failed original-reference comparison. The old native768 component
owner also incorrectly required `isreal(struct)==true`; the corrected strict
recensus passes every768 typed packet and1536 unchanged raw files. This was
OUR metadata-checker error, not an author-paper or solver error.

Hotspot's four actual same-SDP inputs now have all16 native MATLAB scale
attempts and all original1000-candidate/primal checks independently verified
with80-digit PSD/feasible-primal/dual-gap witnesses. The older WORK checker
used the wrong sign for native CVX maximization equality duals and therefore
reported false large gaps. This is **our checker error**, not an author-paper
or solver error. The fixed convention lambda=-CVX-dual/objective-scale is
derived once and checked with actual native scalar max/min/scaling solves,
then applied uniformly to every returned matrix; old false receipts remain.
The separate complete Python cold TwoStage chain for CDF41 reaches its
original gradient stop at6753 (old5000 prefix exact), followed by three QT
steps. Its independent80-digit checks pass, but native complete sample41
and all1000 CDF samples remain separate pending requirements. See [the
actual precision and stopping evidence](validation/hotspot-cdf-numerical-components-v1/NUMERICAL_PRECISION_SCOPE.md).

The new statistical-hotspot Python18-case bank is independently verified for
all243 required starts,717 original stop records and54000 fresh paired rate
samples. This does **not** resolve its original-reference discrepancy:
the actual new run differs by up to8.008012646848087 bit/s/Hz over all54 points.
NoRIS link-budget/source interpretation is being checked independently of
RIS optimization. Real TS declines remain in the output; a channel-criterion
gradient stop is not a final sum-rate optimality certificate. The independently
full MATLAB18 bank exposed an OURS dependency-path failure: all60 actual
starts in its five closed U1..U5/beta0 cases raised MATLAB UndefinedFunction
for double vec. No selected states or stopping records existed in those
cases. The exact owned failed backend was deliberately interrupted; its
genuine parent observes exit3758096408, retained failures and source B_A.
This is not an OOM, paper-model error or solver-convergence result. A distinct
same-version original vec-path restoration is prepared. The actual cold V3
dependency smoke now passes17 of18 exact numeric-record comparisons against
x(:), and genuine CVX class-method/basis dispatch. The original helper uses
reshape(x,numel(x),1): for an empty complex input it retains the complex
storage flag whereas x(:) drops it, with both having shape0x1 and no values.
That retained false is an OURS test-oracle contract mismatch, not an error in
the unchanged original helper. Original SDPT3 callbacks return Solved. The test
host then raises MATLAB:refClearedVar while reading cvx_optval after cvx_end,
retaining its actual stack and source B_A. This is an OURS test-host workspace
failure, not an author-model or SDPT3 convergence failure. Its logical-record
encoder also promoted real(logical) to eight-byte double while claiming
one-byte logical RAW; this is an OURS recording defect, not a solver-input
change. The exact failed owned backend was deliberately interrupted, and its
original parent genuinely observed nonzero exit3758096387; the old false
records and all failure stacks remain. A distinct V4 host preserves both
original unit equations, solver and tolerance, moves the complete unit body
to a nonnested local workspace, adds the exact original reshape-expression
oracle while retaining the old colon false, and records native logical bytes
alongside the explicitly non-native old double projection. All17 source-only
test methods passed. The distinct cold V4 native dependency run has now genuinely
closed with owned exit0, no exception and complete source/runtime B_A. All18
primitive records match the original reshape-expression oracle; the old empty
complex colon false remains visible. Both original real and complex unit models
return Solved through their actual original SDPT3 callbacks. A separate RAW-byte
decoder checks each full solution and objective against its known analytic
solution at the unchanged1e-6 tolerance. The native receipt SHA256 is
`3eeae3ebc490b7905e506a9e790482c77b2493020ddbd5ffaddb51576d68e1f4`;
the actual owned parent is
`9a9e9f7e1c8de5361ea156261393825e678ea6314268434a6bedb47721a6dadb`.
This is a dependency/two-unit certificate, not independent validation of the
whole SDPT3 algorithm, the old failed60 starts or the full18 paper population.

The next distinct V2 full18 cold launch genuinely exits1 before any scientific
case or observation stream is created: MATLAB reports an invalid expression at
bootstrap line61, where our metadata-only multiline struct constructor omitted
the continuation token. The complete failed parent is retained as
`b50cbe1b316edade0841794e2d051ae3371d8535c5685e8e9d32a9fd816ecd3e`.
This is an OURS launcher syntax defect, not a paper/model/convergence error.
A separately named V3 repairs that token and its mechanical generation mirror;
an actual MATLAB parse-only receipt now confirms successful parsing, while its
separate owner terminal remains pending. The distinct full18 original cold run
has actually started, selected the unchanged original CVX/SDPT3 route and entered
the source-bound recording route. This is not complete18 scientific validation.
Historical input recovery and full original-reference agreement remain unresolved.

An independent matrix-sandwich/80-digit PSD check now bounds the **current
declared** U6/beta20 NoRIS ratio-of-expected-powers objective by
5.44384144626725 bit/s/Hz for any precoder, even after removing the NHU QoS
constraints. The original reference point is9.580010498687663. Thus neither
initialization tuning nor a more accurate optimizer on these same current
moments can recover that reference. At least one historical mean, covariance,
beam/user geometry, antenna-gain interpretation or model branch is different.
This is not an upper bound on an unverified final publisher model, on real
E[log] ergodic rates, or on every possible source-consistent historical input.
The positive-sandwich assumptions and the source-noise normalization are
essential; the exact pair-merging algebra is tested independently.

The supplied thesis3-41a also typesets sigma-squared outside the SINR fraction,
while the received-signal model and subsequent3-45/3-46 QT denominator place
the single AWGN inside the denominator. The implementation uses the latter
physical interpretation. This is a qualified author-source/typesetting
conflict, not proof of which branch generated the historical figure or a
verified final-journal erratum.

For MIS sensing, the [R1 finite-budget/domain audit](validation/sensing-correctness-v4/R1_FINITE_BUDGET_AND_COMPACTNESS_AUDIT.md)
documents the printed forced first update, conditional inner accuracy, and
explicit eta/open-simplex counterexamples to the stated full-product
compactness assumption. A fixed-inner closed-simplex bounded sublevel can be
proved instead; this does not automatically prove the outer method or a
4000-step guarantee. The corrected initial-stationary return and boundary
treatment remain explicit implementation errata, not literal source code.

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

## Additional actual checkpoint: native full histories and explicit source units

The [two parameter-table packet](validation/parameter-tables-source-qualified-v1/README.md)
contains actual supplied-author source-read provenance and a fresh portable
replay:36 mapped rows,34 numerical matches and9 negative controls. Numeric
units and instantaneous/statistical branch differences are explicit. The two
external pattern references, final publisher version and realized geometry
are not certified by those scalar matches. The new `--table` route audits
metadata only. Hotspot Fig9 now displays all7 existing source count overrides
and7000 required full samples rather than leaving its base5 shape-pair grid
unqualified; the original numerical implementation is unchanged.

The superseded preview launchers now require explicit opt-in before any
output creation or numerical call. Actual Python guard/negative tests pass;
the native MATLAB guard has a static source-order test, not a new licensed
dispatch receipt. Full original figure commands are shown on the root README.
Historical preview data are neither deleted nor promoted to strict evidence.

The [actual all200 MA initial/input audit](validation/two-timescale-ma-initial-input-contract-v1/README.md)
checks units, LoS normalization, original initial MRT/ZF formulas and100
paired geometries' complete1000 NLoS recipes. No confirmed Fig3/4 gain/noise,
stream-count or same-vector bug was found in that inspected chain. Under the
declared independent uniform angles the exact direction second moments are
diag(1/4,1/2), so swapping2-by3 and3-by2 is not a distribution-equivalent
rotation. Historical Nr/Nc, joint angles, initial positions and convergence
aggregation remain unspecified; neither the seed alone nor this anisotropy
is established as the cause of the reference gap. No optimizer was rerun or
closer orientation selected by this input audit.

The new [native MA Fig. 4 packet](validation/two-timescale-ma-native-figure04-full200-v1/README.md)
independently checks all200 completed source ZF trajectories: 59813 recorded
positions including200 initials, each with1000 original draws (59813000 sample
rates). Independent QR, power, relative ZF residuals, domains, design objectives
and original stops pass. No positions were optimized again. Both fixed initial
index conventions and all100 equally weighted geometries per kappa remain
visible; the maximum unfitted original-curve discrepancy is4.795528605597891
bit/s/Hz. This is correct physical evidence, **not** historical-curve recovery.
Portable frozen verification and a fresh complete first-case replay passed;
a second fresh portable all200 physical run is not claimed.

The [MA energy footnote audit](validation/two-timescale-ma-energy-units-v1/README.md)
binds the supplied R1 source line178. At12GHz, lambda/2 is12.4913524167mm,
not its literal25mm. With the same6 antennas, two axes,8W motor and.94mm/ms
speed, half-lambda movement requires1.2757125872J, about42.5237529078 times
the.03J radio energy. Literal25mm instead gives2.5531914894J and85.1063829787.
The seven exact-arithmetic checks and actual public arithmetic replay pass;
the source is unchanged. This qualified author-source unit error is separate
from the unresolved Fig. 3/4 discrepancy and is not a hardware measurement.

The [native cooperative recording-v4 packet](validation/cooperative-recording-v4-native-two-fullcases-v3/README.md)
contains actual M30(J3/U2/N16) and N48(J1/U2/M25) full cases, each with all8
schemes. Independent checks cover every recorded phase endpoint in its own
fixed W/p/mu context, every QT input/candidate and saved final matrix. Each
native1000-draw RNG replay is bitwise. Actual public-path Python audits pass
both cases without claiming a new MATLAB solve or a new RNG replay. Initial
decoder/configuration metadata failures and an unclassified first portable
process exit remain retained. The complete183-point scan, all performance
trials, all raw QT duals atMP80 and historical curve recovery remain pending.

The [fixed four ISAC cold cap100000 diagnostics](validation/rotatable-isac-correctness-v2/SPECTRAL_INITIAL_FIXED100000_DIAGNOSTIC.md)
retain all full M4/N36/K2/A66 first-RCG-block attempts: three meet the original
1e-6 gradient stop, while BB2/case001 remains capped at100000 with gradient
1.6463678316404304e-4. All available old prefixes and fixed independent
precision witnesses pass. This is **not** a complete-scene/500-bank repair;
the failure is not discarded and these controls are not promoted to production.

## Actual full-scene investigation checkpoint 12

The [source-qualified checkpoint12 findings](validation/full-scene-audit-checkpoint12-v1/README.md)
separate an actual original first-RIS cold non-ascent at iteration19 from the
earlier exact toy counterexample and the different later-block4614 failure.
All249 stored events/83 checks pass, but original stop is false; all80 original
diagnostic alphas fail. Positive raw beta3.19980315315 does not prevent the
negative slope-11.3174949281. Initial/terminal MP physical witnesses are finite
precision, not an all-intermediate-state or interval certificate. The original
W10000 cap remains; explicit direction-erratum/full W cold work is separate.

Cooperative SatCom's same-model positive conditional/Wick evaluation now passes
all91 retained full-context endpoints/all8190 gradient reporting components at
unchanged tolerances. This diagnoses cancellation in our double implementation,
not an author-model error. All3712 saved arrays roundtrip exactly. Native91
fixture readback/MP-stop checks are actual, but native physics, fresh complete183
trajectories and historical curve recovery are not inferred or certified.

MA's prior “original/source stop” fields validate the declared full-sweep global
Eq13/Eq37 interpretation. Supplied R2 refers to local minorants; historical stop
quantity/trajectory remains unidentifiable, even though the5e-5 threshold is
retained. There is no verified gain/noise fix that follows from the figure gap.
An actual all300 saved-evidence inventory finds all five1000-rate families but
no per-draw FPA W/QT/stop/KKT records. Aggregate zero cap counts are insufficient
for those missing checks; new complete original cold recording is separate.
No missing historical state is backfilled or old false flag promoted.

## Actual complete200 saved-dual runnable release

The [complete MA Figure 3 saved-dual package](validation/ma3-complete200-release-v1/README.md)
has now passed the actual fresh single-command route: verify all235 immutable
support/archive pins, unpack all1044 files from all eight parts, independently
audit all200 cases without filtering failures, and render both language-specific
figures. The actual fresh audit, whole-byte interval and command-completion
receipts are published with both plotted curves. Each language's own saved
physical states, original stopping criteria and coordinate certificates pass.

This closes the saved-result package's runnable-release gate, not a new native
optimization, new Monte Carlo ensemble, recovery of unspecified historical
settings, close original-figure agreement, global nonconvex optimality or the
whole six-paper reproduction. The byte-bound support README's old preparation
paragraph is retained as history; the linked release receipt records the later
actual successful execution. Existing failures and interrupted outputs remain.

## MA Figure 5/6 process-loss and recovery boundary

A fresh5 October source/metadata inspection identified the original Python
Figure5 and6 banks as separate9-power-point by100-geometry campaigns, each
requiring900 slots and1000 full NLoS draws per slot (kappa100 and6 respectively).
Their last published progress records are259 and139, not scientific PASS
counts. Both producer execution summaries are missing and no current process
matches the original Python executor or Figure6 storage driver. Completion
and the cause of process loss are therefore unknown; OOM, optimizer failure
or failure of every slot are not inferred. The older native Figure5 progress74
does not establish a current Python task.

Blindly re-running the historical executor would overwrite old progress and
some non-reusable failed result files. A distinct evidence-preserving I/O-only
recovery adapter is now source-reviewed: each old slot must pass the original full
payload/source/runtime reuse gate before it can be reused; every missing,
failed or mismatched slot goes to a NEW attempt target, preserving old bytes.
All900 identities, original1000 draws, algorithms, controls and thresholds
remain required. Figure5's genuine new owned recovery was launched on5 October
with two workers and the original full900 population. It has now genuinely
closed with exit0, no exception and unchanged selected source/input/runtime
bytes. All900 distinct slots pass the original complete reuse gate and have
status reused_converged; none was freshly reoptimized by this recovery. The
earlier259 progress count was stale metadata, not evidence that only259 result
files existed. This closes the original reuse/assembly workflow, not a new
Monte Carlo ensemble, independent physical/dual certification, native900 run
or original-reference agreement. Figure6's separate original900-slot recovery
was actually launched on5 October with one worker; genuine owner/child records
exist and its missing or rejected slots are sent only to new attempt files.
Each retains the complete1000 NLoS draws, original algorithm and stop. It is
running, not a complete900 independent/native/reference certificate.
Figure5 closed supervisor SHA256:
`8978553c1e9690c148c18b61fe3b8fa5226b8eec76911eea2e2126e9e0b61eaf`;
closed900-slot summary SHA256:
`0ed1b2d5e837265c596ce2129307caa1be765eaf9723267ed7e69fa8ac292122`.
Read-only original-route/source/formal-metadata receipt SHA256:
`1846da58155bcdd9d8599baa5887036fdaaa0149e336aec16e3a60c99fd12a7b`.

## Communication array-source conflicts and original-plot compatibility

The [full source audit](mis-communications/COMM_ARRAY_EXPONENT_SOURCE_AUDIT.md)
marks the extra printed2pi, mixed array wave numbers, user-channel L-versus-M
indices, missing imaginary unit in phase exponentials and duplicated SNR
noise factor. These are explicit conflicts in the supplied R2 source, not
an official publisher erratum. A full3-dataset/four-curve/360-sample necessary
space diagnostic at100/160 digits finds original FIG residuals below6.2e-17
for the consistent single2pi model. Thus the original curve cannot be declared
structurally impossible from the current selected state's differing pattern.
The extra2pi frequency-only interpretation has large stable residuals even
with a free constant, under the same declared2x2 geometry. This is not a
rigorous interval infeasibility certificate or a recovery of author phases.
No fitted reproduction or winner reassignment was introduced.

The [stronger complete coupled diagnostic](validation/communications-fig8-coupled-necessary-20261005-v1/README.md)
has also genuinely closed in both frequency lanes, retaining all three datasets,
four curves,360 samples,45 polynomial observations and every100/160-digit
crossprecision component. Per-curve and label-free necessary observations are
numerically compatible in the single-factor model. Some shared-state observations
are nonzero **conditional on** the displayed curves having the source's physical
control-position order. The R2 text explicitly uses row-major numbering, as do
the current implementations; an author column-major convention cannot be inferred
from MATLAB alone. The author generator/legend-to-control mapping and shared
phase state remain unrecovered. This conditional discrepancy is not classified
as an established paper error or rigorous infeasibility, and labels are not
permuted to make the test pass. Complete native optimization and unfitted
reference agreement are still not certified.

The [complete six-path sensing diagnosis](validation/mis-sensing-six-cap-mechanism-20261005-v1/README.md)
has genuinely closed with all180 outer solves,37029 preupdates,36855 steps and
138125 line-search trials. All six4000-step caps fail their own inner epsilon;
later outer solves and all old false states remain. There is no second-search
retry in the complete captured paths, so search-budget exhaustion is not an
established explanation. A diagnostic field misnamed as a projected-gradient
cosine is explicitly an OURS observer-label error, not a paper error. Missing
actual trial EG/candidate and guard operands still prevent a causal cap claim.

The [full-population execution checkpoint](validation/full-population-execution-checkpoint-20261005-v1/README.md)
records the actual original hotspot18, native communication12000 and MA900
independent-math launches. Startup and partial output do not certify complete
convergence, physical correctness or unfitted historical figure agreement.

Machine-readable release status is [status.json](status.json). Complete-figure
plans and independent comparisons are documented in
[FIGURE_REPRODUCTION.md](FIGURE_REPRODUCTION.md). None of the partial evidence
above changes the release's `full_reproduction_passed: false` status.
