# Cooperative multi-satellite / multi-RIS: original-model MATLAB and Python

DOI: [10.1109/JSAC.2024.3460068](https://doi.org/10.1109/JSAC.2024.3460068).

Independent implementations of the accessible author manuscript and supplied
author model, not original author code. The accessible author PDF has 16 pages
versus 18 in the journal publication; final-publisher equivalence and historical
curve agreement remain unverified. No private manuscript/artwork is uploaded.

## Original scope and explicit errata

All eight AP-AO/AP-NoRIS/MR-S-NoRIS/MR-S-PA/MR-S-TS/MR-TTS-NoRIS/MR-TTS-PA/
MR-TTS-TS chains are implemented. AP uses the actual complex QT precoder and
independent per-user RIS manifold design. MR allocates every satellite/user
power independently, never fixed shares or scalar bisection. Two-stage design
retains original exponential smoothing and the **full squared interference
residual** penalty, including negative residuals, then original QT.

Finite-Rician cascaded NLoS products and their non-Gaussian fourth moments are
retained. The original non-coherent satellite-stream/SIC bound is used, not a
coherent-transmission replacement. Ground fading for one user is shared across
satellites; independent users retain independent RIS channels. Gradients are
analytical and independently checked, not finite-difference optimization.

[SOURCE_ERRATUM.md](SOURCE_ERRATUM.md) makes author-equation corrections explicit.
Statistical MR's physical power is `sum p||E h||²`, as in original Eq4-28c;
the later printed self-cross-moment coefficient is not transmit power.
The exact original channel supplies squared GT amplitude coefficients,
additive GEO interference with the correct complex cross term, and full
conditional-Gaussian fourth moments. This is the same original model/QT
framework with declared errata, not literal reproduction of inconsistent
printed equations or a claim about errors in the unavailable final PDF.

Full defaults retain J3/U2/N16/M25/K1 and source altitudes/Rician values.
Fair comparisons use N48/P150W for one satellite versus 3×16 antennas and
3×50W, including 1.25/2.5deg offsets. GT radiation uses the actual ITU S.1428-1
piecewise pattern referenced by the S.1503 FSS prescription; no generic
sidelobe-envelope substitute is used.

## Preferred execution

Run from this directory with NumPy, SciPy, CVXPY and Clarabel/SCS available.
Set one BLAS thread when sharing compute.

```text
python run_cooperative_guarded.py --full --sweep base --output outputs/full-base-guarded.json
python run_cooperative_guarded.py --full --sweep power_kL20 --checkpoint-dir outputs/guarded-bank --output outputs/power20-guarded.json
python run_cooperative_guarded.py --full --checkpoint-dir outputs/guarded-bank --output outputs/all-guarded-figures.json
```

The preferred entry reads same-directory `spectral_config.json`.
It supports `--sweep`, `--checkpoint-dir` and required `--output`; it has no
`--config` option or silent reduced mode. The explicit `--case-power` option
requires `--sweep base` and diagnoses one physical power without modifying the
original full grids. Old `run.py`/`full_config.json` and the unguarded spectral
entry remain available as diagnostics. Configurations disclose reported and
unreported values.
Original author-EPS abscissae give half-octave power grids, linear INR0.01:0.01:
0.12, M5:5:45 and ground Rician-12:3:30dB. Reference ordinates are never used
to fit optimization results. The fixed statistical geometry is optimized
analytically; 1000 independent finite-Rician draws validate its moments rather
than repeat identical deterministic optimizations 1000 times.

MATLAB needs external official CVX and SDPT3, not vendored. Use
`maxNumCompThreads(1)`, `cvx_solver sdpt3`, `cvx_precision high`.
R2025b may require the official CVX `functions/vec_` path.

```matlab
run_strict_cooperative_guarded('spectral_config.json','outputs/base-guarded-matlab.json','base');
run_strict_cooperative_guarded('spectral_config.json','outputs/power20-guarded-matlab.json','power_kL20');
run_strict_cooperative_guarded('spectral_config.json','outputs/all-guarded-matlab.json');
```

## Same algorithms, numerical controls

[NUMERICAL_CONTROLS.md](NUMERICAL_CONTROLS.md) derives exact all-coordinate
gradient contractions and original polynomial/ratio/logsumexp increments.
The scalar-coordinate gradient oracle is retained independently. These
identities prevent raw subtraction from manufacturing a false decline near
the original stopping threshold.

The spectral branch keeps the original RGD direction, normalized circle
retraction, Armijo1e-4, gradient1e-6, full residual penalty and all constraints.
Positive BB1/BB2 values choose only step size before the original halving
search. The original author source does not report the numerical safety cap;
the preferred cap is 20000 after preserved actual 5000-cap failures. It is
never accepted as convergence. A zero step for an already-stationary AP row
is exactly the identity. An earlier implementation's ten-times-gradient
exception was removed in both languages; there is no tolerance relaxation.

Exact diagonal variable normalization improves conic conditioning without
restricting the independent powers. Changed-phase MR warm starts are scaled
once uniformly only to restore feasibility; the QT optimization remains
unrestricted. Nonunique solver outputs need not be identical beamformers.

The preferred guard re-solves the **same** QT block with the **same** incumbent,
auxiliaries and constraints if a numerical backend fails or the independent
primal/QT/monotonicity checks fail. Only solver precision, regularization and
numerical iteration controls change. The original `1e-5` primal and QT gates
are not relaxed. Every attempted status and rejection is retained; a solver's
reported success alone is insufficient. The MATLAB guard analogously changes
CVX precision for the same input subproblem and restores the caller's setting.

## Actual evidence and limitations

The source-bound full-dimensional spectral base case actually completed all
eight original chains, all four physical/convergence/primal/QT gates and
1000 independent moment draws in 59.32s. That is one complete scenario, not
all original figures. The earlier 5000-cap exact-increment base run retained
MR-TTS-TS failures after 658.71s. Neither old failures nor component tests are
promoted to successful new-source results.

The unguarded full bank subsequently exposed same-QT numerical failures at
power 2.828427/11.313708W and a bound-check failure at 8W. Those actual receipts
are preserved. Independently checking the generated failed-input fixtures
confirmed the same original QT solves at stricter numerical settings. The
new guarded complete 8W scenario actually passed all eight schemes, all four
gates, source-unchanged checks and 1000 independent moment draws in 84.82s.
This is a full scenario, not a completed figure bank or publisher-curve match.

The fresh full sweep set, including fair single-satellite baselines, is
running with source/configuration-bound per-point checkpoints. Read actual
receipts for current completion; no complete-sweep certificate follows from
a partial bank. Both-language full-run tests and agreement with original
publisher curves are separately required.

`figure_coverage.json` maps supplied author figures4-1..4-11, not verified
final-publisher numbering. The interference EPS label prints W but marks
the source's normalized ITU line 10^(-12.2/10)=0.06026; the scenario uses
linear interference-to-noise ratio, not 0.06 physical watts at -94dBm.
Unreported historical coordinates/gains/seed/solver settings are disclosed
tuning, not claimed recovered author settings.

## Independent tests and result gates

```text
python test_original_mr_contract.py
python verify_phase_derivatives.py
python verify_increments.py
python test_qt_guard_contract.py
python test_termination.py
```

MATLAB counterparts are `strict_satcom_phase_derivative_test` and
`strict_satcom_increment_test`, using independently generated shared fixtures.
`strict_satcom_qt_guard_test` independently solves an explicitly identified
generated same-QT failure fixture. Mock contract tests are software checks,
not channel-performance evidence.
Component checks do not create paper-performance arrays.

Each QT/AO/RGD/smoothing block records its real stop rule, residual, threshold
and cap. A stopped outer loop does not mask a capped inner phase block.
MR-PA also checks its AP phase source. Primal normalized constraints and QT
bounds have separate unchanged 1e-5 gates. All scenario outcomes are retained;
one failed/capped/numerically-unvalidated point invalidates its selected
figure. Runtime source/config hashes bind actual execution and prevent stale
checkpoint reuse. `full_reproduction_pass` remains false until final-source
and historical-curve conformance are established.
