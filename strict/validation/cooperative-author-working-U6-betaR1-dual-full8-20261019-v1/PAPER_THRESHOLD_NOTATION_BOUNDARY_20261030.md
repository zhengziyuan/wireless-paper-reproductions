# Cooperative multi-satellite paper: interference-threshold notation boundary

This note compares the final publisher version of *Cooperative Multi-Satellite
and Multi-RIS Beamforming: Enhancing LEO SatCom and Mitigating LEO-GEO
Intersystem Interference* (DOI: 10.1109/JSAC.2024.3460068), pages 283, 290
and 291. It does not identify the historical plot-generation parameters.

On page 283, equation (7) bounds the sum of expected received interference
powers by `varsigma_k`; the equation does not divide that sum by noise power.
Equation (6) places received interference and `sigma_k^2` in the same
SINR denominator. On page 290, the simulation description writes the same
threshold symbol as `varsigma_k <= 12.2 dB` without explicitly defining a
normalization or logarithm. On page 291, Figure 4 labels its horizontal axis
`varsigma (W)` and marks an ITU value using `I/N = -12.2 dB`.

These statements mix the notation of a linear power threshold with a dB
quantity without defining the conversion. They leave the numerical connection
between the page 290 statement, equation (7) and the plotted reference unclear.
The two printed dB numbers alone do not establish a logical contradiction or
identify a correction to the page 290 value.

If, conditionally, `I` denotes the same average interference power as the
left-hand side of equation (7), `N` is the corresponding noise power in watts,
and the intended constraint is `10 log10(I/N) <= -12.2 dB`, then the equivalent
linear bound is `I <= N * 10^(-12.2/10)` watts. The multiplier is approximately
0.06025596. This is a conditional conversion, not evidence of the actual
publisher-figure normalization or the intent of the page 290 sentence.

For the separately supplied working script's noise reference
`N = k_B * 100 MHz * 235.3 K = 3.248667097e-13 W`, the conditional bound is
approximately `1.9575155e-14 W`. The paper's table and the working script use
different stated noise references; neither is silently substituted for the
other. See [the existing axis and saved-means evidence](FIG4_FIG5_AXIS_AND_SAVED_MEANS_EVIDENCE_20261030.md)
for the script derivation and its limitations. No full-figure agreement, physical
feasibility, optimizer convergence or full-paper acceptance follows from this
notation check.
