# MIS communications: independent core-algorithm reproduction

Paper: [Movable Intelligent Surface (MIS) for Wireless Communications: Architecture, Modeling, Algorithm, and Prototyping](https://doi.org/10.1109/TWC.2025.3621083). Mathematical source: [arXiv v1](https://arxiv.org/html/2412.19071v1). Equation numbering here is the public arXiv v1 numbering; see `source_map.json`.

This is freshly written code, **not the author's original simulation bundle and not a reproduction of every published figure**.

## Implemented scope

The discrete row-major MS2 shifts, selection/padding vectors, and composite aperture are implemented as
`theta_bar_u = S_u theta + e_u`, `v_u = phi .* theta_bar_u`.
The LoS/MRT communication SNR is `iota_k * abs(c_k^T v_u)^2` with an ordinary transpose. The fixture provides normalized cascaded spatial frequencies; the channel is generated using a canonical planar plane-wave response. This avoids ambiguity from angle-symbol and extra-factor typesetting inconsistencies in preprint array expressions.

For fixed phases, each user's schedule is the exact best available position; there is no exclusive-use constraint between users. Phase design maximizes the paper's stable log-sum-exp soft minimum using analytic angle-coordinate gradients, exponential circle updates, and Armijo backtracking.

Schedules use the smallest position index among machine-equivalent maxima: a tie is at most `32*eps*max(abs(row))` (normal-range floor for a zero row). This floating-point tie convention is not a result-matching tolerance; it prevents identical static patterns from taking different branches under MATLAB/NumPy BLAS.

## Deliberate algorithm differences

- Scheduling is eliminated exactly, rather than optimized on the paper's relaxed multinomial manifold.
- Circle steepest ascent replaces Riemannian conjugate gradient; smoothing stays fixed at the fixture's `mu`, rather than the paper's continuation schedule.
- Position switches make the reduced objective piecewise smooth. No global-optimum or original-paper convergence theorem is claimed.
- The static benchmark optimizes an MS1 aperture of the **same size**, with MS2 phases fixed at zero. It is not the paper's fixed-total-element allocation comparison.
- The best evaluated true worst-SNR incumbent is retained; an optimized static design is a feasible initialization of the MIS design.

The example has MS1 4×4, MS2 2×2, three directions, nine positions, two deterministic starts, and 180 steps/start. It uses explicit phase arrays, with no random-number generator. These budgets/settings replace original sweeps, not emulate them.

## Run

Python 3.10+ and NumPy; base MATLAB with implicit expansion and JSON support. The repository validation report records the actually tested MATLAB version.

```sh
python papers/mis-communications/run.py --output results/mis-communications-python.json
```

```matlab
addpath('papers/mis-communications');
run_mis_communications('results/mis-communications-matlab.json');
```

Run from the repository root. Both implementations read exactly the same `fixture.json`; channel samples and initial phases are not generated independently.

## Outputs and checks

JSON has `paper_id`, `metrics`, `checks`, and `history`. Metrics include all user/position SNRs, selected one-based position indices, optimized phases, a static comparison, and the smoothing gap. History records Armijo softmin values and the best true minimum seen.

Checks verify finite outputs, unit modulus, one-hot scheduling, analytic finite-difference gradients, the direct quadratic/amplitude identity, softmin bounds, and accepted-objective monotonicity. These numerical checks do not prove global optimality.

Not reproduced: the original Monte Carlo/sweep budgets, all article figures, hardware fabrication, EM models, raw chamber data, USRP/LTE experiments, or measured 12.2 GHz results. No private paper drafts, author code, measurements, or credentials are included.
