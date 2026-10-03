# Strict MIS sensing: full scenarios + product-manifold RALM/RCG

Paper: [Wireless Sensing with Movable Intelligent Surface](https://doi.org/10.1109/JSTSP.2026.3681476). Public preprint: [arXiv 2509.15627](https://arxiv.org/abs/2509.15627).

## Source and algorithm contract

The final R1 model has L=1, Gₖ=conj(cₖ)cₖᵀ, aₖᵤ=vᵤᴴGₖvᵤ, echo power βₖ²aₖᵤ², and noise σₖ²/P. Every interfering target is retained. Rank-one evaluation is exactly the dense quadratic identity; it accelerates the original model without changing its dimensions or targets.

The solver jointly updates eta, both complex phase blocks and relaxed row-simplex schedules using the paper's Euclidean product geometry, raw per-block PR rule, stated transports, normalized additive circle retractions and Euclidean simplex projection. Each RALM step minimizes −eta + ρ/2 Σ[max(0, λ/ρ+q)]². The outer update uses **old** λ and ρ in iota=max(q,−λ/ρ), clips λ+ρq to [0,1e10], and increases ρ by 1.2 only if max(iota) fails the 0.8 progress test (the first outer iteration retains ρ). It never replaces this test by positive constraint violation.

Original budgets are retained: **6000 starts × 30 outer iterations × 4000 inner RCG iterations**, rho0=1, epsilon0=1e−3 geometrically tightened to 1e−6, minimum outer step1e−10. The source algorithm says stop when the step OR epsilon criterion holds; its numerical paragraph says AND. The default follows the numerical paragraph AND and records this choice. Its step uses the ambient product norm; no numeric intrinsic-distance implementation is supplied by the manuscript.

The final numerical model is 12GHz, λ=0.025m, d=λ/3, L=1, P=30dBm and β²/σ²=−73.88dB. Noise is normalized to σ²=1 and P converted to watts, which preserves all ratios. Public v1 is not silently used for its differing L/noise/penalty/G expressions.

## Full figures and baselines

- Fig2/3/4: MS1 20×20, MS2 16×16, 3×3 target grid; Fig4 keeps the complete 60×60 clutter grid. SINR and LSE-smoothed PSLR share the full RALM budget.
- Fig5/6: best and mean eta / fairness residual over the full 6000-start Fig3 experiment.
- Fig7/8: P=15:3:30dBm, MS1 10×10, MS2 sides6/7/8/9, default 2×2 targets.
- Fig9/10: MS1 sides10…14 and all gaps1/2/3/4.
- Fig11: MS1 sides10…15, MS2 sides8/9/10, RALM.
- Fig12: MS1 sides7…12, MS2 sides5/6/7, RALM (not a closed-form substitute).
- Fig13/14: MS1 20×20, MS2 sides17/16/15 with Ktheta2 and MS2side16 with Ktheta3, Kphi2…7.
- Fig15: same-aperture 10×10 RIS continuous/1bit/2bit versus MIS10×10/8×8, P15:3:30.
- Fig16: same surfaces, full target K1…6.

Sweep samples are recovered from EPS ticks/legends and integer geometry. A rendered original `close1.eps` identifies the exact 3×3 target grid: azimuth phi=0°,45°,90° and elevation theta=30°,50°,70°, numbered elevation-major/azimuth-minor. Equation(3c) explicitly defines these symbols. The Numerical Results sentence swaps their ranges; its earlier literal interpretation is therefore obsolete. All fixed-count sweeps now share inclusive azimuth0°…90° / elevation30°…70° samples (count1 uses45°/50°). Intermediate grid points are uniformly reconstructed from those recovered endpoints; no phase or simulated ordinate is fitted to an original curve. Old-input tests/checkpoints must not be reused.

The closed-form baseline implements the published coverage-guaranteed quadratic coefficient A=π/(λd)max{1/(Ur−1),1/(Uc−1)}, evaluating the full finite padded surfaces. MS2's phase-coordinate origin is offset by the available shift span, mapping physical displacement to index shift minus its maximum. This inferred orientation/origin choice aligns the positive-quadratic steering law with the published ordinary-transpose G convention in the positive-angle sector. The singular Ur=1 or Uc=1 case is reported unavailable, not repaired with an unreported epsilon.

Scheduling for this baseline uses the original continuous steering law with explicit nearest-index rounding (floor(index+0.5)) in that orientation; it does not optimize over every position to improve the heuristic. Fig2/3/4 outputs additionally contain actual full-front-hemisphere beam samples on phi=−180:1:180 and theta=0:1:90. This plotting grid is an explicit independent choice, not a claim about unpublished original sampling. Render the stored gain/SINR samples with `python plot_beampatterns.py fig2-python.json --output plots`; no artificial curves are generated. Compare MATLAB/Python full samples before treating them as cross-language certified.

The RIS optimizer separately tailors a phase pattern for each target using the same interference-aware echo model and full RALM budget; other target echoes remain in its denominator. 1bit/2bit baselines quantize the continuous design to the nearest alphabet (floor(a+0.5), identical in both languages). These baseline solver/quantization choices are explicit inferred settings because the original baseline optimizer was not described.

PSLR retains every other target plus every cell outside the source's explicitly stated rectangular guard: azimuth±22.5°, elevation±10°. The complete60×60 clutter grid covers the recovered angular target region. Exact intermediate samples, equal clutter echo coefficients, epsilon1e−12 and μ10 halved to≥0.001 remain disclosed reconstruction controls. Stored beam panels identify their metric as exact discrete PSLR separately from the LSE-smoothed optimization metric; Fig4 must not be mislabeled SINR. Fig8's RALM reference is Nside6; Fig10's source-worst RALM curve is gap4 according to the original EPS, not gap1 or each point's arbitrary gap. Complete curve/panel/axis mappings are in `figure_map.json`; the repository-level renderer consumes actual results, not original-figure copies.

There is a remaining source normalization inconsistency, independent of optimizer convergence. Equation(9), G=conj(c)cᵀ and unit-modulus c/v give |cᵀv|≤M and SINR≤P(W)*(β²/σ²)*M⁴. The reported Fig3 parameters M400, P30dBm=1W and reference−73.88dB therefore bound every target by1047.7073 (30.2024dB), whereas `opt1.eps`, the final R1 discussion and public preprint annotate32.02dB (1592.2087). An unreported unit/gain/normalization factor or source parameter correction is needed to reconcile those numbers. The code keeps the reported watts/reference coefficient; it does not fit an extra factor to the graph. Publisher/source clarification and numerical figure comparison remain required.

A single SINR point has an upper budget of720 million inner iterations before backtracking; PSLR continuation multiplies that cap by its μ stages. At an assumed1ms/inner iteration this alone is200h/point; at10ms it is2000h/point. These are conditional budget illustrations, **not measured runtime**. Run supervision and a measured benchmark are required before promising a full-bank completion time.

MATLAB entrypoint:

```matlab
run_mis_sensing('unit-matlab.json','component-test');
run_mis_sensing('plan.json','plan:fig3');
run_mis_sensing('fig2-matlab.json','fig2');
run_mis_sensing('fig3-matlab.json','fig3');
```

## Running and validation

The executable is a full-budget independent reimplementation of the manuscript equations, not the original authors' missing simulation archive. The legacy `papers/` demos are unrelated to strict figure validation.

Python (NumPy only):

```text
python run.py --component-test --output unit-python.json
python run.py --figure fig3 --dry-run --output plan.json
python run.py --figure fig3 --output fig3-python.json
```

MATLAB (base MATLAB, no Manopt/CVX toolbox required): add this directory to the path, then use the paper-specific function below. `'component-test'` means a separate small deterministic algebra/solver test; it does not replace any paper scenario. `'plan:figN'` does not optimize. An explicit figure name launches the complete point list and full budgets. Python `--point n` can select one zero-based full-sized point; it does not reduce its starts, iterations, targets or aperture.

Defaults are explicit in `settings.json`, with known manuscript parameters separated from `inferred_or_tuned`. The author authorized documented choices for parameters omitted from the final manuscript. No environment variable, fast mode or hidden reduced default changes the published sensing budget. A user-edited settings file must be identified with `--settings` / the third MATLAB argument; its contents are embedded in the output. Such a result must not be called the default full-budget result if the budget was edited.

The raw per-block Polak–Ribiere coefficients are preserved, without PR+ clipping. Production uses the manuscript's **distinct step size for every active block**: three in communications and four in sensing. Each block independently backtracks against its own actual projected/retracted displacement. Their combined update is then checked against total actual-displacement Armijo; if coupling makes it fail, a common scaling of the already selected block steps is backtracked. This last coupling safeguard and the line-search constants are inferred implementation details, because the manuscript does not specify them. `common_product_armijo` remains a diagnostic option only, not the production implementation.

The source calls the simplex open, but its Euclidean projection can produce boundary zeros. At those points, the row-mean tangent gradient contains a constraint-normal component, and raw-direction Armijo may not describe the projected step. The `documented_non_descent_restart` safeguard therefore tests **both the raw tangent direction and the actual feasible displacement after the original projection/retraction**. It restarts a block as minus its current gradient if either slope is nonnegative, recording `raw_non_descent` and `projected_non_descent` reasons separately. A large circle-retraction chord can look descending even though its infinitesimal direction is uphill; the raw test prevents such a direction from defeating backtracking. Conversely, simplex projection can reverse a raw descending direction, so the projected test is also necessary. Exact zero-gradient blocks, empty phase blocks (no MS2), and exactly zero projected boundary motions are inactive, not false line-search failures. Original PR coefficients, both slopes, block step sizes/backtracks, restart reasons and coupling scale remain recorded. No PR clipping, incumbent substitution, alternative solver, or relaxed feasibility tolerance is used.

The safeguarded stopping residual combines the circle/eta gradients with the simplex gradient mapping `X − project_simplex(X − grad_X)`. Both this `projected_kkt_norm` and the original row-mean `gradient_norm` are reported. This boundary treatment is explicitly an independent numerical safeguard, not printed manuscript text. Select `non_descent_policy: literal_printed` to retain raw-direction Armijo and raw row-mean stopping. Default component fixtures retain the earlier literal/common-alpha regression; explicitly run `python run.py --guarded-component-test --output guarded.json` and the MATLAB wrapper with figure name `component-test-guard` for the **production block-alpha** component regression. Both component modes are small tests, never paper figures. A line-search failure or iteration cap is an exit reason, never a stationarity certificate. Inspect the final residual and stated tolerance before claiming convergence.

Each start reports epigraph feasibility, binary feasibility at that same eta, final/all inner tolerances, continuation completion, outer stopping and failure/cap counts separately. RALM outer convergence retains the selected source AND/OR rule; reaching the 30-iteration cap alone is not satisfying the outer stopping test. The geometric epsilon endpoint is set exactly to epsilon_min on the final prescribed outer iteration, avoiding a floating-point ulp above the mathematical endpoint. `best_feasible` records precisely that, not a convergence certificate. The optimization/full-figure success gates require complete full budgets, checked baselines and the selected best's inner/outer stopping and binary feasibility. `original_figure_reproduction_certified` remains false: neither these gates nor component parity certify unpublished original grids or publisher-PDF figure parity.

For a diagnostic of one original-sized start without secretly reducing budgets, Python supports `--figure fig3 --diagnostic-start 1`; MATLAB supports `full-start:fig3:1`. These retain full per-start solver budgets and explicitly label the output `single_original_full_start_diagnostic_not_full_figure`. They do not count as the 6000-start figure.

`python diagnose_full_start.py --figure fig3 --start 1 --output outputs/fig3-single.json` runs the same original-size solver with an observer that stores compact outer records, raw/projected restart counts, accepted block-step ranges and checkpointed progress. `--settings` permits disclosed line-search-control experiments without editing defaults; the full-budget guard still rejects reduced30/4000/6000 configuration values. The observer does not change directions, PR, ALM updates or stopping thresholds. Its output records loaded source/runtime identities and whether source files changed during execution.

Every start is evaluated after optimization. Binary scheduling selects the largest final relaxed entry (smallest index on exact tie). The implementation does not eliminate the simplex variable during optimization. Both relaxed and binary performance are reported; a rounded schedule may reduce performance, so the epigraph value must not be relabeled as binary performance.

Outputs store every start's score and feasibility status, the best feasible final state/trajectory, settings, and outer-iteration means. Feasibility alone does not certify optimization stationarity. Terminated trajectories are held at their final state when computing the mean; no incumbent substitution occurs. Each full point is saved when complete. Per-start checkpoint/resume preserves completed starts, portable RNG state, means and the best result in a sibling `OUTPUT_checkpoints` directory. Checkpoint schema 2 binds the model/settings **and the current Python/MATLAB implementation source digest**. Legacy checkpoints or changed implementation sources are explicitly rejected: preserve them as failed/old evidence and use a new output directory. Each language has its own digest representation and checkpoint names; no cross-language checkpoint interchange is promised. Python replacement is atomic; MATLAB writes a temporary file then moves it into place. Only an interrupted, not-yet-checkpointed start is recomputed. No inside-start checkpoint is provided. Neither a full figure bank nor the original plotted numbers have been certified. `--point n` is explicitly labeled `fullsize_partialfigure`, with the original full point count and selected index.

The component fixture uses shared explicit angles, phases and schedule entries, not an assumption that Python and MATLAB RNGs match. Full independent starts use the same portable Park–Miller generator in both languages. Tests cover all block directional derivatives, unit-modulus/simplex constraints, independent Hermitian quadratic reconstruction, and squared-quadratic (quartic echo) reconstruction. The latter confirms the published narrowband rank-one echo identity, not measured hardware or a full-wave electromagnetic model.

## Status and exclusions

`python test_line_search.py` is a fast independent regression entrypoint for the raw/projected sign counterexamples, empty blocks, closed-simplex KKT stopping, and rejection of legacy/changed-source checkpoints. It never launches a paper Monte Carlo run. The production guard revision has component validation and actual full-sized single-start diagnostics, but **neither diagnostic passed the convergence gate**; full-bank convergence/figure validation remains outstanding. New full runs require a new source/runtime-matched output directory; prior attempts cannot be reused across revisions.

The checkpoint identity also binds runtime identifiers: Python/NumPy versions, CPU count and BLAS-thread environment in Python, MATLAB version/architecture in MATLAB. Changing these requires a new output directory. These identifiers do not contain manuscript paths or credentials. Unit `constraint_pass` concerns the phase/simplex domain only; it is not a claim that a sensing epigraph or finite-budget solver has converged.

- Python component tests passed; MATLAB runtime/parity remains a separate root-controlled validation step.
- Full numerical optimizer sweeps have not been run. Having an entrypoint is not evidence that the original figures are reproduced.
- The v3 raw/projected-sign safeguard actually ran a complete **single-start**30/4000-budget diagnostic on the earlier, subsequently contradicted angle input:721.29s,96916 total inner iterations,12 inner tolerance exits,17 caps and one eta-block line-search failure. Final maxq4.90076e−6 exceeds1e−6, projected/KKT6.80489e−5 exceeds final-used1.25893e−6, and outerstep0.261147 exceeds1e−10. Its failed record is preserved, not relabeled passed.
- A separate **single-start** diagnostic on the recovered original figure-marker inputs completed all30 outer iterations in418.97s, with20274 actual inner iterations and the unchanged4000-per-outer upper budget. The final relaxed/binary minimum SINR is49.5352459009 (about16.95dB), and maxq7.28129e−8 meets the1e−6 feasibility tolerance. However, projected/KKT2.60043e−5 exceeds the final-used1.25893e−6 tolerance. There were16 inner-tolerance exits,2 caps and12 line-search failures (theta6, phi4, coupling2); the final phi-block failure accepted no step. The outer numerical AND condition is true only because the final step is zero and epsilon has reached its endpoint: this does **not** overcome the failed inner stationarity gate. `convergence_verified` is false. The compact local receipt is `outputs/fig3-recovered-grid-full-start.json`; a public trimmed receipt in `diagnostics/fig3-recovered-grid-full-start-receipt.json` retains timings, all30 outer numerical records, stop norms and source-change disclosure without full phase/schedule state or private source paths. Neither is a6000-start figure. The start/end source-change flag correctly records an evidence-only edit to `source_map.json` during execution; optimizer, runner and numerical settings remained unchanged, with loaded-source identities retained in the receipt. No completed start from an earlier source/runtime configuration is reused.
- The source-priority contract uses the author's final revised TeX, crosschecked against the public arXiv preprint. Publisher final-PDF comparison is still pending: the DOI search/browser endpoint did not provide its text.
- No private manuscript, reviewer response, measurement data, source path, credential or unrelated solver is included.
