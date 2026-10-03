# Strict full-scenario reproduction work

**Status: implementation and source verification in progress. No package has passed full published-figure reproduction.**

The original theoretical algorithms, dimensions, physical units, channel assumptions, baseline definitions, initialization counts, stopping rules, and figure scenarios must be retained. No alternative algorithm or smaller production scenario may be used to stand in for the paper.

The older `../papers/` implementations are superseded previews, not this strict release. Existing parity outputs in `../validation/` concern only those previews.

## Release gates

1. Verify the final accepted/published source and map every algorithmic update to that source.
2. Record complete figure-specific parameters and randomization/Monte Carlo policy; distinguish explicitly stated values from reproduction-tuned values. A plot tick is not automatically a simulation sampling grid. The author has authorized tuning unreported numerical settings, but not replacing algorithms or reducing the published scenario.
3. Resolve contradictory equations, dimensions, signs, or pseudocode using source cross-checks and mathematical derivation. Document necessary corrections, the evidence, and their effect; do not silently repair them or describe a reproduction-chosen value as published.
4. Implement the original mathematical subproblems in both languages. Different numerical convex-solver backends are acceptable only when they solve the same original subproblem with verified residuals; replacing the subproblem with gradient descent, ZF, fixed power shares, or another surrogate is not acceptable.
5. Run component/gradient/constraint checks separately from complete simulations. A component test may not be described as a full-scene reproduction.
6. Execute the full original scenarios, preserve actual outputs and termination records, and compare the corresponding figures, baselines and theoretical quantities. No timeout, partial batch, or missing figure may be relabeled complete.

## Known source/configuration gaps

- MIS communications: original smoothing/iteration/initialization settings are incompletely stated, and the displayed maximization objective conflicts with descent-direction wording. Tuned settings and the necessary objective-sign correction must be explicit.
- MIS sensing: the source supplies 6000 starts, 30 outer and up to 4000 inner iterations, but the pseudocode and numerical section disagree on the stopping-condition connective. The selected interpretation must be documented and compared; the full budget must not be silently reduced.
- Rotatable-array ISAC: original QT/MM, RCG and PGA/BB rotation updates are implemented independently of the preview's alternative updates. Omitted numerical settings are recorded as tuned; final-version equivalence and complete figure convergence remain unverified.
- Two-timescale MA: original MRT AO/SCA and ZF AO/MM are now implemented independently. The unique eigenvalue typo is documented; the correlated-ZF matrix products remain undefined at the paper's N≠M dimensions. No different covariance approximation is substituted.
- Cooperative SatCom: finite-Rician moments, statistical/two-timescale expressions, AP/MR QT and the author's RMO phase updates are implemented. Source-version and referenced antenna-pattern conformance are recorded separately; author-model results must not be called final-published-figure agreement.
- Hotspot SatCom: instantaneous QT/SOCP, AO/SDR randomization and the author's original RGD/two-stage algorithms are implemented. The supplied maximization objective uniquely resolves its printed descent-sign conflict; this and the lifted/unlifted formula typos are documented. The author's statistical-CSI QoS-to-SOCP expression has a genuine mathematical inconsistency. It is not replaced by instantaneous CSI, LoS-only design or another optimizer.

See each package's source contract and `status.json`. Ordinary unpublished numerical controls may be tuned and validated, with the provenance recorded. An undefined mathematical model or incompatible source versions remain scientific blockers until resolved. They must never be silently replaced with a different model or a reduced configuration.

## Current execution evidence

`validation/` separates original-algorithm component outputs from full figure work. Python and actual MATLAB executions cover shared algebra/gradient/convex-subproblem inputs; these checks do **not** certify all full-scene chains or all paper figures. The MIS closed-form beampattern has also been evaluated at 20×20 / 16×16 with 9 targets and a full front-hemisphere grid, but agreement with the original numerical figure is not certified.

Full-size optimizer debugging is an explicit release gate. The first sensing Fig3 batch retained 6000 starts / 30 outer / 4000 inner caps. Eight starts finished without a feasible converged result; diagnostic reruns exposed a simplex-boundary line-search issue. That unsuccessful batch was stopped and preserved, not counted as successful reproduction. Numerical corrections must be rechecked in the full-sized scenario before resuming with a new source-version checkpoint.

Original distinct per-block MIS step sizes are implemented; the earlier common-step experiment remains diagnostic only. Actual full-size 30×4000 single-start trials, including failed line searches and unmet residuals, are retained in `validation/diagnostics`. No 6000-start success is inferred from one start.

A complete first ISAC realization executed all six schemes at the full dimensions but failed the inner-convergence gate: 33 of 111 W calls hit an independently chosen 500-iteration cap. An isolated, otherwise identical original QT/MM trial reached the unchanged relative criterion after 2828 updates. Its first 500 objective values exactly matched the earlier trajectory. The unreported W cap is now 10000; this increases computational allowance without changing the model, optimizer, threshold or 100-channel requirement. It is not proof of original nonconvex stationarity or all-figure completion. The first realization also has a zero BS–RIS bridge under the original half-space visibility law, so it cannot demonstrate a RIS gain; it is preserved, not removed from the bank.

Both satellite physical models and bounded original-algorithm chains have been checked, with actual conic-solver residuals and stop reasons. A feasible bounded chain remains different from a fully converged sweep. The formal Hotspot phase method is the author Algorithm 3-2 RGD, not the optional RCG diagnostic.

The author chose to proceed with the supplied LaTeX and accessible author manuscripts rather than wait for institutional publisher-PDF access. Final-PDF equivalence remains unverified, but this is not a reason to replace or stop implementing the supplied mathematical model.

## Dependencies

Python convex blocks use CVXPY with a supported conic solver (`requirements.txt`). MATLAB convex blocks use an independently installed CVX toolbox; MIS and ISAC use base MATLAB. These dependencies and their licenses are not bundled with the public source; do not upload proprietary solver binaries, manuscripts, reviewer material or private datasets.

Actual local checks used Python 3.12, MATLAB R2025b and CVX 2.2.2 with free SDPT3. On this MATLAB release, CVX's official `functions/vec_` support directory needed to be added to the path. SDPT3 log/exp programs use CVX's documented successive-approximation backend and emit a warning; objective and physical residuals are checked rather than suppressing that warning or claiming bitwise solver equality.
