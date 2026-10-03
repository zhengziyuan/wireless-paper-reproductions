# Full original figures: execution and comparison

**Work in progress, not a completed all-paper figure reproduction release.**
No published figure has passed all source, parameter, execution and original
reference-agreement gates. The owner requires full original models, scenes,
baselines and dimensions in MATLAB/Python; no replacement curves or reduced
production banks are permitted.

## Original figure inventory

`figure-catalog/` inventories 85 captioned figures and two captioned parameter
tables in the six supplied author sources. 73 figures require numerical
experiments; 12 are architecture/framework/hardware illustrations. Each
multi-panel figure is counted once, but every panel and baseline still needs
its complete output. Satellite numbering follows the supplied thesis chapters,
not a verified final publisher PDF. Tables are inventoried, not certified merely
because a configuration file exists.

Each package's `figure_map.json`, `figure_catalog.json` or `figure_coverage.json`
maps original artifacts, ordinate fields/units, grids, curve selections and
source conflicts. Inventories hash the source and figure assets without
redistributing private manuscripts, original EPS or hardware photographs.

## One full-budget entry point

From the repository root, install `strict/requirements.txt` and inspect a plan:

```sh
python strict/reproduce.py --paper mis-sensing --figure 2
```

The default is a plan, not a simulation or a hidden fast demonstration. To run
and plot the full 20x20/16x16, nine-target closed-form model with all 361x91
angle samples per target:

```sh
python strict/reproduce.py --paper mis-sensing --figure 2 --language python --execute
python strict/reproduce.py --paper mis-sensing --figure 2 --language matlab --execute
```

MATLAB must be installed/discoverable or specified with `--matlab`. Convex
packages require independently installed/configured CVX, not bundled binaries.
The local R2025b/CVX2.2.2 check also needed CVX's official `functions/vec_`
support directory on the path, a runtime compatibility step rather than an
algorithm change.

These commands write numerical JSON, PNG/SVG and a render receipt. Full-grid
MATLAB/Python parity and original-figure agreement are separate checks. A
phase-convention or normalization revision needs new source-matched receipts;
historical paired outputs are not evidence for the revised implementation.
**The corrected closed-form design is not yet a recovery of the original
finite-aperture Figure2.** Titles explicitly state that original agreement is
unverified. Display cropping/color limits change neither stored samples nor
physical scenarios.

The corrected same-reference design uses both conjugated chirps (MS1−A,
MS2+A) with the Eq11 positive array exponent. It is exactly field-conjugate
to Section VI's negative exponent / +A,−A convention, even with every finite
one-padded element retained. The previous extra MS2-only origin offset is
superseded, not silently reused. Positions follow the original positive
displacement law with nearest-index recovery, never a substituted SINR-maximising
placement. The full nine-target positions are `[10,6,2,15,12,3,20,18,4]`
(zero-based). `mis-sensing/CLOSED_FORM_CONVENTION.md` gives the proof.

Other plans retain full implemented banks. Some complete-figure adapters or
renderers remain unavailable and fail explicitly, not with substitute plots.
MIS optimized figures retain 6000 starts, sensing30 outer steps and4000 inner
caps. ISAC retains100 channels per point. MA retains the full configured
100-geometry/1000-NLoS banks and actual exhaustive searches. Banks/searches can
be extremely expensive; no count is silently reduced. Plans, input banks or
one successful realization are not complete Monte Carlo figures.

Sensing Figs5/6 must reuse the exact Fig3 bank, not new starts or a different
best start per iteration. Its aggregate renderer is not ready. Undefined
matrix products and inconsistent statistical-CSI formulations also fail
explicitly rather than being replaced by other channel models/optimizers.

## Original references stay independent

`figure-reference/mis-sensing-fig15.json` is extracted from the author's EPS
straight-line vectors with visually verified axes. It is **original plot
reference, NOT simulation**, with precision limited by EPS decimal coordinates.
The parser rejects unsupported exporters, unverified axes, mixed coordinate
frames, unmatched labels and unsupported paths. Reference ordinates never
enter optimization, simulation inputs or fitted gains.

For implemented sensing multi-curve schemas, `render_figure.py` writes computed
`curves.json`. Independently compare it with the reference:

```sh
python strict/figure_validation.py --simulation PATH_TO_SIMULATED_CURVES.json --reference strict/figure-reference/mis-sensing-fig15.json --output comparison.json
```

