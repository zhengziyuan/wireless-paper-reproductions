# RIS-aided hotspot capacity: author-thesis implementation

DOI: [10.1109/TWC.2023.3309957](https://doi.org/10.1109/TWC.2023.3309957).

New independent MATLAB + Python implementation of the supplied author-thesis model. **Not original author code**, nor yet verified against the17-page final IEEE full text. No private source documents redistributed.

## Scope

The instantaneous branch uses true QT/SOCP active precoding, actual lifted complex SDP with Gaussian randomization, AO with the quadratic coefficient refreshed after the precoder update, and original author Algorithm3-2 manifold RGD then QT/SOCP. The formal RGD direction contains no PR/conjugate term. NoRIS uses the same QT optimization: no ZF or water-filling substitute. Defaults retain N16 feeds/J16 users/U6/K10/M25, finite satellite/ground Rician fading and the same satellite-to-RIS channel shared by all HUs. Physical construction uses the ESA/Bessel squared power pattern and explicit aperture gains.

**Statistical CSI is not implemented.** The thesis has a mathematical inconsistency: Eq3-41b sums only NHU interference while Eq3-46 constructs full-user blocks; Eq3-46 calls norm-squared-to-linear an SOC and uses an imaginary coefficient where a negative self-NLoS quadratic is needed. Imaginary coefficients do not negate norms. General full-rank covariance SINR QoS is not directly convex/SOCP. `--csi statistical` explicitly reports this issue; no instantaneous, pure-LoS or unrelated SCA replacement is used.

`full_config.json` separates source-reported parameters from **tuned/not-reported** coordinates, gains, initialization, seeds, grids,1000 MC realizations/1000 randomizations, caps and thresholds. These are not recovered original figure data. Every requested MC sample is optimized; infeasible samples are not silently removed or targets reduced.

## Run

```text
python run.py --component-test --output outputs/component-python.json --fixture-output outputs/component-fixture.mat
python run.py --scenario-test --output outputs/scenario-python.json
python run.py --chain-test --output outputs/chain-python.json
python run.py --full --sweep base --output outputs/full-base-python.json
python run.py --full --output outputs/full-sweeps-python.json
```

Tests are bounded/full-dimensional, not complete paper reproductions. The full Python backend is explicitly SCS (`eps1e-7/max100000`) after Clarabel failed physical-scenario QT; Clarabel performs minimum-power SOCP initialization. SCS solves the **same original convex problem**, not an algorithm fallback. Full runs have not started; solver runtime may be substantial and needs actual benchmarks.

MATLAB needs external official CVX2.2.2/free SDPT3, not vendored. CVX's documented successive approximation handles log/exp for SDPT3; its experimental warning and true physical feasibility must be recorded. R2025b may require CVX's official `functions/vec_` path.

```matlab
cvx_solver sdpt3
cvx_precision high
strict_hotspot_component_test('outputs/component-fixture.mat','outputs/component-matlab.json');
run_strict_hotspot_satcom('full_config.json','outputs/full-base-matlab.json','base','instantaneous');
run_strict_hotspot_satcom('full_config.json','outputs/full-sweeps-matlab.json');
```

## Numerical details and evidence

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
