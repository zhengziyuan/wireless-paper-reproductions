# MIS sensing: independent reduced RALM reproduction

Paper: [Wireless Sensing with Movable Intelligent Surface](https://doi.org/10.1109/JSTSP.2026.3681476). Mathematical reference: [arXiv v1](https://arxiv.org/html/2509.15627v1). `source_map.json` separately records public-preprint and locally cross-checked article-section/equation locators.

This is freshly written code, **not the author's original simulation bundle and not a reproduction of every published figure**.

## Implemented scope

The full discrete overlap/padding aperture is `v_u = phi .* (S_u theta + e_u)`. For the cascaded plane-wave row `c_k^T`, the Hermitian PSD matrix is `G_k = conj(c_k) c_k^T`, so `v_u^H G_k v_u = abs(c_k^T v_u)^2`.

Echo powers are fourth order: `beta_k^2 * abs(c_k^T v_u)^4`. Sensing SINR divides each desired echo by the sum of all other target echoes plus `noise_k/P`. The example fixes one BS antenna, making the public preprint's `P L^2` normalization and the article's `P` normalization identical.

For fixed phases, scheduling chooses the highest SINR independently for every target. The optimizer uses the paper's inequality augmented-Lagrangian family:
`L = -eta + rho/2 sum(max(0, lambda/rho + eta-selected_SINR)^2)`.
Analytic phase/eta derivatives, Armijo descent, clipped multiplier updates, and conditional penalty growth are implemented.

Scheduling selects the smallest-index position among maxima separated by at most `32*eps*max(abs(row))` (normal-range floor for a zero row). This machine-scale tie convention avoids different branches for mathematically identical static patterns; it is unrelated to the cross-language parity tolerance.

## Explicit departures and source conventions

- Exact one-hot scheduling replaces the relaxed simplex variable and its inner RCG block.
- Exponential phase-coordinate steepest descent replaces inner RCG; branch changes make this a piecewise-smooth reduced RALM heuristic. The paper's convergence claims are **not** claimed for this altered solver.
- Penalty grows when feasibility progress is insufficient (`violation > 0.8*previous`), an explicitly chosen safeguard rather than the public v1 Eq. (29) displayed opposite inequality.
- The Hermitian rank-one matrix follows the stated PSD quadratic form and the article source. The preprint HTML Eq. (11) displays an unconjugated expression; that displayed expression is not used as an executable PSD matrix.
- The quadratic opposite-phase baseline is sampled from the heuristic section, using a fixture curvature; all non-overlapped padding elements remain in the evaluator. It is not a replay of the paper's continuous large-aperture/nearest-displacement plots.
- An optimized same-MS1 static aperture is a second baseline. The best evaluated phase design is retained and assigned the feasible epigraph value `eta=min(selected_SINR)`. The final *raw optimizer* eta may still violate constraints; outer-loop history records that violation explicitly.

The reduced example is MS1 4×4, MS2 2×2, three directions, nine positions, three deterministic starts, and 10 outer×60 inner iterations/start. It does **not** use the article's 6000 starts or 30×4000 budget. Explicit fixture phases/frequencies are shared by both languages; no RNG-identity assumption is used.

## Run

Python 3.10+ and NumPy; base MATLAB with implicit expansion and JSON support. The repository validation report records the actually tested MATLAB version.

```sh
python papers/mis-sensing/run.py --output results/mis-sensing-python.json
```

```matlab
addpath('papers/mis-sensing');
run_mis_sensing('results/mis-sensing-matlab.json');
```

Run from the repository root.

## Outputs and checks

The JSON interface is `{paper_id, metrics, checks, history}`. Metrics include target/position SINRs, fourth-order echo powers, exact schedules, phases, baseline results, and a **fixed-design** power sweep (no separate reoptimization at each power).

Checks cover the Hermitian quadratic identity, quartic echo identity, analytic SINR and augmented-Lagrangian gradients, circle and one-hot constraints, inner accepted-step descent, and returned-incumbent epigraph feasibility. `constraint_pass` refers to the returned physical/scheduling design, not convergence of the raw RALM eta. History contains real outer-loop objective, penalty, gradient, violation, and incumbent traces.

The quartic identity check independently constructs each Hermitian matrix `G_k`, evaluates `v_u^H G_k v_u`, squares that quadratic form, and compares it with the amplitude-based echo evaluator. It does not merely square and re-check the evaluator's own gain array.

Not reproduced: PSLR extension, stochastic trials, original figures, full-scale budgets, target detection ROC/waveform processing, hardware experiments, or unpublished measurement data. This nonconvex solver is not a global-optimality certificate.
