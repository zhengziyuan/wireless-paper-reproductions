# Complete paired power curves and a remaining physical-input mismatch

Both languages have the complete two configured power sweeps: all11 abscissas
`2**arange(0,5.01,0.5)` at kappa_L20 dB and all13 abscissas through64 W at
kappa_L0 dB, with all8 original schemes and full J3/U2/N16/M25 dimensions.
These are actual saved numerical returns. The source case index restores their
original curve labels; raw result files retain the dispatcher's `base` label.
No optimizer or random realization was repeated to create this packet.

The archive contains **all384 actual final states** (24 cases x8 schemes x2
languages), their11 physical input arrays, constraints, returned metrics,
four full curve PNG/SVG/JSON sets, complete source/audit bindings, independent
MP80/MP100 final-physics reports and the unfitted original-reference comparison.
Every one of3072 physical field coordinates per precision passes the unchanged
`1e-9+1e-10*abs(reference)` comparison. All original physical bounds and phase
domains pass. The maximum cross-precision difference is1.4432e-79.

The192 separately optimized MATLAB/Python minimum-SINR pairs differ by at most
0.0003274557 in linear SINR,0.000116419 relative to Python, or0.000505571 dB.
The11 paired input arrays have matching shapes and relative Frobenius errors
at most5.2289e-14. They are not bitwise identical. Only13/192 optimized pairs
meet the much tighter same-state field tolerance; no solution-equality gate
is relaxed or declared passed. Both convex backends and phase paths can differ.

These curves **do not reproduce the supplied author figures**. All88+104
original EPS ordinates per language are paired without interpolation, gain
fitting or rescaling. The maximum linear-SINR gaps are31.1269814 for source
Fig4-2 and14.1377065 for Fig4-3. The source file hashes, verified linear axes,
all eight legend colors, and complete vector paths are retained. Each EPS path
contains one constant-y extension0.066 coordinate units beyond the clipped
right axis; that drawing extension is retained explicitly and is not counted
as an additional measurement. Private EPS/manuscript files are not distributed.

An independent bound shows why solver changes alone cannot close this gap.
Let `I` be the one shared GT limit, `n_u` useful received power and `o_u` the
noise-plus-GEO offset. If `B_u` bounds useful power divided by GT leakage for
every satellite serving user u, then `sum_u n_u/B_u <= I`. Every feasible
minimum SINR t must therefore obey

```text
t <= I / sum_u(o_u/B_u).
```

For AP, `B_u=max_j m_ju^H T_j^-1 m_ju` by generalized Cauchy-Schwarz.
Statistical MR uses `||m_ju||^4/(m_ju^H T_j m_ju)`; TTS MR uses
`(||m_ju||^2+tr C_ju)^2/tr[T_j(C_ju+m_ju m_ju^H)]`. The diagnostic verifies
positive-definite GT second moments and nonnegative variances. It removes
all satellite power constraints and all nonnegative intra-system interference,
so it gives an upper bound even for a stronger optimizer on these same inputs.

| Fixed input | AP-NoRIS bound | MR-S-NoRIS bound | MR-TTS-NoRIS bound |
|---|---:|---:|---:|
| kappa_L20 dB |0.298940480|0.265886880|0.270959000|
| kappa_L0 dB |0.267099392|0.242051795|0.819751502|

MP80/MP100 evaluate these bounds with a maximum difference4.1581e-78.
All actual saved NoRIS results lie below the bound, while52/72 original NoRIS
ordinates per language exceed it even after accounting for EPS rounding.
This identifies a mismatch between the **declared reconstructed inputs** and
the author's unrecovered numerical inputs. It is not an error proof against
the author paper under its original inputs. Receive gains, multibeam patterns,
GT diameter, array orientation and historical initialization remain explicitly
unreported or unverified; no one of them is claimed as the unique cause.

The native24 cases also retain all phase-stop/QT checks at MP80/100 and the
configured1000-draw physical moment replay, with per-case report hashes in this
packet. Exact shared inputs reuse two moment streams; these are not24000
independent optimized performance trials. Complete phase/QT tapes for these24
cases remain in the local numerical archive; this compact public archive
contains the complete final-state population. The public case000 tape remains
available separately. Historical Python MP whole-case false flags are unchanged.
Full183 execution, full historical trajectories, final-publisher equivalence,
original-reference agreement and complete paper reproduction remain open.

Restore and independently inspect all public final states:

```powershell
python tools/cooperative-stable-replay/unpack_power_evidence.py --packet strict/validation/cooperative-power24-dual-final-states-20261017 --output-dir strict/outputs/power24
python tools/cooperative-stable-replay/audit_power_curve_states_mp.py --directory strict/outputs/power24 --output strict/outputs/power24-MP80-MP100.json
python tools/cooperative-stable-replay/audit_no_ris_input_bound.py --directory strict/outputs/power24 --reference-directory strict/outputs/power24/reference-comparison --output strict/outputs/power24-NoRIS-bound.json
python tools/cooperative-stable-replay/compare_power_references.py --reference-directory strict/outputs/power24/reference-comparison --curve-directory strict/outputs/power24 --output-dir strict/outputs/power24-unfitted-reference
```

The reader requires NumPy, SciPy and mpmath; rendering additionally uses
Matplotlib. CI repeats the public final-state physics, bound and whole-grid
reference comparison without MATLAB, private EPS or a new optimization run.
The full archive SHA256 is
`e308bd15f3000192f90a62f5b622c4e4ce3146f44b3a1ffd9a901e93288f8b0d`.
