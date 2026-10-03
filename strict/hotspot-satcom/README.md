# RIS-aided hotspot capacity: author-thesis implementation

DOI: [10.1109/TWC.2023.3309957](https://doi.org/10.1109/TWC.2023.3309957).

New independent MATLAB + Python implementation of the supplied author-thesis model. **Not original author code**, nor yet verified against the17-page final IEEE full text. No private source documents redistributed.

## Scope

The instantaneous branch uses true QT/SOCP active precoding, actual lifted complex SDP with Gaussian randomization, AO with the quadratic coefficient refreshed after the precoder update, and original author Algorithm3-2 manifold RGD then QT/SOCP. The formal RGD direction contains no PR/conjugate term. NoRIS uses the same QT optimization: no ZF or water-filling substitute. Defaults retain N16 feeds/J16 users/U6/K10/M25, finite satellite/ground Rician fading and the same satellite-to-RIS channel shared by all HUs. Physical construction uses the ESA/Bessel squared power pattern and explicit aperture gains.

**Statistical CSI is not implemented.** The thesis has a mathematical inconsistency: Eq3-41b sums only NHU interference while Eq3-46 constructs full-user blocks; Eq3-46 calls norm-squared-to-linear an SOC and uses an imaginary coefficient where a negative self-NLoS quadratic is needed. Imaginary coefficients do not negate norms. General full-rank covariance SINR QoS is not directly convex/SOCP. `--csi statistical` explicitly reports this issue; no instantaneous, pure-LoS or unrelated SCA replacement is used.

`full_config.json` separates source-reported parameters from **tuned/not-reported** coordinates, gains, initialization, seeds,1000 MC realizations/1000 randomizations, caps and thresholds. HU and Rician grids are now recovered from original author-thesis EPS curve vertices and visually checked axes, not guessed tick grids. Reference ordinates never enter the optimizer. Every requested MC sample is optimized; infeasible samples are not silently removed or targets reduced.

`figure_coverage.json` maps every author-thesis figure3-1 through3-10 to its relative original EPS filename, axes, curves, conflicts and remaining gaps. These are not verified final-publisher figure numbers. Figure3-9's scalar grid is4000:4000:28000 elements per subsurface, but its changing physical row/column shape/spacing is unspecified: the legacy configured element candidate is provisional, not a reproduction of that grid. The per-HU ECDF subcaptions conflict with EPS filenames. Figure3-10 remains blocked; `statistical_formulation_audit.md` gives the exact covariance identity and phase-fixed nonconvexity counterexample.

RandRIS is now explicitly implemented using the physical scenario's shared uniformly random unit-modulus phase and the same original QT precoder design. The complete AO chain records genuine20/100 outer-iteration evaluations and per-HU SINRs for the original five-curve comparisons. An original tolerance stop before a budget is labelled with its actual iteration count; no trace is padded or invented. Phase CPU times are recorded separately for AO and TwoStage.

## Run

```text
python run.py --component-test --output outputs/component-python.json --fixture-output outputs/component-fixture.mat
python run.py --scenario-test --output outputs/scenario-python.json
python run.py --chain-test --output outputs/chain-python.json
python run.py --full-case --output outputs/full-budget-case-python.json
python run.py --full --sweep base --output outputs/full-base-python.json
python run.py --full --output outputs/full-sweeps-python.json
```

Tests are bounded/full-dimensional, not complete paper reproductions. `--full-case` executes one physical sample at the complete configured N16/U6/K10/M25 dimensions and AO/RGD/QT/randomization budgets. It does not change the1000-MC figure configuration and is not an MC estimate. SCS/Clarabel solve the same original convex problems, not alternate algorithms. Full MC sweeps have not run.

A complete-budget SCS attempt failed after149.7s at AO iteration12: the active-QT objective decreased, and earlier primal/QT residuals substantially exceeded validation limits. The genuine history and residuals are retained in `full_budget_failure_receipt.json`; no sample or objective drop was erased. Subsequent exact epigraph conditioning was introduced and tested; full-chain validation remains necessary. A second full-sized attempt failed the SDP PSD check after190.1s. Passing a synthetic component or short chain did not establish full-run success.

The current conditioned Clarabel preset has also been tested on the intact
physical case. Although early subproblems passed independent feasibility checks,
its active-QT solver failed at AO iteration15 after55.6s. The history, actual
auxiliary magnitudes, backend/options and earlier conic residuals are retained in
`full_budget_clarabel_failure_receipt.json`. The failing mathematical input is
saved locally as an independently generated fixture in ignored `outputs/`, not
an author manuscript or original code archive. **No successful complete scene or
near-original-figure reproduction is claimed.** Full dimensions/budgets and
1000-MC figure configurations were not reduced.

MATLAB needs external official CVX2.2.2/free SDPT3, not vendored. CVX's documented successive approximation handles log/exp for SDPT3; its experimental warning and true physical feasibility must be recorded. R2025b may require CVX's official `functions/vec_` path.

```matlab
cvx_solver sdpt3
cvx_precision high
strict_hotspot_component_test('outputs/component-fixture.mat','outputs/component-matlab.json');
run_strict_hotspot_satcom('full_config.json','outputs/full-base-matlab.json','base','instantaneous');
run_strict_hotspot_satcom('full_config.json','outputs/full-sweeps-matlab.json');
```

## Numerical details and evidence

The active QT uses weighted epigraph `lambda_prime=|a|^2*physical_interference`,
with `gamma<=2Re(a*desired)-lambda_prime` and the correspondingly weighted
interference constraint. This removes large-epigraph/tiny-coefficient numerical
conditioning while preserving the feasible set/objective, including a=0. Both
languages use the same identity; it is not a new optimization algorithm.

Variable/noise normalization is algebraically exact. SDR uses a principal Hermitian square root to pair shared-language Gaussian draws; current phase is retained as rounding incumbent, with no rank-one/global-optimum claim. Formal two-stage phase design follows the thesis's explicit RGD in Algorithm3-2/Section3.4.3, using tangent gradient, normalization retraction and Armijo. Eq3-36 maximizes F=f2-f3 but the prose prints -gradF: the formal method minimizes cost=-F, whose descent direction is +gradF. This unique sign-consistency interpretation is recorded, not disguised as literal agreement. `phase_rgd(...,literal_sign=True)` (MATLAB seventh argument true) diagnoses the printed opposite sign only. `phase_rcg` is a separate explicit PR+ diagnostic and is never selected by the formal chain. Initialization is minimum-power SOCP, not ZF.

Other algebraic typo interpretations are explicit: phase-lift L includes the conjugated QT auxiliary and the interference sum covers all J other than the desired stream, both fixed by the original Eq3-18 expression despite omissions/index changes in displayed Eq3-19/21. The phase gradient is differentiated directly from Eq3-36; the expanded imaginary-term sign/sums after Eq3-37 are inconsistent. Eq3-6's noise brace conflicts with the single AWGN in Eq3-4/5 and outside-sum noise in Eq3-11/13; one additive noise variance is used. The component fixture independently checks the lifted versus unlifted phase objective, finite-difference gradient and tangent identity. Source-map labels are author-thesis labels, not verified publisher-final equation labels.

Full-count Python components passed QT identities, physical power/QoS constraints, PSD/diagonal/rounding and analytic-gradient checks. Physical feasible initialization and a bounded original-algorithm chain passed. All tests in `outputs/` keep `full_reproduction_pass:false`. Statistical-CSI completion, full sweeps in both languages, final-model reconciliation and agreement with published curves remain outstanding.

## Termination and valid-figure policy

Each AO, RGD and QT block records its actual final stopping residual, original
stop rule, tuned threshold, iteration count and cap termination. No optimization
update or original stopping test was replaced to add these receipts. Capped RGD
or QT blocks cannot be hidden by another block's convergence. Empty, missing or
nonfinite stopping/numerical records fail closed. Solver-primal normalized
constraint residuals and QT/SDR-bound violations are separate gates; both use
`1e-5` validation tolerances explicitly classified as tuned numerics. Python
retains solver backend/residuals; MATLAB retains CVX status and reported solver
tolerance plus independently evaluated primal and bound residuals.

All required MC outcomes, including failures and capped algorithms, remain in
the output. `raw_unvalidated_means` is diagnostic only; `means` is absent/null
unless every configured sample passes convergence, physical, primal and bound
checks. A failed sample is not silently dropped to improve the mean.
`valid_figure_point` and `overall_implemented_scope_success` concern only the
selected instantaneous author-model scope, not statistical-CSI or final-paper
conformance. `all_configured_sweeps_requested` identifies whether every configured
sweep was requested. The bounded physical chain test intentionally is not a full
convergence experiment. Run `python test_termination.py` for pure receipt tests;
no artificial paper-rate arrays are generated. No full MC sweep was run to add
these gates.

The original AO20/AO100 curves are explicitly reported finite-budget evaluations,
not stationarity claims. Their separate `valid_budget_endpoint` gate requires
physical/primal/QT/SDR validity and records the actual budget/termination, without
setting `algorithm_success=true` for an unconverged fixed-budget method. Full
converged AO/TwoStage/NoRIS/RandRIS success remains gated independently.
