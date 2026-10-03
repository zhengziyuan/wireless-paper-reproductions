# Cooperative multi-satellite / multi-RIS: author-model implementation

DOI: [10.1109/JSAC.2024.3460068](https://doi.org/10.1109/JSAC.2024.3460068).

New independent MATLAB + Python implementation of the accessible author manuscript and supplied author thesis. **Not the original author code.** Final-publisher equivalence and agreement with published figures remain unverified: the accessible author PDF has16 pages while the final journal paper has18. No private PDF/LaTeX is redistributed.

## Implemented scope

All eight AP-AO/MR-S-PA/MR-S-TS/MR-TTS-PA/MR-TTS-TS/AP-NoRIS/MR-S-NoRIS/MR-TTS-NoRIS chains are implemented. AP uses the actual complex QT precoder and per-user author manifold gradient method. MR allocates independent powers for every satellite/user, not fixed shares or scalar bisection. Two-stage phase design uses exponential smoothing and the **full squared interference residual** penalty, including negative residuals, then genuine QT. TTS moments retain the finite-Rician bilinear NLoS product and its non-Gaussian fourth moment. Phase gradients are analytical, not finite-difference optimization.

The generator retains J3/U2/N16/M25/K1 and reported source altitudes/Rician/default parameters. Fair single-vs-multi comparisons use N48/P150W against3x16 antennas/3x50W with1.25/2.5deg offsets. GT receive radiation uses actual ITU S.1428-1 piecewise main/transition/side/back lobes referenced by the S.1503 FSS prescription, not a generic sidelobe envelope.

`full_config.json` separates source-reported candidates from **tuned/not-reported** gains, diameter, coordinates, seeds, exact grids,1000 MC samples, caps and thresholds. These are not recovered original figure settings. A fixed statistical geometry is optimized analytically; MC independently validates its moments instead of repeating identical deterministic optimization1000 times.

## Run

```text
python run.py --component-test --output outputs/component-python.json
python run.py --model-test --output outputs/model-python.json
python run.py --chain-test --output outputs/chain-python.json
python run.py --full --sweep base --output outputs/full-base-python.json
python run.py --full --output outputs/full-sweeps-python.json
```

The first three are bounded mathematical/integration tests, **not full paper reproductions**. Full runs never silently shrink dimensions/counts. One configured figure family can be selected by its id; fair-comparison IDs include `multi_vs_single_single_1.25_kL20`. Full runs have not started, and honest runtime needs a coordinated benchmark.

MATLAB needs external official CVX2.2.2/free SDPT3, not vendored here. Run `cvx_setup`, set `cvx_solver sdpt3` and `cvx_precision high`, and add this directory:

```matlab
strict_satcom_component_test('outputs/component-matlab.json');
run_strict_cooperative_satcom('full_config.json','outputs/full-base-matlab.json','base');
run_strict_cooperative_satcom('full_config.json','outputs/full-sweeps-matlab.json');
```

CVX2.2.2/MATLAB R2025b may need CVX's official `functions/vec_` folder onpath. Exact variable-coordinate normalization improves conditioning without changing the problem. Changed-phase MR warm starts are scaled once uniformly to restore feasibility; optimized JxU powers remain independent. Solver feasibility and deterministic moment/gradient identities are checked separately; numerical backends need not yield identical nonunique beamformers.

## Evidence and limitations

Full-count Python synthetic components passed physical constraints/QT identities. Full geometry analytical gradients and a bounded all-eight-scheme chain passed. See `outputs/` and `source_contract.json`; tests keep `full_reproduction_pass:false`.

Publisher-version reconciliation is outstanding. Public-author Eq30d's power coefficient appears inconsistent with original physical Eq25c; implementation follows the physical constraint also given in the thesis. The cited S.1503-3 edition itself was not downloaded; available S.1503 editions verify the FSS S.1428 reference. Numerical values/exact grids are disclosed tuning. All full sweeps, both-language full-run validation and agreement with plotted paper curves remain to be completed; do not advertise this as complete reproduction of every final figure.
## Termination and full-sweep receipts

Every executed scheme now records each QT/AO/RMO stopping rule, actual final
residual, threshold, iteration count and whether its safety cap was exhausted.
The original objective/gradient stopping tests and optimization updates are not
changed by these receipts. A converged outer loop does not mask a capped RMO
block; MR-PA additionally records whether its AP-AO phase source converged.
Solver-primal normalized residuals and QT lower-bound violations have separate
gates, with `1e-5` tolerances explicitly classified as tuned numerical validation.
The Python output names the backend and retains available solver statistics;
MATLAB retains CVX status and reported solver tolerance. Normalized physical
power/interference residuals are checked in addition to native conic residuals.

`overall_implemented_scope_success` concerns only the selected author-model
sweeps, never publisher-final figure agreement. Any failed, capped or numerically
unvalidated scenario stays in the output and makes its `valid_figure_point=false`.
`all_configured_sweeps_requested` distinguishes one requested sweep from the whole
configured sweep set. The bounded chain test intentionally need not converge and
continues to declare `full_reproduction_pass=false`. Run `python
test_termination.py` for receipt-only regression tests; these synthetic statuses
are never written as paper curves. No full MC sweep was run to add these gates.
