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
- Full-size scenario families for numerical Figs.3–20: convergence, power, Rician
  factor, movement region, user count, correlated extension, user/antenna position
  errors and full finite-grid exhaustive searches. The latter have no hidden cap;
  default actual-MC searches retain all ordered geometries and only prune
  infeasible partial spacing branches.

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
undefined when N=6,M=5 or N=8,M=5. No invented effective covariance, covariance
trace reduction or alternate Wishart approximation is substituted. The actual
channel (68) remains valid and is simulated for the correlated ZF comparisons;
outputs mark analytical (75) as blocked. Consequently the complete printed
correlated analytical derivation cannot honestly be claimed reproduced without
an author-approved expression. Figs.13–16 therefore remain original-figure
blocked, even if their implemented correlated-MC evaluations all finish. The
positions were optimized by the uncorrelated MRT/ZF objectives, not (69)/(75).

## Full configuration and provenance

`source_contract.json` maps models/equations and issues. `full_config.json` labels
paper-explicit settings, author-figure-axis inference and tuned metadata. N=6/M=5,
N=4/M=3, N=8 user/correlation experiments, path loss −40 dB/exponent2.8, distances
U[50,70]m, noise −80 dBm, P=1W, spacing lambda/2, angular distributions, kappa6/100
and zeta=0.00005 remain as specified. Position units are wavelength; lambda=1 is
a units choice, while path-loss/user-error distances remain meters.

The paper does not disclose MC counts or seeds. The full configuration chooses
**100 geometry realizations and 1,000 independent circular-complex-Gaussian NLoS
draws per geometry**, and a 1,500 AO/benchmark safety cap. These are tuned, not
quoted original counts. Full sweep grids are inferred from author figure ticks;
ticks alone do not prove every original marker. Initialization/factorization,
solver accuracy and benchmark stopping settings are also disclosed choices.
The original brute-force expectation/evaluation protocol is not fully disclosed.
The default `brute_force_objective="instantaneous_MC"` maximizes the **actual
sum-rate mean over the complete exported NLoS ensemble**, rebuilding the original
MRT/ZF beamformer at every feasible grid geometry. All ordered layouts remain,
because fixed finite random draws are not permutation-invariant. The explicitly
selectable `"paper_statistical_design_objective"` instead exhaustively optimizes
the MRT approximation / ZF bound and may remove permutation duplicates; such a
result is a finite-grid optimum of the **design surrogate**, not a true ergodic
finite-MC optimum. These protocols are not conflated or silently substituted.

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

Python: NumPy, SciPy (Bessel function), CVXPY and Clarabel. CVXPY is a numerical
backend for the **same original convex subproblem**, not a replacement update.
Python numerical settings are explicit in `full_config.json`.

```text
python run.py --component-test --output component-python.json
python figures.py --figure 5 --output-dir output/figure5
python figures.py --figure 5 --output-dir output/figure5 --prepare
python figures.py --figure 5 --output-dir output/figure5 --execute
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
bank or configuration mismatch is not called a full run. For correlated
Figs.13–16, completed numerical evaluations may set
`overall_implemented_scope_success=true`, but `original_figure_complete` and
`overall_full_success` remain **false** with
`original_figure_status="blocked_by_source_formulation"`; complete MC sample
counts cannot override the unresolved analytical/optimization scope. These
implemented receipts can be reused without endlessly rerunning unchanged MC.
MATLAB full wrappers
default to the immutable `run_config.json` beside the exported job folder.
An additional implementation fingerprint includes the actual engine sources and
runtime/dependency identity, so changing an algorithm cannot reuse stale results
even when its configuration and random inputs stay unchanged. Input identities
are shared across languages; implementation identities are intentionally separate.

MATLAB requires an **external official CVX installation**, not vendored here.
Run CVX setup and add its paths before these functions. In the tested official
CVX 2.2.2 layout, the `double vec` compatibility function may require:

```matlab
addpath(fullfile(cvx_root,'functions','vec_'))
addpath(pwd)
run_strict_two_timescale_ma('component-matlab.json');
run_strict_two_timescale_ma('scenario-matlab.json','output/figure5/jobs/case-000-mc-000.json');
run_full_ma_figure('output/figure5/jobs','output/figure5/matlab');
```

This path points to CVX's own support function; it does not replace any mathematical
subproblem. With SDPT3, CVX prints an **experimental successive-approximation**
warning for the logarithmic ZF objective. Record this backend warning and solver
status truthfully. An unavailable/failed solver is not replaced by a projected
gradient method; results are marked failed. A native exponential-cone backend,
when available, solves the same convex problem but must be named in run metadata.
The full configuration explicitly selects MATLAB `SDPT3`/`best` precision rather
than inheriting an unnoticed interactive CVX solver setting.

## Evidence and computational warning

Python full-N6/M5 component tests actually executed: MRT analytic gradients,
ZF Woodbury identity, MM tangency, two original convex coordinate subproblems,
spacing/box and curvature correction proof. Deterministic fixed-array benchmark
spot checks have also executed. These are **not full numerical figures**.
MATLAB/full-run status must be taken from actual output artifacts, not inferred
from the existence of this code. Full Monte Carlo figures have not been executed
by writing the drivers. Grid-search cost is `D^(2N)` before pruning; D=10,N=6
means 10^12 ordered candidate geometries. Even symmetry reduction does not make
the full original brute-force scenarios inexpensive. Do not launch them during
component testing or report unfinished partial searches as complete results.
