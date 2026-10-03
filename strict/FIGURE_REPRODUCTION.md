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

These commands write numerical JSON, PNG/SVG and a render receipt. Actual
MATLAB/Python full-grid outputs have been compared and agree, **but this
closed-form result does not yet match the original figure**. Titles explicitly
state that original agreement is unverified. Display cropping/color limits
change neither stored samples nor physical scenarios.

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

## A source inconsistency that tuning cannot repair

In supplied sensing R1 Eqs9/11, steering entries and entries of
`v = bar(theta) .* phi` have unit modulus and `G = conj(c) * transpose(c)`.
Therefore, with nonnegative interference:

```text
v^H G v = |c^T v|^2 <= M^2
SINR <= P_W * (beta^2/sigma^2) * M^4
```

The stated L1, P30dBm=1W and reference ratio-73.88dB imply:

| Source figure | M | Absolute model upper bound | Original ordinate |
| --- | ---: | ---: | ---: |
| Sensing Fig3 | 400 | 30.2024dB | 32.02dB |
| Sensing Fig15, P30dBm MIS | 100 | 6.12dB | 21.67dB |

These source inputs and outputs cannot hold simultaneously under the printed
model. More starts/tighter solvers cannot exceed the bound. The author answered
that the three stated parameters should be correct; they remain unchanged.
No extra array/processing gain, changed power unit or fitted beta is silently
inserted. The inconsistency needs resolution before original-curve certification.

`mis-sensing/test_figure_inputs.py` independently tests the bound, original
target markers and rectangular PSLR guard. `compare_beams.py` compares actual
dual full-grid outputs, not original agreement. `test_figures.py` exercises
negative cases for missing curves/samples, reference misuse and partial banks.

The complete-size ISAC case0 with a disclosed larger unreported W cap passed
its original stopping/physical checks across all six schemes, but is one
realization, not100. Its zero BS-RIS bridge is retained, not used to manufacture
RIS gains. Hotspot full-size conic failures are preserved, not omitted from
MC means. Hardware experimental figures need original measurement evidence,
not synthesized simulation traces.
