# Two actual native recording-v4 full cases

These are actual MATLAB M30 and N48 complete eight-scheme cases, not a mock,
Python simulation relabeled as MATLAB, or a full 183-point bank. Every complete
saved final matrix, phase-stage context, QT input/candidate, and all original
1000 actual **channel-moment** draws are preserved in byte-exact MAT-v7.3 files.
Independent matrix/scalar-gradient/QT checks and a separate native bitwise RNG
replay have actually passed for these cases. Actual source, input and selected
backend intervals and output SHA bindings are preserved.

The `.states.mat` files accompany the original `.json` result stems. Keep their
names together. Source snapshots under `executed-sources` are byte-exact; they
are not newly optimized results or standalone installed production entries.

Install the existing repository reproduction requirements plus
`requirements-state-audit.txt`, then from this folder run:

```text
python audit_native_recorded_fullcase.py recording-v4-M30-actual-matlab-v1.json recording-v4-M30-actual-matlab-v1-runtime.json M30-configuration.json NEW-M30-readonly-audit.json --native-rng-replay recording-v4-M30-actual-matlab-v1-rng-replay.json
```

Replace M30 with N48 for the second case. This adapter only changes module path
resolution to copied frozen sources/current repository science. It does not
change any numerical function body or rerun an optimizer. A public-path replay
is a distinct receipt and is **not** presumed executed by this freeze operation.
The recorded native RNG proof does not claim Python generates MATLAB draws.

Still false: complete formal183 execution, all-QT-dual/final-gradient MP80
certification, 1000 optimized performance samples, recovery of the author's
historical geometry, publisher conformance and original-figure agreement.
Existing v2/v3/Python evidence and all failures remain unchanged.

The initially prepared v1 HDF5 decoder failed before matrix/gradient/QT audit:
it mistook a direct class=cell dataset in a scalar MATLAB struct for a struct
array field. Its original sources and actual failure reproduction are retained.
The new reader adds only that MATLAB-class distinction. The new auditor changes
only reader import/source routing; its full numerical body reverses byte-for-byte
to v1. The real native schema and separate synthetic direct-cell row/column
regression checks passed before the actual numerical v2 audits. A decoder-only
test is not itself a numerical certificate.

The N48 v2 auditor separately failed before numerical checks because MATLAB
serialized the original single-satellite latitude list [1.25] as scalar 1.25.
V3 accepts only that predeclared field conversion when J==1, the source list
has one element, and the scalar is exactly equal. All other configuration
fields must match exactly. Source configuration bytes/SHA and mathematical
array dimensions are unchanged; no generic array flattening or tolerance was
introduced. The metadata-only proof and old v2 source are preserved. Both
actual native cases were independently audited with the same final v3 source.
