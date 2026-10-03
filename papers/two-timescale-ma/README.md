# Two-timescale movable-antenna MU-MIMO: independent MATLAB + Python core

Paper: [Zheng et al., IEEE TCOM (2025)](https://doi.org/10.1109/TCOMM.2025.3585515).
The [author-posted arXiv v2](https://arxiv.org/abs/2410.05912v2) explicitly links that published DOI. Equation numbers refer to its [primary full text](https://arxiv.org/html/2410.05912v2).

This is newly written code, **not the authors' original simulation package and not reproduction of every published figure**. It implements the MRT statistical-CSI position optimizer in a reduced 6-antenna/3-user wavelength-normalized scene. It does not use rotatable-antenna or imperfect-CSI TWC models.

## Implemented

- Rician LoS phase model and i.i.d. NLoS core assumption (Eqs. 1–2).
- MRT approximate statistical sum rate (Eq. 13), exact antenna-position gradient, global antenna-wise curvature bound.
- Antenna-wise AO/SCA quadratic lower bound (Eq. 31) with linearized minimum-distance constraints (Eq. 30). The 2D convex subproblem is solved by polygon projection, without CVX.
- Instantaneous MRT with Eq. 10 channel-proportional power; instantaneous equal-user-power ZF (Eqs. 32–35); ZF statistical lower bound (Eqs. 37–39).
- Fixed-array baseline, optimized positions, actual objective histories, finite-difference gradient, spacing/box/power/ZF-interference checks, and Rayleigh position-invariance check.

ZF metrics at optimized positions are explicitly **ZF evaluated at MRT-optimized positions**, not a ZF-optimized design. The three explicit complex NLoS arrays in `fixture.json` are deterministic parity inputs, not a Gaussian Monte Carlo experiment; their rates must not be described as ergodic estimates. The statistical Eq. 13 quantity is an approximation, not the exact expected rate.

## Not implemented

The paper's ZF position AO/MM algorithm, spatial-correlation extension, energy/latency study, full parameter sweeps, and original 20 figures are not included. No global-optimum or general-gain claim is made. The eigenvalue curvature formula follows Eq. 29a; the inconsistent square-root sign printed in Eq. 29b is not copied.

## Run

Python requires NumPy:

```sh
python papers/two-timescale-ma/run.py --output results/two-timescale-ma-python.json
```

MATLAB requires only base MATLAB:

```matlab
addpath('papers/two-timescale-ma');
run_two_timescale_ma('results/two-timescale-ma-matlab.json');
```

Create the output directory before the MATLAB call. Both implementations load exactly the same fixture (no cross-language RNG). Results contain `paper_id`, `metrics`, `checks`, and `history`. Source/equation traceability and deviations are in `source_map.json`. Values are computed from the model and optimization; no published curves are embedded.
