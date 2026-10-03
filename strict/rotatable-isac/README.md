# Rotatable active/passive-array ISAC: full-dimension theoretical implementation

This directory implements the rotation-aware model and QT/MM transmit QCQP,
RIS Riemannian conjugate-gradient (RCG), projected-gradient/BB rotation and exact
NMSE-scale AO in **Low-Altitude ISAC with Rotatable Active and Passive Arrays**.
It does not depend on, replace, or relabel the earlier reduced independent
package under `papers/rotatable-isac`.

Primary mathematical source: [arXiv full text](https://arxiv.org/html/2512.20987).
The current abstract [version record](https://arxiv.org/abs/2512.20987) still
describes an older MSE-constrained formulation; the title-matched author revised
source agrees with the weighted-NMSE HTML. The publisher-final version associated
with DOI `10.1109/JSTSP.2026.3693227` still needs a final version-to-equation check.
This code must not be described as numerical agreement with all published figures.

## What is implemented

- Rotation-dependent element positions, half-space directivity, all direct and
  RIS-assisted channels, steering/response Jacobians and analytic utility gradients.
- The original sensing Lipschitz MM upper bound, communication LDT/QT auxiliaries,
  original Q/P matrices, Hermitian eigendecomposition and scalar-dual bisection QCQP
  update. There is no projected-gradient replacement for this subproblem.
- Original untruncated Polak–Ribiere RCG, tangent projection, transport, normalized
  linear retraction and Armijo test. There is no phase-ascent or PR+ replacement.
- Original box-projected PGA and BB initialization, with the necessary numerical
  interpretations below recorded explicitly.
- Exact scale `iota=(p'p)/(pd'p)`, held fixed during each AO cycle.
- Full scenario drivers: original BS/RIS dimensions, 66 sensing samples, **100
  independent channels**, **all six original scheme families**, power/BS-count/
  user-count/rotation-range/rho sweeps. The complete 37-point rho grid is retained.
- Independent Python and MATLAB algorithms consume the same exported numerical
  inputs. The MATLAB implementation is base MATLAB; it does not require CVX.

## Paper parameters versus reconstructed settings

`source_contract.json` maps sources and algorithms. `full_config.json` explicitly
classifies paper-explicit, inferred and tuned settings. Published dimensions,
path counts, angular distributions, MC count, six schemes and sweep families are
not reduced. Figure tick values are evidence of axes, not proof of every original
sample marker. Noise, exact target-sector bounds, seed, numeric stopping budgets,
line-search settings, initialization and some rotation legends are not fully
specified in the final text. They are reconstructed/tuned, not invented quotations
from the paper. The desired-sector bounds occur in an earlier author script but
are not verified as the final plotting configuration.

Power-normalized directivity uses `G0=2(b+1)`: integrating the visible-half-sphere
pattern gives `2*pi*G0/(b+1)=4*pi`. This is a stated normalization interpretation,
not an unnoticed reuse of legacy `G0=1` settings. No-RIS zeros the whole BS–RIS
bridge, disabling both reflected communication and sensing paths.

## Transparent numerical safeguards

The component test runs at BS=4, RIS=36 and sensing-grid=66. In this deterministic
scene the printed untruncated PR direction becomes non-ascent on iteration 2.
`RCG_solver.mode="literal_printed"` records that failure. Formal full runs use
`"documented_non_ascent_restart"`: a non-ascent direction is restarted to the
Riemannian gradient, with **raw PR, raw slope and reason** in the output. The PR
coefficient is never truncated. This standard safeguard is not specified in the
printed algorithm and is not claimed otherwise.

The printed BB denominator is `s'*(grad_new-grad_old)`, negative near a concave
maximum. The full-size component test observes that sign and the resulting
clipping to `alpha_min`. The ascent secant uses the curvature of the minimized
`-F`, hence denominator `-s'*(grad_new-grad_old)`. Both `"as_printed"` and
`"ascent_sign_correction"` are selectable and the component output compares
them. Full configuration uses the disclosed correction. Armijo/feasibility checks
remain applied to the actual model, not surrogate or stored curves.

Half-space visibility at `b=0` is discontinuous at the boundary; zero response
derivatives are only piecewise derivatives, not global smoothness claims. Exact
`iota` is undefined at zero overlap, so this case produces an explicit failure.
Full runners retain failed/nonconverged outcomes instead of fabricating curves.

## Commands

From this directory, with NumPy installed:

```text
python run.py --component-test --output component-python.json
python figures.py --family power-b0 --output-dir output/power-b0
python figures.py --family power-b0 --output-dir output/power-b0 --prepare
python figures.py --family power-b0 --output-dir output/power-b0 --execute
python execute_bank.py --bank output/power-b0 --workers 2
python render_figures.py --bank output/power-b0 --output-dir output/power-b0/rendered
```

Without `--prepare`/`--execute`, the driver only writes a truthful workload plan.
Families: `power-b0`, `power-b2`, `bs-count`, `users`, `rotation`, `rho`. Formal runs
use a 10000-iteration W safety cap and 500-iteration AO/RIS/rotation safety caps,
not the component-test caps. The unreported W cap was increased after a full-size
trial needed 2828 updates to meet the unchanged original relative stopping rule;
the first 500 objective values exactly matched the earlier capped trajectory.
This is numerical-budget tuning, not a different optimizer or a full-MC result.
Resume checks
the SHA-256 of the entire immutable configuration snapshot and all scene
arguments. A result is reused only if all six schemes succeeded, converged and
passed physical checks. Failed/partial/nonconverged or changed-input results are
retried. Every W, RCG and PGA call records its actual termination reason, iteration
budget/count and original stop measurements. Reaching a safety cap without the
existing stopping criterion is `capped_unconverged=true`, not convergence.
`converged` retains the original outer-AO test; `inner_all_converged` requires
every applicable inner call in every AO cycle to meet its original stop criterion,
and `full_converged` requires both. Both language resume gates additionally check
the recorded inner measurements, so small outer improvement cannot hide an inner
cap. A criterion genuinely met on the last allowed iteration is not rejected just
because the budget was reached. Component diagnostics deliberately use bounded
inner caps and are not subject to the formal full-run convergence claim.
No mathematical update or stopping inequality was changed to add these records.
Full input-bank manifests validate every case's exact 100 realization
coverage; `overall_full_success` stays false unless **all** required jobs succeed.
An implementation fingerprint also includes engine-source and runtime identities;
changing the algorithm invalidates stale results even for unchanged numerical
inputs. Shared input fingerprints and language-specific implementation identities
are intentionally kept separate.
MATLAB full wrappers default to the immutable `run_config.json` beside the job
folder. Missing inputs or fingerprint/configuration mismatches are not treated
as completed full runs.

MATLAB:

```matlab
addpath(pwd)
run_strict_rotatable_isac('component-matlab.json');
run_strict_rotatable_isac('scenario-matlab.json','output/power-b0/jobs/case-000-mc-000.json');
run_full_isac_figure('output/power-b0/jobs','output/power-b0/matlab');
```

One exported scenario runs all six schemes. `fixture.json` is a deterministic,
full-dimension component input, **not a Monte Carlo experiment**. No private
manuscript or original proprietary code is redistributed here.

`execute_bank.py` consumes a **previously prepared immutable complete bank**,
retains every failed/nonconverged input slot, and writes durable per-job
progress. Its bounded workers each use one BLAS thread; this controls CPU,
not the100-channel population, six schemes or original stopping thresholds.
The separately frozen fixed-rotation-v3 power-b2 bank (five powers ×100 channels
×six schemes) is now actually running with two workers. All500 input jobs,
configuration and the input manifest are byte-identical to the retained v2 bank;
no old numerical result is reused. The incomplete v1/v2 outputs, scientific
sources and in-flight observations were hash-retained before the authorized
version transition. They are historical incomplete banks, not numerical-theory
failures or completed figures.

The first fresh v3 bank scenario passed all six original inner/outer stops and
physical checks. A separate actual production equivalence test compared all
six schemes' complete metrics, states, inner histories and stop gates with the
retained v2 result, bitwise. It also compared both full2828-update W blocks and
an active-RIS full500-update RCG block, including raw PR/Armijo/restart records.
The latter correctly retained its unconverged-cap status. No budget, stopping
threshold or direction update changed. See the
[W-block proof](FIXED_CHANNEL_CACHE_PROOF.md) and
[fixed-rotation channel-base proof](FIXED_ROTATION_BASE_CACHE_PROOF.md).
One successful scenario is **not** a completed100-channel point or500-job figure.

`render_figures.py` validates all100 channel receipts for every point before
producing any curve. It never averages only successful survivors. Rotation
figures select exactly the six source-verified legend series from five bound
pair families. Fig17 uses only the four original RIS-present series,
mean NMSE on the horizontal axis, mean rate vertically, with NMSE decreasing
left-to-right. These are render adapters, not verified numerical agreement.

## Current evidence and computational cost

Python component tests have actually executed: analytic W/RIS/rotation gradients,
QCQP KKT residual/power/actual-objective improvement, RCG unit modulus and exact
NMSE identity. Their numerical output is separate from formal figures. MATLAB
and full-run verification status must be reported from actual output files, not
this README. No full paper Monte Carlo sweep has been executed by creating these
drivers. The rho family alone requires 22,200 nested AO jobs; rotation legend
experiments can add more. No fabricated wall-time estimate is provided.

### Actual one-scene and W-budget diagnostics

One complete, full-dimension **single realization**, power26dBm/b=2/K=2,
was executed for all six schemes with the original selected 500-step inner caps.
It took 298.28 seconds. All six schemes met the outer-AO relative-increase test
and physical constraints, but **none passed full convergence**: 33 of the 111
W QT/MM calls exhausted their 500-step budget without the inner stop rule.
There were no RIS/PGA capped calls. This is a diagnostic, not a 100-realization
figure, successful full reproduction or evidence of RIS gain. In this realization
the RIS bridge is identically zero at the final orientations: its two arrival
visibility cosines are -0.1527 and -0.2619, all RIS phases remain one, and RIS
gradients vanish. Rot-/fixed-/no-RIS results coincide within each BS family.

An authorized follow-up changed **only the unreported W safety budget** from
500 to 10,000, preserving the complete input, original QT/MM formulas, fixed iota
and 1e-6 stopping threshold. This **one initial W block**, not six schemes or a
Monte Carlo sweep, reached the relative-objective stop after 2,828 iterations
(41.59 seconds). Its first 500 objective values matched the prior actual run
exactly; terminal relative improvement was 9.9982e-7 and power was 0.39810717W.
The last MM-QCQP stationarity residual was 4.66e-12, whereas the **actual nonlinear
fixed-iota objective** power-ball KKT residual was 0.12564 (relative0.02685).
Thus meeting the paper-style objective stopping rule is not proof of stationarity
or global optimality. A larger W budget is supported by this case, not guaranteed
for all original scenarios. Production-budget decisions and new complete runs
must remain separate from this diagnostic receipt.

The portable `diagnose_w_budget.py` reproduces this one-block test, requires a
same-engine actual reference, validates the unchanged trajectory prefix and
records actual/surrogate residuals, stopping status, timing and content hashes.
It never launches the full figure bank and stores no machine-specific paths.

```text
python diagnose_w_budget.py --scene exported/jobs/case-000-mc-000.json --reference full-scene-python.json --maximum-iterations 10000 --output diagnostic-w.json
```

### Actual six-scheme rerun with the selected 10,000-step W budget

On 2026-10-03 the **same full-size case-0 realization** was actually rerun for
all six schemes using a new immutable input/configuration snapshot. All physical
and random values were identical to the earlier 500-cap case; only `W_solver`
and disclosed parameter provenance changed. The W stop stayed at **1e-6**;
no dimension, sensing grid, original update, other solver budget or threshold
was reduced or relaxed. Actual elapsed time was **907.67 seconds**.

All six schemes passed the complete original-stop/physical/fingerprint gate:
every W/RIS/PGA call met its recorded stopping criterion and every outer AO
converged. There were **zero unmet-cap calls**. The three rotating-BS schemes
each used 32 AO sweeps and 18,330 W iterations; the three fixed-BS schemes each
used 2 AO sweeps and 2,831 W iterations. Across the six schemes this is 102 W
calls and 63,483 W iterations, with a maximum 2,828 iterations in any one W call.
Rotating-BS final utility/rate/NMSE were 5.83796359/12.33912820/0.65011646;
fixed-BS values were 3.51632793/13.19113355/0.96748056.

This is **one successfully converged realization, not a complete 100-channel
point, full figure, MATLAB full-scene validation or verified match to the
reference curves**. The RIS bridge remains exactly zero and all phases remain
one: the three schemes within each BS family coincide. It therefore provides no
evidence of RIS gain. Each rotating-BS trajectory also has two rotation blocks
stopped by the paper's relative-step criterion rather than the gradient
criterion; passing those original stop rules does not certify every block's KKT
stationarity or global optimality. A portable condensed actual receipt, including
the raw-result hash and exact configuration/input/engine fingerprints, is in
`diagnostics/2026-10-03-case0-w10000.json`. The reference figure/axis/metric
inventory and unresolved legend-selection details are in `figure_catalog.json`.
