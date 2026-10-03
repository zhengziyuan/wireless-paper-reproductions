# Full corrected-source ZF Figs.14/16

These are explicitly **corrected-source original-model evaluations**, not
historical-figure recovery. The printed correlated-ZF (72)/(74)/(75) remain
undefined/unsupported for the stated row-correlated channel; see the
[dimension-correct proof](CORRELATED_ZF_EXACT_EVALUATION.md). No effective
covariance, trace replacement, iid approximation to the correlated channel,
fitted gain, or changed position optimizer is used.

## Full scenario and trajectory

Both original dimensions are retained: Fig.14 `N=8,M=5`, Fig.16 `N=6,M=5`,
with all three `kappa=5,10,15 dB` cases, original noise, power, geometry,
Bessel covariance, and minimum spacing. **100 geometries and1000 NLoS
draws per geometry are disclosed configured choices**: the source does not
state its original Monte Carlo counts. Neither number is reduced here.

The frozen original engine first executes the independent iid Algorithm2
ZF trajectory (and all original benchmark families). Both channel models
then use precisely that same accepted trajectory and the same exported1000
complex draws. No correlated-objective reoptimization is inserted. This is
the explicit source-supported evaluation interpretation, not recovery of
unreported experimental records.

`corrected_figures.py` and `run_corrected_ma_figure_matlab.m` require
**all300 source jobs** before deriving or plotting anything. Every source
job must pass its full benchmark/trajectory/constraint/coordinate-gap
checks. No survivor average is allowed. A missing/failed input slot stays
in its original slot; no replacement random geometry is sampled.

## Exact original-model expectation and complete evidence

At **every accepted ZF position**, both implementations independently:

- construct original iid `S=I` and correlated `S_nm=J0(2*pi*distance/lambda)`;
- evaluate all1000 original unit-norm equal-power ZF beamformers;
- check every `1000 x M` Schur inverse-Gram identity and all1000 rate identities;
- evaluate the exact conditional Gaussian Laplace inverse moment and average
  over all1000 supplied other-column draws;
- retain each conditional moment and its adaptive-quadrature error estimate,
  direct MC inverse diagonals, sample rates, per-user moments/standard errors,
  original position, and the unchanged original iid design objective.

The iid design optimizer **still uses the paper's original noncentral-Wishart
statistical expression**. The new iid exact-Jensen evaluation is diagnostic;
it does not silently change that optimizer or relabel its approximation.

The Jensen guarantee is on the **population** expectation. Its finite1000
outer-ensemble plug-in is not guaranteed to be below a finite MC sample
mean. Adaptive quadrature errors are reported numerical estimates, not
interval certificates. First-order delta standard errors are diagnostics,
not confidence intervals. The full evidence retains these distinctions.

## Five explicitly separate panels

The local source EPS legends list `MA-ZF, Simplified with MA spacing` and
`MA-ZF, Spatially correlated Rayleigh`, with three Rician cases. Those
legends do not independently determine whether historical values were MC
or the printed analytical formulas. Therefore the output keeps **six
curves per panel** and does not identify a new evaluator with the old plot:

1. Original-channel MC comparison, with the source's two-model structure.
2. Corrected exact original-model population-Jensen plug-in comparison.
3. MC minus Jensen plug-in diagnostic (no finite-sample lower-bound claim).
4. Outer-MC delta standard error diagnostic.
5. Quadrature rate-error estimate diagnostic.

Means include all100 geometries. For differing convergence lengths, the
last accepted state is explicitly held constant; no fictitious AO update
is created. Geometry standard errors are retained in JSON. Each panel has
all six legends, boxed axes, serif typography and vector SVG/PNG exports.

## Python full entrypoint

Run from repository root with one BLAS thread per worker. Use a **fresh**
bank name for preparation; an existing input bank is never overwritten.

```powershell
python strict/two-timescale-ma/corrected_figures.py --figure 16 --bank work/corrected-fig16 --prepare
python strict/two-timescale-ma/corrected_figures.py --bank work/corrected-fig16 --execute --workers 1
```

Fig.14 uses exactly the same commands with `--figure 14` and a separate
bank name. `--execute` completes/reuses the original engine receipts and
then derives the corrected panels. Resume uses the identical immutable
input bank and source/configuration hashes. Per-position cached evidence
is rejected if truncated, nonfinite or hash/position mismatched.

To inspect readiness without running any incomplete geometry:

```powershell
python strict/two-timescale-ma/corrected_figures.py --bank work/corrected-fig16 --output-dir work/corrected-fig16/corrected-source-figures
```

## Independent MATLAB full entrypoint

Use the Python-prepared **same** shared-input bank; no MATLAB resampling:

```matlab
addpath('strict/two-timescale-ma');
run_corrected_ma_figure_matlab('work/corrected-fig16/jobs', ...
    'work/corrected-fig16/matlab-source', ...
    'work/corrected-fig16/matlab-corrected', ...
    'work/corrected-fig16/run_config.json');
```

The optional fifth argument `false` derives from an already complete
300-job MATLAB source bank without rerunning it. All source checks still
run. Writing this entrypoint is not evidence that its full bank executed.

## Actual check scope, not a full-bank claim

The fresh segmented-integral Python and MATLAB checks actually ran full1000-draw
initial positions at **both N6/M5 and N8/M5**, both channel models. Independent
paired comparisons passed the unchanged per-moment fixed tolerances and combined
reported-error checks; see the
[quadrature audit and paired receipts](QUADRATURE_ACCURACY_AUDIT.md).
Python tests also covered the exact central-iid inverse moment and no-partial-bank
aggregation rules. Dedicated independent entrypoints remain available:

```matlab
validate_corrected_zf_position_matlab('n6-matlab.json', ...
    'work/corrected-fig16/jobs/case-000-mc-000.json', ...
    'work/corrected-fig16/run_config.json');
```

```powershell
python strict/two-timescale-ma/test_corrected_figures.py
python strict/two-timescale-ma/compare_corrected_positions.py --python n6-python.json --matlab n6-matlab.json --output paired-position.json
```

Separately, the first actually executed N6 Fig16 source trajectory was evaluated
at **all46 accepted positions**, with both unchanged channel models and all1000
exported draws at each position. It retained all5000 conditional moments/error
estimates per position/model, full Schur/rate checks and unchanged-source MC
matching; that diagnostic took `1031.067 s`. The full300-job Fig16 source bank
continues independently. One complete trajectory does not satisfy the all300
source/evaluation gate, and no partial-bank corrected figure is rendered.

Initial-position checks are **not all300 geometries, complete Algorithm2
trajectories, or historical original-curve closeness**. A corrected full
figure is complete only after its full source and full derivation summaries
both pass. Old blocked-formula receipts are preserved, not overwritten.

中文说明：这里修正的是原信道模型下的期望求值，不改原位置算法、不缩小
场景。原文无定义的闭式公式与历史图匹配仍单独标明；数值自洽、完整运行、
双语言对照、接近原图，是四个不同的验收项。
