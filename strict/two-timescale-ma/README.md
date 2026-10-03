# Two-timescale MA: original MRT AO/SCA and independent ZF AO/MM

This directory implements **Two-Timescale Design for Movable Antenna-Enabled
Multiuser MIMO Systems**, DOI
[10.1109/TCOMM.2025.3585515](https://doi.org/10.1109/TCOMM.2025.3585515).
The [primary arXiv v2 source](https://arxiv.org/html/2410.05912v2) and
[version/DOI record](https://arxiv.org/abs/2410.05912v2) match the MA paper, not the
separate rotatable-antenna manuscript. A title-matched author R2 source was checked
against these equations. No private manuscript or original author code is bundled.

This is not the old `papers/two-timescale-ma` MRT-only reduced implementation.
MRT and ZF independently optimize their own antenna positions through the actual
paper coordinate subproblems; ZF is not merely evaluated at MRT positions.
The current primary numerical backend is `certified_exact_2d`, solving the
**same original two-real-variable convex coordinate program** with complete
polygon active-set candidates and an independent concavity objective-gap
certificate. This is not a different AO/SCA/MM update; see
[the proof and actual tests](EXACT_2D_SUBPROBLEM.md).

## Implemented scope

- Rician channel (1)–(4); LoS spatial phases; MRT (10) and statistical approximation
  (13); original MRT coordinate AO/SCA surrogate (23)–(31), Algorithm 1.
- ZF beamformer (34), fixed equal power; statistical lower bound (37)–(39);
  Woodbury/rational identity (41)–(53); original MM and position-SCA minorants
  (54)–(67), Algorithm 2, solved as the stated concave convex-coordinate program.
- Original rectangular movement region and linearized minimum-spacing constraint.
- All five benchmark families: MA-MRT, MA-ZF, FPA-MRT optimized power, FPA-ZF
  water-filling power and FPA adaptive beamforming with LDT/QT. “FPA-OPT” is the
  paper's label; the iterative nonconvex beamforming solution is **not claimed
  globally optimal**. Baseline numeric stopping rules are reconstructed settings.
- Bessel covariance and valid correlated channel (68), Monte Carlo MRT/ZF,
  correlated MRT closed form (69). Correlated histories evaluate the actual
  correlated channel at every **uncorrelated-objective** AO sweep geometry;
  this is evaluation, not optimization of the correlated (69)/(75) objectives.
  Section V and the Figs.13/15 captions/text describe **model evaluation**, not
  a new correlated objective optimizer. Accordingly MRT Figs.13/15 use a
  **source-supported interpretation**: original Algorithm 1's iid trajectory,
  with iid/correlated Monte Carlo and (13)/(69) evaluations on the same geometry.
  This does not recover the author's unreported experiment records or establish
  that the resulting curves closely match the reference figures.
- Actual iid Monte Carlo rate histories for convergence Figs.3/4 and correlated
  model-comparison Figs.13–16, using the complete exported NLoS ensemble at every
  accepted AO sweep. The statistical objective is not mislabeled as actual MC.
- Full-size scenario families for numerical Figs.3–20: convergence, power, Rician
  factor, movement region, user count, correlated extension, user/antenna position
  errors and full finite-grid exhaustive searches. The latter have no hidden cap;
  default actual-MC searches retain all ordered geometries and only prune
  infeasible partial spacing branches.
  Figs.19/20 require their separately frozen complete source-axis configurations
  below; the historical shared `full_config.json` grid must not be used for Fig19.

## Explicit mathematical corrections and actual remaining blocker

Equation (29a) defines the largest eigenvalue of a real symmetric matrix
`[[a,b],[b,d]]`. Its characteristic polynomial gives
`lambda_max=(a+d+sqrt((a-d)^2+4*b^2))/2`. The printed (29b) has `-4*b^2`, which can
make the radicand negative. The default explicitly selects **(29a)**, retaining an
`equation_29b_as_printed` diagnostic option. This is a transparent uniquely
determined typo interpretation, not an alternative curvature model.

Algorithm 2 and the displayed coordinate constraints contain incorrect equation/
problem references. The default solves the mathematically stated **P5.n** with
the spacing inequality **(30)**, explicitly recorded in the source contract.

**Correlated-ZF analytical equations (72)/(74)/(75) remain genuinely unresolved.**
`Omega` is M×M, but spatial covariance `S(t)` is N×N; the printed products are
undefined when N=6,M=5 or N=8,M=5. In addition, (68)/(70) correlate the **rows**
of the Gaussian channel, whereas the standard Wishart assertion (71) requires
the relevant iid-row covariance structure; a dimension-only replacement does
not in general preserve that distribution. A second-moment counterexample is
provided in `correlated_model_notes.md`. No invented effective covariance, covariance
trace reduction or alternate Wishart approximation is substituted. The actual
channel (68) remains valid and is simulated for the correlated ZF comparisons;
outputs mark analytical (75) as blocked. Consequently the complete printed
correlated analytical derivation cannot honestly be claimed reproduced without
an author-approved expression. **ZF Figs.14/16** remain original-figure
blocked, even if their implemented correlated-MC evaluations all finish.
MRT Figs.13/15 have no such dimensional/formulation blocker: valid (68)/(69)
are evaluated on the original iid Algorithm 1 trajectory under the explicit
interpretation above. The source does not uniquely establish whether the author
instead reoptimized (69), so no recovered-original-protocol claim is made.
The optional derivative notes/tests are mathematical diagnostics, not a new
production optimizer or a silent reuse of the iid curvature for (69).

The new [exact original-model correlated-ZF evaluator](CORRELATED_ZF_EXACT_EVALUATION.md)
returns to the inverse-Gram/Jensen argument (35)/(37), before the invalid
Wishart step, and uses the exact conditional Gaussian Laplace integral under
(68). **No covariance or Wishart approximation is substituted.** Python and
MATLAB actually evaluated the same complete1000-draw original-N6/M5 geometry:
corrected population-Jensen plug-in26.2661648457, actual correlated-ZF
mean27.2396524305, and all5000 Schur identities passed. This dimension-correct
evaluation does not recover the undefined printed (74) or historical curves.
Finite-ensemble estimates are not guaranteed finite-MC lower bounds.
`evaluate_correlated_zf.py` writes separately labeled corrected histories on
a completed original Algorithm2 trajectory. Old blocked receipts are preserved.
The new [full corrected-source Figs.14/16 entrypoints](CORRECTED_SOURCE_FIGURES.md)
retain both original dimensions and all three Rician cases, with the complete
configured100 geometries/1000 draws and every accepted unchanged Algorithm2
position. Separate MC, exact-Jensen and error panels prevent confusing a
mathematically corrected evaluation with recovery of the historical figures.
Both Python and independent MATLAB full-bank adapters are provided; writing
or preparing them does not claim that all300 figure jobs have executed.

## Full configuration and provenance

`source_contract.json` maps models/equations and issues. `full_config.json` labels
paper-explicit settings, author-figure-axis inference and tuned metadata. N=6/M=5,
N=4/M=3, N=8 user/correlation experiments, path loss −40 dB/exponent2.8, distances
U[50,70]m, noise −80 dBm, P=1W, spacing lambda/2, angular distributions, kappa6/100
and zeta=0.00005 remain as specified. Position units are wavelength; lambda=1 is
a units choice, while path-loss/user-error distances remain meters.

The paper does not disclose MC counts or seeds. The full configuration chooses
**100 geometry realizations and 1,000 independent circular-complex-Gaussian NLoS
draws per geometry**. The historical `full_config.json` uses1,500 AO/benchmark
safety caps; the new independent
[`configs/full-ao10000-fig03-18-v2.json`](configs/full-ao10000-fig03-18-v2.json)
uses10,000 for AO while retaining the1,500 benchmark cap. These are unreported
controls, not source-specified iteration budgets. The physical problem, all five
schemes, solver certificates and the original5e-5 fractional stop are unchanged.
The [actual full-size slot68 replay](../validation/two-timescale-ma-corrected-zf/full-slot068-same-algorithm-unreported-cap-audit-v1.json)
converged at1599 sweeps; all1501 original objective/position entries and9000
coordinate records match the old1500 prefix bitwise. All1000 exported draws were
evaluated at every accepted position. The old failure is preserved, not relabeled.
A fresh complete200-job Fig3 bank uses the new config and byte-identical inputs,
with zero old-output reuse; its full completion is still pending. A single
successful long-cap replay does not guarantee that10,000 suffices for all jobs.

The MC counts, seed, initialization/factorization, solver accuracy and benchmark
stopping settings remain disclosed choices. Most sweep grids are inferred from
author figure ticks;
ticks alone do not prove every original marker. Initialization/factorization,
The original brute-force expectation/evaluation protocol is not fully disclosed.
The default `brute_force_objective="instantaneous_MC"` maximizes the **actual
sum-rate mean over the complete exported NLoS ensemble**, rebuilding the original
MRT/ZF beamformer at every feasible grid geometry. All ordered layouts remain,
because fixed finite random draws are not permutation-invariant. The explicitly
selectable `"paper_statistical_design_objective"` instead exhaustively optimizes
the MRT approximation / ZF bound and may remove permutation duplicates; such a
result is a finite-grid optimum of the **design surrogate**, not a true ergodic
finite-MC optimum. These protocols are not conflated or silently substituted.

The [direct original EPS marker audit](../validation/two-timescale-ma-corrected-zf/BRUTE_FORCE_SOURCE_PROTOCOL_AUDIT.md)
requires all D3:18 points for Fig19 and D3:12 for Fig20, separately:
[`figure19-full-axis-ao10000-fixed-mc-protocol-v2.json`](configs/figure19-full-axis-ao10000-fixed-mc-protocol-v2.json)
and [`figure20-full-axis-ao10000-fixed-mc-protocol-v2.json`](configs/figure20-full-axis-ao10000-fixed-mc-protocol-v2.json).
Both retain the full ordered fixed-draw MC search choice, not a recovered unique
author objective. Neither huge full search has completed. Separate WORK-only
exact statistical-objective B&B research passed
[eight complete small-grid and four active-spacing subtree checks](../validation/two-timescale-ma-corrected-zf/statistical-grid-certified-small-tests-v1.json);
it is not enabled as a production search, and large-D tractability is not proven.

Error scenarios are reconstructed as follows: user Cartesian coordinates are
perturbed independently within ±error meters before deriving design AoDs/path
loss; evaluation uses the true statistical geometry and instantaneous CSI. MA
position error perturbs the final optimized physical positions independently
within ±error wavelengths; instantaneous beamforming adapts to the resulting
true channel. This mapping is not fully specified in the paper and is therefore
classified as an implementation interpretation, not an original recorded setup.
Nominal design feasibility and realized, jittered-position feasibility are
reported in separate fields. Errors are not clamped to repair the constraints;
an error realization can therefore violate spacing or the movement box, and this
is reported honestly. The experiment does not claim imperfect instantaneous-CSI
beamforming: its short-timescale beamformer uses the true realized channel.

## Dependencies and commands

Python: NumPy/SciPy for the primary exact2D solver. CVXPY/Clarabel remain
optional backends for the same original convex subproblem; repository runtime
metadata currently records their versions. Primary backend names/settings are
explicit in the immutable selected configuration. The model,100x1000 population and original
outer stop are unchanged.

```text
python run.py --component-test --config configs/full-ao10000-fig03-18-v2.json --output component-python.json
python figures.py --figure 5 --config configs/full-ao10000-fig03-18-v2.json --output-dir output/figure5
python figures.py --figure 5 --config configs/full-ao10000-fig03-18-v2.json --output-dir output/figure5 --prepare
python execute_bank.py --bank output/figure5 --workers 1
python render_figures.py --bank output/figure5 --output-dir output/figure5/rendered
python figures.py --figure 19 --config configs/figure19-full-axis-ao10000-fixed-mc-protocol-v2.json --output-dir output/figure19
python figures.py --figure 20 --config configs/figure20-full-axis-ao10000-fixed-mc-protocol-v2.json --output-dir output/figure20
python test_exact_2d.py
python test_coordinate_scaling.py
python test_correlated_zf.py
python derive_figure04.py --source-bank output/figure3 --output-dir output/figure3/derived-figure04
```

Default figure invocation only writes the full workload plan. `--prepare` exports
complete shared random-input jobs, consumed by both independent language
implementations. `--execute` actually evaluates them. `--figure` accepts 3–20.
There is no tiny default profile or implicit full-sweep truncation. A SHA-256 of
the complete immutable configuration snapshot and every job argument binds each
result to its inputs. Only successful, converged, physically feasible nominal
designs with all five complete MC schemes are reused; brute force also requires
both searches complete. Failed, partial, nonconverged or changed-input results
are retried. `run_config.json`/`manifest.json` record the exact input bank. Both
languages validate every case's complete geometry coverage and output
`overall_full_success=false` until **all** required jobs succeed. An incomplete
bank or configuration mismatch is not called a full run. For correlated-ZF
Figs.14/16, completed numerical evaluations may set
`overall_implemented_scope_success=true`, but `original_figure_complete` and
`overall_full_success` remain **false** with
`original_figure_status="blocked_by_source_formulation"`; complete MC sample
counts cannot override the unresolved analytical scope. For MRT Figs.13/15,
complete source-supported model-comparison evaluations can close the implemented
figure scope, but `original_curve_closeness_verified` remains false until an
actual reference comparison is performed. These
implemented receipts can be reused without endlessly rerunning unchanged MC.
The already-running corrected-source Fig16 bank retains its original1500-config
identity until a separate controlled transition; the new Fig3 configuration
must not be pasted onto those300 receipts. Its integral/evaluator fingerprint
and scope remain separate from the new AO-cap bank.
`derive_figure04.py` permits a source-matched full-bank reuse, not a reduced
experiment: Fig3 already executes both independent MRT/ZF optimizers. Only
after **all200** κ6/100 geometry jobs pass, the adapter checks exact original
case/config/input regeneration and freshly evaluates every accepted ZF position
with the identical **all1000** NLoS draws. Fig4 then explicitly records its
shared Fig3 source and fresh ZF MC-history derivation, without pretending to
have rerun identical position optimization. Until that full source gate passes,
the adapter emits readiness only, no partial curve.
MATLAB full wrappers
default to the immutable `run_config.json` beside the exported job folder.
An additional implementation fingerprint includes the actual engine sources and
runtime/dependency identity, so changing an algorithm cannot reuse stale results
even when its configuration and random inputs stay unchanged. Input identities
are shared across languages; implementation identities are intentionally separate.

MATLAB's primary `certified_exact_2d` backend uses base MATLAB and needs
**no CVX installation**. It has the same complete polygon candidates and
finite primal/global-gap certificate. Only the optional explicitly selected
SDPT3 conic branch requires an external official CVX installation, not vendored
here. The primary base-MATLAB commands are:

```matlab
addpath(pwd)
run_strict_two_timescale_ma_full_v2('component-matlab.json',[],...
    'configs/full-ao10000-fig03-18-v2.json');
run_strict_two_timescale_ma_full_v2('scenario-matlab.json',...
    'output/figure5/jobs/case-000-mc-000.json','output/figure5/run_config.json');
run_full_ma_figure_v2('output/figure5/jobs','output/figure5/matlab-full-v2');
```

The separately versioned MATLAB-full-v2 entry repairs the first assignment to
an empty history struct array; every numerical helper is otherwise exactly
text-identical to the preserved frozen engine. The original MATLAB engine,
its failed startup receipts, and the live Python implementation are unchanged.
The old batch's200 startup-error files are **not200 numerical scenarios**.
A WORK first full N6/M5 case has actually executed, and an independent oracle
recomputed all5×1000 physical sample rates, all accepted design objectives,
coordinate certificates and the original5e-5 stopping conditions; it also
matched the shared-input Python positions and curves. See
[the independent full-case receipt](../validation/two-timescale-ma-corrected-zf/first-full-job-matlab-recordfix-independent-validation-v1.json)
and [the exact numerical-source body proof](../validation/two-timescale-ma-corrected-zf/matlab-full-v2-source-body-identity.json).
These establish one full case, **not the new200-case bank or historical-figure
closeness**. The new executor uses fresh before/after source/runtime identities,
checks complete100×1000 exported inputs and criterion stops, and retains every
failed/stale attempt. It needs a fresh output folder; do not relabel the old
startup files as this version.

For the optional SDPT3 branch only, run CVX setup/add its paths. In the tested
official CVX2.2.2 layout the `double vec` compatibility path points to CVX's
own support function (`addpath(fullfile(cvx_root,'functions','vec_'))`); it does
not replace any mathematical subproblem. With SDPT3, CVX prints an **experimental successive-approximation**
warning for the logarithmic ZF objective. Record this backend warning and solver
status truthfully. An unavailable/failed solver is not replaced by a projected
gradient method; results are marked failed. A native exponential-cone backend,
when available, solves the same convex problem but must be named in run metadata.
The primary configuration explicitly selects `certified_exact_2d`; the optional
SDPT3/best branch requires a separate configuration with its backend recorded.

## Evidence and computational warning

Python full-N6/M5 component tests actually executed: MRT analytic gradients,
ZF Woodbury identity, MM tangency, two original convex coordinate subproblems,
spacing/box and curvature correction proof. Deterministic fixed-array benchmark
spot checks have also executed. These are **not full numerical figures**.
MATLAB/full-run status must be taken from actual output artifacts, not inferred
from code existence. Full-bank execution has started, but a passed single
geometry does not certify a complete100-geometry figure. `execute_bank.py`
writes durable per-job progress; failures remain in their original input slots.
`render_figures.py` emits curves only after every required100-geometry/1000-NLoS
receipt passes, never by averaging survivors. Unequal trajectory lengths use
an explicitly disclosed final-state hold, not invented AO updates.
Grid-search cost is `D^(2N)` before pruning; D=10,N=6
means 10^12 ordered candidate geometries. Even symmetry reduction does not make
the full original brute-force scenarios inexpensive. Do not launch them during
component testing or report unfinished partial searches as complete results.
