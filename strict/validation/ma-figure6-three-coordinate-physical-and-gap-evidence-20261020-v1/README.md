# MA Figure 6: three coordinate exceptions, physical coefficients and gap evidence

This supplement contains six new source-bound single-coordinate captures from
three common saved prestates. It separates a different stepwise floating-point
path from a mathematical failure of the original coordinate subproblem.

Both language lanes meet their own original saved gap and feasibility tolerances
at MP80 and MP100. The independent physical derivation also satisfies the existing
`1e-9` objective-before and tangent/direct-gradient numerical consistency checks.
This is not a claim that every coefficient, curvature, historical path, or original
reference passed a new gate. Coefficient and curvature errors are diagnostics.

| Saved coordinate | Python gap | Native gap | Original gap tolerance (approximately) |
|---|---:|---:|---:|
| 006/024 MRT | 0 | 0 | 1.089e-9 |
| 006/027 ZF | 3.031e-16 | 2.570e-16 | 1.237e-9 |
| 008/024 MRT | 4.285e-16 | 3.242e-19 | 1.114e-9 |

The largest exact-halfspace primal residual is about `8.85e-21`, within the
original `6–7e-12` tolerance. A small positive residual is not relabelled exact
feasibility. Each original tie set has one member; the saved distinct candidate
values are not near tied under the original8eps window. Candidate list ordering
differs, so a same-index candidate position difference is not a causal diagnosis.

The physical reader distinguishes the actual captured binary64 direction/beta
fields from a common original-angle/distance MP reference. It uses the source
literal `1e-4` and `-2.8` as exact promoted binary64 values, and mathematical pi.
MRT curvature retains `equation_29a_max_eigenvalue`. The ZF theoretical Hermitian
matrix is not confused with Python's stored lower-triangle eigenvalue convention
or native's explicit Hermitian average. Both conventions and actual stored
anti-Hermitian residuals remain visible in the reports.

The three old historical stepwise bit-equality flags remain false; this alone
does not mean a dual-language mathematical error or create an extra permanent
numerical-acceptance requirement. New captures do not recover historical internal
operands or runtime. Existing original-reference EPS discrepancies remain; this
supplement does not certify an original curve, all900 histories, or the full paper.

## Contents and provenance

`CAPTURE_INVENTORY.json` locates the six typed captures, stored once each, the
three source-bound fixtures, and their actual original closed journals.
`evidence/` contains the complete actual MP reports and compact scope closures.
Large JSON files use lossless gzip. `NUMERIC_PROJECTION.json` records metadata-only
path projection: every JSON numeric token/nonpath numeric string is retained;
native MAT character fields are replaced at equal width while every numeric
dtype, shape and Fortran-order byte digest is unchanged. Original NPZ bytes and
all published numerical source bytes are exact copies. Public projection hashes
and original artifact hashes are deliberately separate.

The V2 fixed-coefficient reader genuinely returned1 at final JSON serialization:
a cross-language diagnostic difference divided by the ULP at zero overflowed a
binary64 display value. Its partial files remain in the source evidence archive;
their sizes/hashes and true failure are recorded here. V3 changed only JSON
representation/output handling, then completed naturally0. No failed result is
silently promoted or deleted.

## Read or recheck saved evidence

From this directory, inspect file integrity and recorded scope without NumPy/MP:

```text
python replay_saved_evidence_v1.py --stage inspect
```

With NumPy, SciPy and mpmath installed, explicitly repeat either saved-only check
into a fresh output directory:

```text
python replay_saved_evidence_v1.py --stage fixed-coeff --output-dir ./fresh-fixed-check
python replay_saved_evidence_v1.py --stage physical-coeff --output-dir ./fresh-physical-check
```

The wrapper materializes metadata-projected inputs, verifies their digests, and
calls the unchanged published audit numerical functions. It does not fabricate
new historical authorization/lifecycle receipts and does not call production
coordinate solvers, optimizers, root solvers, MC or RNG. Exit0 means only the
selected original check scope; exit2 retains a scientific check failure and
host/input exceptions remain failures. The `inspect` mode completed once with natural exit0 on the original49-file
public layout, with empty stderr and all watched bytes unchanged. Its actual
receipt binds the tested source and original manifest. The fixed-coefficient and
physical-coefficient numerical modes have not been rerun in the public relative
layout. The replay source header's first-use-pending statement refers to those
numerical modes. The original MP executions above completed in their recorded
source layout.

This final capsule changes only this documentation, `SCOPE.json`, the manifest,
and the added compact inspect receipt. All numerical inputs, numerical sources,
and existing evidence reports are byte-identical to that inspected capsule.
The metadata-only final layout was not inspected again and no MP was repeated.

See `SCOPE.json`, `SOURCE_PROVENANCE.json`, `MANIFEST.json`, and both detailed MP
reports for the precise boundary. The capture-generation providers are included
for source inspection; direct provider invocation is not the public replay entry.
