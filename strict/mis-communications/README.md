# Strict MIS communications: full scenarios + product-manifold RCG

Paper: [Movable Intelligent Surface (MIS) for Wireless Communications: Architecture, Modeling, Algorithm, and Prototyping](https://doi.org/10.1109/TWC.2025.3621083). Public preprint: [arXiv 2412.19071](https://arxiv.org/abs/2412.19071).

## Source and algorithm contract

The independently implemented model is the final R2 LoS max–min SNR formulation: padded MS2 shifts, ordinary-transpose channel amplitude, relaxed row-simplex scheduling, and negative-softmin continuation. It is not the private Rician sum-throughput/statistical-CSI code located elsewhere.

For each fixed μ the optimization includes **both complex-circle phase blocks and the relaxed scheduling block**. The geometry is the Euclidean/Frobenius geometry explicitly stated in the final source: complex-circle tangent projection, row-mean-subtracted simplex tangent, per-block raw PR directions, tangent projection transport on circles and identity transport on schedules. Retraction is normalized additive circle motion plus Euclidean simplex projection. There is no Fisher multinomial gradient, exact scheduling elimination, phase-only ascent or incumbent-altered solver.

A transparent erratum resolves a source contradiction: (P2) maximizes f = −μ log Σexp(−g/μ), whereas the printed descent directions minimize +f. This implementation minimizes −f and changes all gradients consistently; `objective_convention` can explicitly select literal printed descent for diagnostic comparison. μ is halved exactly as prescribed. The final source gives μ₀=1000 as an example and equally spaced alternative initial μ, but omits their range/count, final μ, RCG cap/tolerance and start count. The default independent implementation records five initial μ values [100,325,550,775,1000], final μ≥0.001, 6000 starts and 4000 inner iterations with 1e−6 gradient threshold **as inferred settings, not manuscript facts**.

## Full figure bank

`figures.json` enumerates every full point rather than shrinking dimensions:

| Figure | Full scenarios | Points |
|---|---|---:|
| 7 | MS1 2×1, MS2 1×1, K=4 + SMS | 1 |
| 8 | MS1 2×2, MS2 1×1, K=4 + SMS | 1 |
| 9 | MS1 sides 6/8/10 × K 8/16/32; every integer MS2 rectangle 1…MS1 | 600 |
| 10 | Total 64/100/144, K 8/16/32, both row/column allocation schemes, complete integer geometries | 108 |
| 11 | MS1 1×64 with MS2 1×36/16/4 and MS1 8×8 with MS2 6×6/4×4/2×2, K=2:2:16 | 48 |

Reference SNR is 0.01, elevation 45°, azimuth spans −60°…60°. Spacing 0.5λ and normal incidence are explicitly inferred because the numerical section does not specify them. Inclusive uniform user sampling resolves the paper's azimuth-symbol typo, but Fig7's “20° separation” conflicts with four users spanning −60°…60°. The exact original user samples are unknown. Figure11's printed U=28 for 1×64/1×36 is inconsistent with the model: the correct count is 29. The code follows the independently checked shape count.

SMS is optimized with the same genuine product-manifold solver, no movable layer and the required comparison aperture (fixed-total SMS only for Fig10). The same-aperture dynamic RIS reference is analytically 0.01 M². Baselines are actual computed values, not copied paper curves.

MATLAB entrypoint:

```matlab
run_mis_communications('unit-matlab.json','component-test');
run_mis_communications('plan.json','plan:fig9');
run_mis_communications('fig7-matlab.json','fig7');
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

Every start is evaluated after optimization. Binary scheduling selects the largest final relaxed entry (smallest index on exact tie). The implementation does not eliminate the simplex variable during optimization. Both relaxed and binary performance are reported; a rounded schedule may reduce performance, so the epigraph value must not be relabeled as binary performance.

Outputs store every start's score and feasibility status, the best feasible final state/trajectory, settings, and outer-iteration means. Feasibility alone does not certify optimization stationarity. Terminated trajectories are held at their final state when computing the mean; no incumbent substitution occurs. Each full point is saved when complete. Per-start checkpoint/resume preserves completed starts, portable RNG state, means and the best result in a sibling `OUTPUT_checkpoints` directory. Checkpoint schema 2 binds the model/settings **and the current Python/MATLAB implementation source digest**. Legacy checkpoints or changed implementation sources are explicitly rejected: preserve them as failed/old evidence and use a new output directory. Each language has its own digest representation and checkpoint names; no cross-language checkpoint interchange is promised. Python replacement is atomic; MATLAB writes a temporary file then moves it into place. Only an interrupted, not-yet-checkpointed start is recomputed. No inside-start checkpoint is provided. Neither a full figure bank nor the original plotted numbers have been certified. `--point n` is explicitly labeled `fullsize_partialfigure`, with the original full point count and selected index.

The component fixture uses shared explicit angles, phases and schedule entries, not an assumption that Python and MATLAB RNGs match. Full independent starts use the same portable Park–Miller generator in both languages. Tests cover all block directional derivatives, unit-modulus/simplex constraints, independent Hermitian quadratic reconstruction, and squared-quadratic (quartic echo) reconstruction. The latter confirms the published narrowband rank-one echo identity, not measured hardware or a full-wave electromagnetic model.

## Status and exclusions

`figure_map.json` specifies every numerical figure's source files, exact axis/metric transformations, panel groups and complete point counts. Fig7/8 full results now include model-evaluated `beampattern_samples`: every MIS position over azimuth−90°:.5°:90° at elevation45°, plus the SMS pattern and user look-direction values. These arrays are generated from the optimized phases, never copied from original figure ordinates. The original EPS marker positions confirm user azimuths−60°,−20°,20°,60°; their40° adjacent spacing conflicts with the Fig7 paragraph's20° wording. The existing inclusive four-user input is retained, with that source discrepancy disclosed. Root-level rendering is a separate step; missing/nonconverged simulation points do not become certified figure results because a renderer exists.

`python test_line_search.py` is a fast independent regression entrypoint for the raw/projected sign counterexamples, empty blocks, closed-simplex KKT stopping, and rejection of legacy/changed-source checkpoints. It never launches a paper Monte Carlo run. The production guard revision is **unit-validated only**; post-revision full-budget convergence/figure validation remains outstanding. New full runs require a new source/runtime-matched output directory; prior attempts cannot be reused across revisions.

The checkpoint identity also binds runtime identifiers: Python/NumPy versions, CPU count and BLAS-thread environment in Python, MATLAB version/architecture in MATLAB. Changing these requires a new output directory. These identifiers do not contain manuscript paths or credentials. Unit `constraint_pass` concerns the phase/simplex domain only; it is not a claim that a sensing epigraph or finite-budget solver has converged.

- Python component tests passed; MATLAB runtime/parity remains a separate root-controlled validation step.
- Full numerical optimizer sweeps have not been run. Having an entrypoint is not evidence that the original figures are reproduced.
- The source-priority contract uses the author's final revised TeX, crosschecked against the public arXiv preprint. Publisher final-PDF comparison is still pending: the DOI search/browser endpoint did not provide its text.
- No private manuscript, reviewer response, measurement data, source path, credential or unrelated solver is included.
