# MA source semantics and exact theory counterexamples

This is a source/theory audit, not a new simulation, paper-wide PASS, official
publisher erratum, or explanation of a figure discrepancy. The supplied R2
source SHA256 is `9ba173a0da8fcd472bb211155e0a4c1e7b9a0104a718bd88ac166808be876b19`.
Private manuscript files are not redistributed.

## Confirmed source issues

Remark 4 (R2 lines 601–604) identifies the inverse removed-row matrix with the
complete FPA inverse matrix. That equality is false in general. Choose N=2,
M=1, kappa=1, and two unit-modulus LoS entries. The complete matrix Sigma is 1,
the removed-row Theta is 3/4, and their inverses are respectively 1 and 4/3.
Every FPA placement has the same single-user complete Gram and inverse 1.
The Woodbury subtraction is exactly 1/3, recovering the correct complete
inverse; removing a row is not placing an antenna at its fixed position.
At kappa=0 the distinction vanishes, which the negative control also checks.

Equation (29b) (R2 line 431) prints a minus before 4*b^2 under the square root
of the symmetric 2-by-2 maximum eigenvalue formula. The characteristic
polynomial requires a plus. For the positive-semidefinite all-ones matrix,
the printed radicand is -4 and the correct eigenvalues are 0 and 2. This sign
issue was already disclosed in the full configuration; the implementation
uses the stated Eq. (29a) maximum eigenvalue, not the undefined printed root.

Neither issue has been silently used to change a simulation. Both engines
already form the removed-row Theta separately. The invalid FPA equality is
not used by the implemented algorithm, and neither source issue is an
established cause of the Fig. 3/4 reference differences.

## Normalization and metric distinctions

The source audit did not find a new definite MRT/ZF normalization or power-unit
implementation mismatch. MRT uses the instantaneous common coefficient
P/||H||F^2, not equal P/M per-user physical power. ZF normalizes each column
and uses P/M. -80 dBm is 10^-11 W; -40 dB path-loss gain is 10^-4.
Both implementations keep the statistical design objective separate from
the mean of the actual per-draw log2(1+SINR) rates. Eq. (13) is a
ratio-of-expectations approximation, not a general lower bound on actual rate;
Eq. (37) is the specified ZF design lower-bound expression.

Unreported historical geometries, samples, seeds, rectangular factorization,
initialization and solver precision remain qualified reconstruction choices.
In particular, independent uniform elevation/azimuth produce unequal
direction-component second moments (1/4 and 1/2); transposing an unspecified
rectangular arrangement cannot be assumed statistically irrelevant. This is
not a fitted geometry or a demonstrated cause of a reference difference.

## Runnable exact controls

From the repository root, using ordinary Python with no third-party packages:

```sh
python -B strict/validation/two-timescale-ma-source-semantic-v1/verify_theory_errata.py
```

All seven portable exact-rational controls actually passed with exit 0 on
5 October 2026. Their complete mathematical bodies are copied unchanged from
the separately completed eight-control local source audit; its machine-local
private-file pin control and receipt writer are intentionally not distributed.
ROOT also actually reran all eight local controls successfully. This is exact
algebra and source semantics, not MATLAB execution, a full Monte Carlo run,
global optimality, or agreement with the published curves.

The local complete eight-control source receipt SHA256 is
`6a21aa73b016015295d508b922e8814b9f791451c5631452ff5a5d8c0400a8b9`.
Whole original source bytes remained unchanged in that audit. Full six-paper
reproduction and the reference-gap root cause remain incomplete.
