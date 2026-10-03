# Cooperative multi-satellite / multi-RIS SatCom: independent core implementation

Paper: Z. Zheng et al., *Cooperative Multi-Satellite and Multi-RIS Beamforming: Enhancing LEO SatCom and Mitigating LEO-GEO Intersystem Interference*, IEEE JSAC 43(1), 279-296, 2025. [DOI](https://doi.org/10.1109/JSAC.2024.3460068). [Public author manuscript at EURECOM](https://www.eurecom.fr/publication/7869/download/comsys-publi-7869.pdf).

**Status: executable independent reduced core, not full-paper/figure reproduction.** Public author-manuscript equations were read and cross-checked against the author's doctoral thesis. The 16-page author PDF is not represented as the publisher's final typeset 18-page paper. `source_map.json` identifies verified model equations and algorithm changes.

## Implemented scope

- The exact deterministic-LoS limit of the paper's Rician cascaded channel: `h_L[j,u] = h_LL[j,u] + G_LR[j,u] diag(phi[u]) h_R[u]`. The 1-by-N UPA special case uses half-wavelength steering responses. Fixture amplitudes are **normalized test inputs**, not the publication's link-budget settings.
- Noncoherent multi-satellite MR transmission: desired **powers** are summed across satellites, not coherent amplitudes. The MR vectors are `sqrt(p[j,u]) h_L[j,u]`. The GEO-to-LU direct-plus-RIS interference, LEO-to-GT interference protection, per-satellite transmit power, and unit-modulus constraints are evaluated.
- A genuine unit-circle manifold ascent stage for a smooth minimum-SINR objective with the signed squared GT-interference residual penalty described in Section V. Analytic phase derivatives include the MR channel changes, desired/cross-user terms, GEO-to-LU cascade, and leakage. Armijo search and normalized retraction are implemented without Manopt.
- Exact max-min power allocation **within the additional restriction** `p[j,u] = satellite_share[j] q[u]`. For each target SINR, linear interference equations produce the componentwise minimum nonnegative power vector; bisection checks satellite-power and GT-leakage bounds. This is **not** paper Algorithm 2's quadratic-transform/CVX iteration and is not the unrestricted optimal power allocation.
- Initial-RIS and no-RIS baselines receive the same constrained power optimization. After the phase stage, power is reoptimized to restore physical feasibility. A feasible phase candidate is selected only if its minimum SINR does not decrease. This safeguard is an independent implementation addition.

The signed square penalty penalizes slack as well as violation; it is retained for correspondence with the source, not promoted as an exact replacement for inequality constraints. Physical constraints are checked separately. The fixed-power phase-stage utility can increase even when final max-min SINR does not; its history must not be interpreted as an original-paper convergence curve.

## Not implemented

Finite-Rician statistical closed forms, two-timescale random-channel expectations, adaptive-precoding AO/Algorithm 1, unrestricted QT/CVX power updates/Algorithm 2, all of Algorithm 3's smoothing-continuation stages, original orbital geometry and antenna-gain templates, Monte Carlo confidence intervals, and published Figures 2-11. There are no original measurement data or hardcoded published curves.

## Run

Python 3.10+ and NumPy; MATLAB uses only base MATLAB (JSON support and implicit expansion, R2016b+). From the repository root:

```sh
python papers/cooperative-satcom/run.py --output outputs/cooperative-python.json
```

```matlab
addpath('papers/cooperative-satcom');
run_cooperative_satcom('outputs/cooperative-matlab.json');
```

`fixture.json` is shared by both implementations. No language-specific random generator is used. JSON contains `paper_id`, numeric `metrics`, `checks`, and numeric `history`. Source files do not contact external services.

## Validation

The Python fixture passes analytic-vs-central-finite-difference gradients, an independently evaluated explicit-W SINR identity, unit modulus, transmit power, protected-GT interference, monotone phase-stage utility, and the fixed-share bisection bracket. Initial Python gradient maximum error: approximately `3.2e-10`. The fixture minimum SINRs are approximately 1.3571 (no RIS), 2.1581 (initial RIS), and 2.2462 (optimized core); these are **new fixture results**, not values from a published figure. Cross-language validation must be based on actual MATLAB execution, not merely source inspection.

Nothing here establishes a global optimum of the RIS problem. Cite the paper when using its model; see the repository rights policy. The public manuscript is linked, not redistributed.
