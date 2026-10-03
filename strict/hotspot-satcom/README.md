# RIS-aided hotspot capacity: original-model MATLAB and Python

DOI: [10.1109/TWC.2023.3309957](https://doi.org/10.1109/TWC.2023.3309957).

Independent implementations of the supplied author model, not original author
code. The final 17-page IEEE full text and historical original-curve agreement
remain unverified. Private manuscripts, author artwork and reference ordinates
are not redistributed or presented as simulation output.

## Model and explicit errata

The instantaneous branch uses original complex QT active precoding, lifted
complex SDP/Gaussian randomization, AO and original Algorithm 3-2 RGD then QT.
NoRIS and RandRIS precoders are optimized by the same QT, not ZF or
water-filling. Defaults retain N16/J16/U6/K10/M25, finite satellite/ground
Rician fading and one satellite-to-RIS channel shared by all HUs.

Statistical CSI is implemented as the explicitly labelled
`corrected_QT_erratum`, **not** the original printed invalid scalar SOC.
The full-rank moment SINR of the early ESA-weighted physical signal model and
original QT framework are retained. Later printed scalar-mu/isotropic moments
require an unstated equal-feed-gain simplification and are not silently
equated to this physical branch. The original LoS mean/array coordinates are
also unrecovered; fixing HU distances is not a claim that every source-model
setting is verified.
The exact vector-QT identity is also applied to NHU QoS, preserving original
average-SINR feasibility at each step. Literal printed-SOC calls fail with an
explanation; no instantaneous, LoS or unrelated optimizer is substituted.
[STATISTICAL_ERRATUM.md](STATISTICAL_ERRATUM.md) supplies the identity,
feasibility proof, exact normalized NHU projectors, shared-G fourth moments,
noise normalization and source-index/sign corrections. It also marks the
displayed unsquared ESA power-pattern convention: the unchanged generators
use a nonnegative squared-amplitude gain with explicit peak gain, not literal
unsquared equation3-3. Publisher wording and historical convention remain
unverified; original LoS phases are not inferred from a matching plot.

All RIS-to-HU large-scale attenuation uses the source's common 400m distance.
Actual user offsets remain in propagation phases, not an unintended
distance-dependent power change. Satellite fields already include thermal
noise normalization; the effective noise variance is one, not renormalized
twice. Statistical ground Rician factor is 20dB and its NHU target is -3dB,
distinct from the instantaneous scenario's 0dB ground factor and 3dB target.

## Preferred execution

Run from this directory with NumPy, SciPy, CVXPY and Clarabel/SCS installed.
Set one BLAS thread when sharing compute. Complete figure runs can be long.

```text
python run_instantaneous_geometry.py --full-case --output outputs/instantaneous-case.json
python run_instantaneous_geometry.py --full --sweep cdf_kS20 --checkpoint-dir outputs/instantaneous-source-geometry-bank --output outputs/instantaneous-cdf20.json
python run_statistical_validated.py --full-case --case-u 3 --case-beta 20 --checkpoint-dir outputs/statistical-validated-case --output outputs/statistical-case.json
python run_statistical_validated.py --full --checkpoint-dir outputs/statistical-validated-bank --output outputs/statistical-all18.json
```

`instantaneous_geometry_config.json` is the instantaneous configuration;
`statistical_validated_config.json` is the uniform-feasible-ensemble statistical
configuration. `run_statistical_geometry.py` and its20000-cap single-start
configuration remain separate selectable diagnostics, including their retained
cap failure. Configurations separate reported source values from unreported/tuned
geometry, seed, MC count, solver controls and safety caps. Statistical full
runs retain every U1..6 × satellite-Rician0/10/20 point and 1000 independent
finite-Rician MC channels for each optimized design.

The source requires every HU pair distance to remain in10..20m. The preferred
isolated geometry modules declare radius10m, independently check all pairs,
and leave all other original channel/algorithm terms unchanged. Old radius15
geometry violated this requirement. Its actual receipts are preserved as
historical diagnostics, not strict original-scenario certificates. See
[GEOMETRY_CONTRACT.md](GEOMETRY_CONTRACT.md). Historical coordinates have not
been recovered; the new geometry is not fitted to reference ordinates.

`--full-case` is one complete original-sized optimization, with full iteration
budgets and all 1000 original SDR rounding draws when applicable. It is not a
1000-realization instantaneous figure bank. Statistical MC validates the fixed
statistical design on fresh channels; it separately reports the source's
ratio-of-expected-powers rate approximation and the actual MC E[log] estimate.

MATLAB requires external official CVX and SDPT3, not vendored here. Use
`maxNumCompThreads(1)`, `cvx_solver sdpt3` and `cvx_precision high`.
CVX's true status/physical residuals are retained; its log/exp successive
approximation warning is not hidden. R2025b may require official CVX's
`functions/vec_` folder on the path.

```matlab
run_strict_hotspot_instantaneous_geometry('instantaneous_geometry_config.json','outputs/instantaneous-case-matlab.json','full-case','instantaneous');
run_strict_hotspot_instantaneous_geometry('instantaneous_geometry_config.json','outputs/instantaneous-cdf20-matlab.json','cdf_kS20','instantaneous');
run_strict_hotspot_statistical_validated('statistical_validated_config.json','outputs/statistical-case-matlab.json','full-case');
run_strict_hotspot_statistical_validated('statistical_validated_config.json','outputs/statistical-all18-matlab.json','full');
```

## Numerical controls, not substitute algorithms

Exact epigraph elimination, positive log-argument scaling and real/imaginary
norm realification condition the original convex problem, including zero QT
auxiliaries. Backend retries solve only that same mathematical problem.
The instantaneous SDP guard checks the best of **all original Gaussian
candidates** against the relaxation bound. If numerical inaccuracy invalidates
that bound, it resolves the identical SDP with identical auxiliaries,
incumbent and draws under stricter numerical controls. Neither candidate count
nor the 1e-5 primal/bound gates are reduced or relaxed.

The statistical spectral branch preserves original RGD direction, circle
retraction, Armijo1e-4 and gradient1e-6. Positive BB1/BB2 values choose only the
step seed. Exact polynomial/ratio/log1p increments prevent false declines
caused by subtracting nearly equal large objectives. The unreported safety
cap is20000 in the historical spectral/single-start branches. The corrected-
distance full18 bank retained U6/beta0 two-stage failure at that cap. An
independent identical-stage run genuinely reached1e-6 at39910, so the new
validated branch declares100000 as an unreported safety cap only. A cap is
never convergence; no original stop threshold is loosened. Previous controls
remain diagnostics with their actual identities and failed stops preserved.

All NoRIS/two-stage/AO schemes now use a disclosed common0..U feasible-start
ensemble. Every original QT/RGD chain is run to its real stops. The best
completed physically feasible original objective selects the fixed design,
but any prescribed start that fails, caps or is missing makes the ensemble
fail. Complete states, histories and numerical gates for every start are
saved; successful-start selection is never an ensemble certificate. Exactly
1000 fresh paired channels evaluate each selected design, with no initializer
average or failure-survivor mean. No reference ordinate controls this policy.

RandRIS uses the scenario's sampled unit-modulus phases and QT precoder.
AO20/AO100 are actual fixed-budget evaluations, not stationarity claims.
An earlier original stop is labelled with its actual count; no trace is padded.
Phase and whole-scheme CPU times are measured separately.

## Actual evidence and boundaries

Post-400m complete instantaneous original QT/SDP/RGD/NoRIS/RandRIS optimization
passed physical, convergence, primal and relaxation-bound gates after the
same-SDP numerical guard. The statistical spectral U4/beta20 complete case
also passed all four gates with 1000 independent MC channels. The older
source-bound statistical 18-point 5000-cap run completed but retained two
genuine capped scenarios. It is not a successful figure certificate.

The old spectral18 run actually passed its internal four gates, but its
radius15 geometry violates the source10..20m requirement and its original
54-ordinate curve disagreement is large. It is not strict figure reproduction.
After the isolated source-distance correction, a statistical U4/beta20 case
passed all four gates and1000 MC in39.27s, and a full instantaneous U6 case
passed all four gates in144.20s. Fresh source-compliant18-point and1000-MC
banks were started without reusing old points. The new single-start statistical
18-point bank actually finished1177.66s: physical/primal/QT checks passed,
but U6/beta0 two-stage hit20000 iterations and the full convergence gate is
false. Its failed stop is not overwritten by the separate39910 phase diagnosis.
The new uniform-ensemble/cap100000 branch is a distinct fresh execution and
never resumes a single-start case as an ensemble certificate. Partial progress
and complete-case tests are not all-figure completion. Read actual receipts.
Historical SCS/Clarabel/SDP and 5000-cap failures are preserved, not upgraded
to success for newer source code.

`figure_coverage.json` maps supplied author figures3-1..3-10, not verified
final-publisher numbering. HU/Rician grids follow original EPS abscissae.
For figure3-9 the source says fixed M and element count changes only maximum
aperture gain: a count-only adapter must freeze declared subpanel centers and
scale both field amplitudes, not move their propagation phases. Historical
center geometry is not thereby recovered. Reference ordinates never enter
the optimizer.

## Independent tests and fail-closed receipts

```text
python test_statistical_contract.py
python test_rgd_increments.py
python verify_statistical.py
python verify_rgd_controls.py
python verify_spectral_controls.py
python verify_geometry.py
python test_statistical_ensemble.py
python verify_ensemble.py
python audit_single_hu_guarantee.py
python audit_covariance_contract.py
python test_termination.py
```

MATLAB counterparts are `strict_hotspot_statistical_test`,
`strict_hotspot_rgd_controls_test` and `strict_hotspot_spectral_test`.
The last test compares a deliberately bounded 12-step synthetic trajectory;
its original capped stop flags remain false even when component parity passes.
Components are never copied into a paper-performance bank.
The independent new geometry counterpart is `strict_hotspot_geometry_test`.
`strict_hotspot_ensemble_test` recomputes all full-dimension initializers and
the common SHA256 phase schedule from a shared numeric fixture, and independently
rejects missing/capped/bound-violating start sets. It is not a full optimizer
run or curve certificate. The standalone mathematical counterexample audit
refutes the source's generic PSD/global-optimality claim, not the entire RGD
method; production retains original RGD with actual stationarity evidence.

Actual runtime sources and immutable configuration are hashed before/after
runs. Checkpoints bind source, configuration and RNG state. Every required
outcome, including failures/caps, remains present. Diagnostic
`raw_unvalidated_means` is separate from certified `means`; no survivor-only
average is exported. All selected samples/points must pass physical,
convergence, solver-primal and QT/SDR-bound gates before rendering.
`full_reproduction_pass` remains false until final-source and original-curve
agreement are separately established.
