# Complete paired RIS-size sweeps: verified final physics, unresolved source curves

The packet contains all **18 original source slots**: M=5,10,...,45 for
kappa_L=20 dB (ordinals48–56) and kappa_L=0 dB (ordinals57–65), with all eight
schemes in both Python and MATLAB. J=3,U=2,N=16,K=1 remain fixed. These are
author-thesis Chapter4 figures4-6 and4-7; conformance to the final publisher
version and recovery of the author's hidden channel inputs remain unverified.

The Python selection uses16 completed historical returns and the two separately
completed corrected full executions for056/065. Those new epochs use the exact
old11 physical coefficient arrays, original configurations and bounds, and the
same configured1000 moment returns. Their complete phase/QT MP80/MP100 evidence
was already published in the [two-control packet](../cooperative-corrected-python056-065-20261017/README.md).
The old failed float-auditor flags and all old receipts stay unchanged. Selection
is explicit in every source binding; no failed original slot disappears from the
curve. The plain published two-control JSON has CRLF text newlines whereas its
original archive payload has LF. Both byte forms are retained and checked; only
that exact text conversion is admitted, with no numerical or flag changes.

All **288 actual final states** pass independent MP80 and MP100 evaluation of
SINR, denominators, satellite powers, GT interference, original primal bounds
and phase domains. Each precision checks2304 physical field coordinates;
maximum MP80/MP100 difference is2.264e-78. The existing field policy remains
1e-9+1e-10*abs(reference), physical constraint tolerance1e-5 and phase-domain
tolerance1e-10. Native complete phase-stop/QT checks and each configured1000-draw
moment stream are separately bound to their actual receipts. This compact
packet includes every final state, not every inner trajectory or raw moment
draw. The1000 moment-validation draws and configured solver caps are disclosed
reconstruction controls, not recovered author-reported performance-MC budgets.

All144 independently optimized MATLAB/Python minimum-SINR pairs are retained.
Maximum linear-SINR gap is0.00131553603 (relative0.000263470271 and0.00114408614 dB).
No common-state evaluator tolerance is relaxed into a solution-equality claim.
The two implementations use different convex backends and may reach different
stationary points; these small observed gaps do not prove a unique optimum.

The curves **do not reproduce the original references**. All144 source vector
ordinates per language are paired without fitting, interpolation or rescaling.
Maximum linear-SINR gaps are70.6197958 for figure4-6 and23.7347603 for4-7.
Both original panels have nine in-axis points per curve and no clipping tail.
Their visually checked plot rectangles are[50,10,615,429] and[55,10,615,429].
Their vertical ranges are **2–11 and1–5**, respectively; preserving those
nonzero lower endpoints is essential when decoding the EPS coordinates.
The abscissa is the RIS subsurface count; there is no W-versus-normalized-INR
abscissa conflict in these two panels. Private author EPS files are not included.

An independent NoRIS relaxation removes all satellite-power constraints and all
nonnegative intra-system interference. Its bound is
`t <= I / sum_u(offset_u / max_j B_ju)`, with positive-definite GT second moments
checked at MP80/MP100. All actual NoRIS solutions obey the bound. **All54 source
NoRIS ordinates per language exceed this bound on the current fixed inputs**,
even after the original EPS coordinate-rounding allowance. Thus improving an
optimizer on these fixed inputs cannot recover those source ordinates. This is
a conditional incompatibility with the present reconstruction inputs, not proof
of an error in the author's unrecovered physical inputs or paper. Geometry,
antenna patterns, gains and normalization remain unresolved; none is fitted to
the reference curves.

Restore and replay the actual public data without a new optimization:

```powershell
python tools/cooperative-stable-replay/unpack_power_evidence.py --packet strict/validation/cooperative-subsurfaces18-dual-final-states-20261017 --output-dir strict/outputs/subsurfaces18
python tools/cooperative-stable-replay/audit_power_curve_states_mp.py --directory strict/outputs/subsurfaces18 --output strict/outputs/subsurfaces18-final-MP80-MP100.json
python tools/cooperative-stable-replay/audit_no_ris_input_bound.py --directory strict/outputs/subsurfaces18 --reference-directory strict/outputs/subsurfaces18/reference-comparison --output strict/outputs/subsurfaces18-bound.json
python tools/cooperative-stable-replay/compare_power_references.py --case-scope subsurfaces --reference-directory strict/outputs/subsurfaces18/reference-comparison --curve-directory strict/outputs/subsurfaces18 --output-dir strict/outputs/subsurfaces18-reference
```

The legacy power-tool names retain their original default cohorts. Restoration
requires all18 exact ordinals, both languages and all eight schemes. NumPy,
SciPy and mpmath are needed for numerical replay; Matplotlib additionally renders
figures. CI checks saved states and does not repeat these optimizations.
The lossless archive contains28 payloads in five512KiB-or-smaller parts,
2,549,097 bytes, SHA256
`0d652bb08da89d24211f4dac9f9da5ebcd5b9d3bee7fb2b4d9753a1677111da0`.
Full183 execution, original-reference agreement and complete paper reproduction
remain unfinished.
