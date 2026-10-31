# MA Figure 6: trajectory exceptions versus the source-curve gaps

All 900 existing Python/MATLAB pairs and their prior independent own-state
mathematical checks are described in [the saved-population packet](../../strict/validation/ma6-all900-saved-science-20261020-v1/README.md). Three intermediate
trajectory comparisons remain outside the fixed path gates. This note compares
those three saved terminal results with their contribution to the corresponding
100-geometry curve points, and with the previously extracted author-R2 curve.
No optimization, random sampling, MATLAB execution, or complete population
replay was repeated.

| Power / geometry / scheme | First failing saved sweep boundary (zero-based) | Python minus MATLAB terminal mean | Contribution to 100-geometry mean difference | Python figure mean minus supplied source |
| --- | ---: | ---: | ---: | ---: |
| 27 dBm / 24 / MA-MRT | 50 | -2.21085e-11 | -2.21085e-13 | -1.3632944 |
| 27 dBm / 27 / MA-ZF | 345 | +4.85450e-10 | +4.85450e-12 | -2.4021306 |
| 33 dBm / 24 / MA-MRT | 58 | -2.94520e-12 | -2.94520e-14 | -1.4736681 |

Units for rates are bit/s/Hz. Each failure is at a sweep boundary where the
absolute saved design-objective difference first exceeds the existing 1e-9
gate; the three maximum position differences there are approximately
2.043e-10, 2.596e-10 and 1.219e-10 wavelength. Every saved terminal passes
both languages' own nominal and realized spacing/box checks; the complete
independent saved-state checks are a separate earlier result. Minima shown in
the JSON are direct binary64 measurements, not exact-real certificates.

The small direct contributions cannot explain the much larger *observed*
source gaps as a Python/MATLAB return discrepancy. They do not bound the
unknown consequences of changing model parameters, solving a different
problem or using the author's unrecovered random ensemble. In the 45 existing
Python/source comparisons, MA-ZF and MA-MRT are each below all nine source
points; FPA-MRT and FPA-OPT are above all nine, and FPA-ZF is above eight.
Thus the current discrepancy is not just a uniform signed shift across all
schemes. This observation does not identify its cause or certify any figure.

The [author manuscript R2](https://arxiv.org/html/2410.05912v2) specifies path-loss, noise, distance/angle ranges and κ=6 for
Fig. 6. The saved job uses these stated numerical conventions. The author's
actual random draws, MA starting positions, N_r/N_c factorization and FPA
layout are not recovered. The present 2×3 half-wavelength FPA layout is a
reconstruction choice; seeking original author inputs/code is justified,
whereas adjusting those choices to fit the plotted curves would not verify
the original experiment. Publisher-final equivalence is unverified.

The source vectors and the 45 point-by-point gaps come from the existing
[original-reference packet](../../strict/validation/MA6-closed900-original-reference-20261017/README.md).
The three detailed observations are in the adjacent redacted JSON. The
original 1e-9 trajectory failures, author-reference mismatch, and all wider
paper gates remain open.
