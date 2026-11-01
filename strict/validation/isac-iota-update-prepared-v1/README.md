# Prepared ISAC scaling update helper

This isolated Python helper implements the exact scaling update in Eq. (23)
or the practical denominator safeguard described immediately afterward in
[arXiv v2](https://arxiv.org/html/2512.20987v2#S2.SS4). It is not connected
to the solver and does not run an optimization, generate channels, or claim
that the paper's overall algorithm converged. The paper does not give a
numerical value for the positive epsilon; callers must supply one explicitly
and state its provenance. The helper does not verify that provenance.

At a fixed nonnegative beampattern and template it records both the actual
previous-iota and updated-iota NMSE, with the observed direction of change.
It never asserts that the safeguarded step is monotone. Zero desired energy,
zero beampattern energy, invalid values and detected numerical overflows or
underflows return a structured failure instead of a score. Floating-point
rounding can make a positive epsilon disappear when added to a larger overlap;
this is reported. This tool does not resolve all conditioning or rounding
issues, validate inputs against physical channels, or preserve an AO trajectory.
NMSE values and comparison directions are binary64 results: an observed equality
does not prove exact equality when a difference is below rounding precision.
When the pattern is identically zero and the desired pattern has positive energy,
NMSE is exactly 1 for every positive iota. The helper's `zero_pattern_energy`
failure is a conservative refusal to choose an update, not a claim that no
finite minimizer exists.

Run only the self-contained toy cases with `python -B test_iota_update.py`.
The tests are algorithm component checks, not scientific acceptance. The
frozen production Python and MATLAB implementations remain untouched and
require corresponding independent changes and cross-language verification.
A MATLAB counterpart is being prepared separately; MATLAB execution and cross-language agreement remain unverified.