The report checks all labels and all same-grid samples, and gives maximum
absolute ordinate error/RMSE without interpolation, fitting, rescaling or
discarding failed points. A numerical acceptance flag requires an explicitly
supplied `--max-abs-error` criterion; no arbitrary tolerance is silently called
the author's standard. Numerical agreement does not certify model correctness.

## Explicit reference units and the recovered numerical fingerprint

In supplied sensing R1 Eqs9/11, steering entries and entries of
`v = bar(theta) .* phi` have unit modulus and `G = conj(c) * transpose(c)`.
Therefore, with nonnegative interference:

```text
v^H G v = |c^T v|^2 <= M^2
SINR <= P_W * effective_reference_per_W * M^4
```

The earlier unconditional statement that the sensing figures exceed their
model bound is **retracted**: the source does not identify the ratio's inverse
power unit or whether its noise is raw per PRI or matched-filter processed.
The bound is exact, but applying a particular numerical value requires an
explicit reference contract. Physical P30dBm remains1W under every contract.

For L1 and the printed reference level−73.88dB, the conditional bounds are:

| Reference contract | Fig3, M400 bound | Fig15, M100 bound |
| --- | ---: | ---: |
| Declared inverse-W, gain1 default | 30.2024dB | 6.12dB |
| Declared inverse-W, effective gain100 candidate | 50.2024dB | 26.12dB |
| Inverse-mW reference, converted to SI, gain1 | 60.2024dB | 36.12dB |

Coherent PRI integration, processed-noise normalization or a reference-level
difference can yield an effective noise/reference factor in Eq9. Their physical
origin must not be inferred from one ordinate. `mis-sensing/normalization.py`
and its MATLAB counterpart separately declare unit, raw/processed domain,
effective factor and physical watts; processed reference gain cannot be counted
twice. Default `settings.json` uses the explicitly labelled literal gain1
interpretation; `settings_reference_candidate.json` is a distinct factor100
candidate with unverified physical attribution and unchanged full budgets.

Using the full M100/four-target continuous-RIS scene, all six original power
samples P15:3:30dBm and the original per-start RALM budgets, the factor100
candidate yields a maximum absolute error of0.008354dB and RMSE0.004852dB
against the original EPS. This is a six-point numerical fingerprint for an
effective20dB reference/noise difference, **not proof that the original Tp was
100**. The diagnostic actually used one deterministic initialization per
target/power, not the6000-start bank; some historical stopping flags failed.
Its quantized1bit/2bit results do not match at the same precision. It therefore
does not certify all curves, the MIS curve, full optimizer convergence or the
73 numerical figures. Original ordinates remain comparison-only data and never
enter an optimiser or phase-fitting objective.

To explicitly inspect the candidate, use a package command such as:

```sh
python strict/mis-sensing/run.py --figure fig3 --settings strict/mis-sensing/settings_reference_candidate.json --dry-run --output candidate-plan.json
```

Passing that settings file to an actual full command retains the full original
6000/30/4000 configured bank. A diagnostic or plan is not bank execution.

`mis-sensing/test_figure_inputs.py` independently tests conditional bounds,
original target markers and the rectangular PSLR guard. `test_normalization.py`
tests SI/reference equivalence and rejection of double-counted processing gain.
`test_closed_form.py` checks exact finite phase/field identities at20×20/16×16,
all25 overlaps and all nine placements. MATLAB mode `closed-form-test` provides
the corresponding independent checks:

```sh
python strict/mis-sensing/test_closed_form.py
python strict/mis-sensing/test_normalization.py
```

```matlab
run_mis_sensing('closed-form-matlab-tests.json','closed-form-test');
```

SINR line searches now use an algebraically exact objective increment to avoid
cancellation between near-equal ALM objectives, with all cross terms and
positive-part active-set crossings retained. A recorded backtracking-exhaustion
restart retries the current block's negative gradient without clipping the
original PR coefficient, changing ALM updates or relaxing Armijo/feasibility/
stopping thresholds. These are disclosed numerical safeguards, not different
theoretical algorithms or convergence certificates. PSLR retains its own metric.

`compare_beams.py` compares actual dual full-grid outputs, not original
agreement. `test_figures.py` exercises negative cases for missing curves/samples,
reference misuse and partial banks. Old failed solver receipts remain preserved
with their original source hashes; they do not describe new-version residuals.

The complete-size ISAC case0 with a disclosed larger unreported W cap passed
its original stopping/physical checks across all six schemes, but is one
realization, not100. Its zero BS-RIS bridge is retained, not used to manufacture
RIS gains. Hotspot full-size conic failures are preserved, not omitted from
MC means. Hardware experimental figures need original measurement evidence,
not synthesized simulation traces.
