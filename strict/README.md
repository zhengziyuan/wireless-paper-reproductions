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
- Rotatable-array ISAC: final-version identity and omitted noise/sector/iteration/sweep settings are being checked. Original QT/MM, RCG and rotation updates must replace the preview's alternative updates; unreported settings must be documented as tuned.
- Two-timescale MA: original MRT and ZF optimization must both be implemented. The source contains an eigenvalue-expression sign inconsistency and a correlated-ZF dimension issue; missing full experiment settings remain unresolved.
- Cooperative SatCom: the accessed author manuscript is not yet verified against the final published version. Original finite-Rician statistical/two-timescale expressions, AP/MR/QT and phase-design algorithms and full figure settings are required.
- Hotspot SatCom: the final journal full text has not been obtained. Thesis/abstract cross-checks cannot certify final formula-level equivalence; no ZF baseline may replace the original QT/SOCP and AO/SDR stages.

See each package's source contract and `status.json`. Ordinary unpublished numerical controls may be tuned and validated, with the provenance recorded. An undefined mathematical model or incompatible source versions remain scientific blockers until resolved. They must never be silently replaced with a different model or a reduced configuration.

## Dependencies

Python convex blocks use CVXPY with a supported conic solver. MATLAB convex blocks use an independently installed CVX toolbox. Manopt may be required by a package. These dependencies and their licenses are not bundled with the public source; do not upload proprietary solver binaries, manuscripts, reviewer material or private datasets.
