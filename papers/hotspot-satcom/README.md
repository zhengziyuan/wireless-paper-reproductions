# RIS-aided hotspot SatCom: independent RIS-design core

Paper: Z. Zheng et al., *RIS-Aided Hotspot Capacity Enhancement for Multibeam Satellite Systems*, IEEE TWC 23(4), 3648-3664, 2024. [DOI](https://doi.org/10.1109/TWC.2023.3309957). [Official publisher record](https://ieeexplore.ieee.org/document/10258030/).

**Status: executable independent core; final journal full-text verification pending.** The publisher abstract confirms the semi-orthogonal/pairwise-decorrelation manifold phase-design method. Detailed formulas were checked against the author's supplied doctoral-thesis Chapter 3, which identifies this exact paper/DOI. The final publisher paper/preprint was not accessible during implementation. Consequently **no final journal equation numbers or complete reproduction claim are made**. See `source_map.json`; verification must be completed before claiming final-paper formula-by-formula equivalence.

## Implemented scope

- Deterministic LoS channel instances, with one common RIS serving correlated hotspot users (HUs) and direct-only non-hotspot users (NHUs). Each HU effective row channel is `c_u = h_u^H + phi R_u`, with `R_u = diag(conj(r_u)) G`. The half-wavelength 1-by-N array responses and link amplitudes are explicit in the shared fixture. Amplitudes are normalized numerical test inputs, not original satellite link-budget inputs.
- The thesis-mapped two-stage RIS design criterion `F = f2 - f3`: `f2 = sum_u ||c_u A||^2`, `A = I - sum_k h_k h_k^H / ||h_k||^2`; `f3 = sum_(u>v) |c_u c_v^H|^2`. **A is a semi-orthogonal operator, not a substituted orthogonal projector**; when NHU channels are not orthogonal, it is generally not idempotent.
- Analytic derivatives of both criterion terms in phase coordinates, unit-circle tangent ascent, normalized retraction, Armijo backtracking, and independent central-finite-difference verification. This implements the substantive RIS phase-design stage without Manopt.
- The physical downlink SINR, HU sum rate, total power, and NHU QoS constraints. The three comparisons are optimized-RIS, initial-RIS, and no-RIS, all with the same subsequent precoder baseline.
- A **separately labelled baseline**: normalized zero-forcing directions, minimum NHU QoS power, and exact HU water filling for those fixed ZF directions. This is useful for evaluating the phase-design mechanism, but **it is not the paper's QT/SOCP second stage**. Its constrained fixed-direction allocation is solved, not the full joint satellite-precoding problem.

## Not implemented

The paper's satellite QT/SOCP updates, full AO/SDR with Gaussian randomization, finite-Rician statistical-CSI extensions, original 16-feed/16-user orbital deployment, aperture/link-budget sweep, Monte Carlo results, timing comparison with CVX, and original Figures 2-10. RIS-criterion monotonicity does not imply monotonicity or global optimality of the final sum rate. The ZF baseline can be infeasible for other channel/power fixtures; the program reports this rather than silently reducing NHU QoS targets.

## Run

Python 3.10+ and NumPy; MATLAB uses only base MATLAB (R2016b+). From the repository root:

```sh
python papers/hotspot-satcom/run.py --output outputs/hotspot-python.json
```

```matlab
addpath('papers/hotspot-satcom');
run_hotspot_satcom('outputs/hotspot-matlab.json');
```

Both implementations read `fixture.json`, use the same floating-point operations/loops, and do not use language-specific random generators. Output JSON contains `paper_id`, numeric `metrics`, `checks`, and numeric `history`.

## Validation

Python validation passes analytic gradient, independent received-signal SINR, ZF residual, RIS unit modulus, total power, NHU QoS, and monotone criterion checks. Initial Python gradient maximum error is approximately `7.8e-10`; ZF residual is approximately `4e-16`. In this **new normalized fixture**, the RIS criterion improves from approximately -0.4417 to 2.6127. HU sum rates with the explicitly labelled ZF baseline are approximately 5.6378 (no RIS), 5.8104 (initial RIS), and 10.8731 bit/s/Hz (optimized RIS). These numbers do not reproduce published curves and must not be compared as identical simulation settings.

Cross-language agreement requires actual MATLAB execution. Public code visibility does not itself grant an open-source license; see the repository policy. No private manuscript, original data, or publisher PDF is redistributed.
