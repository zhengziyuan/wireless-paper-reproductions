# Rotatable active/passive-array ISAC: independent MATLAB + Python model core

Paper: [Low-Altitude ISAC with Rotatable Active and Passive Arrays](https://doi.org/10.1109/JSTSP.2026.3693227), primary full text [arXiv:2512.20987](https://arxiv.org/html/2512.20987).

This release is newly written, **not the authors' original code, not all published figures, and not an implementation of every published solver**. It reproduces the paper's rotation-aware channel and ISAC utility model in a small deterministic scene and solves it with an explicitly disclosed analytic-gradient AO variant.

## Implemented

- Euler rotation `Rx Ry Rz`, rotated coordinates and steering phases, one-sided directional element power gains (Eqs. 2–11).
- Complex multipath BU/RU/BR links, RIS-composite communication and sensing fields (Eqs. 12–14).
- Communication plus dedicated sensing beams, sensing-beam interference in SINR (Eq. 17), actual transmit beampattern (Eq. 18b).
- Scale-normalized NMSE, exact `iota` update (Eqs. 22–23), weighted rate-minus-NMSE objective (Eq. 24).
- Alternating analytic-gradient precoder, phase and rotation updates with Armijo acceptance; power-ball, unit-modulus and mechanical-box feasibility.
- Fixed-array baseline with optimized electronic precoder/phases, joint-rotation variant, genuine objective histories, full real-variable gradient check and NMSE/utility identities.

The shared scene uses two users, 2×2 BS and RIS panels, two paths per link, six sensing look directions and normalized wavelength/power. Those are **test input choices**, not published figure parameters. Rates are single-fixture results and not Monte Carlo averages. The RIS initial `Rx(pi)` face orientation makes reciprocal incident and user directions visible; the angle box is centered on that frame. Eq. 12b is followed literally with its Hermitian bridge convention.

## Solver deviations and limits

The precoder uses projected gradient, **not QT/MM**. RIS uses phase-gradient ascent, **not Riemannian conjugate gradient**. Rotation uses analytic Jacobians and projected Armijo steps, without BB initialization. The exact scaling is held fixed during each outer AO sweep and refreshed between sweeps. These substitutions are intentional to produce a transparent base-MATLAB/NumPy implementation, not evidence that the published solver or published curves were reproduced.

Not implemented: paper QT/MM QCQP subsolver, RCG, 100-realization study, all original parameter sweeps, statistical CSI, movement energy/latency, hardware measurements, or global optimality/Pareto-frontier certification. No hardcoded rate curves are present.

## Run

Python requires NumPy:

```sh
python papers/rotatable-isac/run.py --output results/rotatable-isac-python.json
```

Base MATLAB:

```matlab
addpath('papers/rotatable-isac');
run_rotatable_isac('results/rotatable-isac-matlab.json');
```

Create the output directory before the MATLAB call. Both programs load the identical `fixture.json` (no RNG). JSON results contain `paper_id`, `metrics`, `checks`, and `history`. `source_map.json` records exact public equation labels, implemented scope and deviations.
