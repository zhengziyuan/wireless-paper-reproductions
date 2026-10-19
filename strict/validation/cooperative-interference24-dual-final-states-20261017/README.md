# Complete interference curves, a retained language outlier, and source gaps

Both languages have all 24 original interference-sweep slots: case024–035 at
kappa_L20 dB and case036–047 at kappa_L0 dB, each with the complete grid
0.01,0.02,…,0.12 and all eight schemes. Dimensions remain J3/U2/N16/M25,
transmit power50 W, and the configured moment-validation count1000. These
are saved full-case numerical executions, with original failures preserved.
The packet restores the source axes from the exact183-case index and verifies
every stored numeric power/interference bound. Raw dispatcher metadata still
says `base`, `power_w`,50; those raw fields are retained alongside derived axes.

The public archive includes all384 actual final states, all11 physical input
arrays, original bounds, all four complete curve PNG/SVG/JSON sets, source and
audit bindings, original-vector reference values and independent reports.
All3072 scalar physical field coordinates per precision pass MP80/MP100 with
the unchanged `1e-9+1e-10*abs(reference)` tolerance. Original physical bounds
and unit-modulus domains also pass. Maximum precision difference is3.465e-79.
No optimizer or random draw was repeated to assemble these24 full-case curves.

One language difference remains visible. At case047,INR0.12,kappa_L0 dB,
MR-TTS-TS returns minimum SINR9.41420494396 in Python and4.43927746234 in
MATLAB: an absolute gap4.97492748161, or3.264713585 dB. The other191 pairs
differ by at most0.000913892271 linear SINR or0.00143770001 dB. All input
shapes match; the maximum paired relative Frobenius input error is5.229e-14.
Only14/192 optimized pairs pass the diagnostic same-state field tolerance.
Independent optimized-solution equality is not certified.

The outlier is traced to the first MR-TTS phase call at mu1. The initial
phase is bitwise identical; the preceding NoRIS powers differ by a relative
norm5.55484e-5 (maximum absolute coordinate difference4.20981e-6). The actual
first-phase endpoints have criteria13.9603068209 and4.38103785808. Independent
MP80/MP100 checks all50 complex gradient coordinates at both endpoints under
both fixed contexts and at the common initial phase. Each original endpoint
passes its own strict1e-6 norm stop. At either common fixed context, the
Python endpoint's objective is about9.579 higher than the MATLAB endpoint's.
This is evidence about two stationary points, not a global-optimum certificate
or a Hessian classification.

Two **new isolated first-phase controls** test this sensitivity. Both use the
same native channel arrays, native interference bound, initial phase, mu1,
Python positive-Wick evaluator, RGD direction, Armijo rule and alternating
BB controls. Only the saved fixed-power array changes. The original configured
100000 cap and strict1e-6 gradient stop remain; the cap and step-seed controls
are explicitly unreported numerical controls, not claimed published budgets.
The controls return13.9603068211 after1137 iterations and4.38103784110 after
4278 iterations. MP80/MP100 norms are7.20988e-7 and9.98511e-7, and all actual
gradient fields pass. Thus changing p0 alone is sufficient to reproduce the
high/low first-phase outcome under one implementation. This does not establish
a unique explanation for every full-chain difference. These are two phase
calls with no convex solve or Monte Carlo draws; no full-case curve value is
replaced. Both complete new phase histories and actual states are included.

The curves still **do not reproduce the author references**. All192 original
ordinates per language are paired without fitting, interpolation or rescaling.
Maximum linear-SINR gaps are39.0963858 for source Fig4-4 and18.7502248 for
Fig4-5. Each original curve has12 in-axis vector points and no clipping tail.
The verified plot rectangles are[48,10,606,431] and[56,10,606,429], with
vertical ranges0–14 and0–4.5. Original private EPS files are not distributed.

There is also an unresolved **horizontal-unit conflict**: the original EPS
labels the interference threshold in W and annotates I/N=-12.2dB, whereas
the supplied implementation varies noise-normalized I/N on the same scalar
grid. Whole-grid pairing alone does not prove unit conformance. An independent
NoRIS relaxation, `t <= I/sum_u(offset_u/max_j B_ju)`, checks positive-definite
GT second moments at MP80/MP100 and removes transmit-power constraints and
nonnegative intra-system interference. All actual NoRIS results obey it. If
the two scalar grids are identified as the same normalized input, all72
original NoRIS ordinates per language exceed this fixed-input bound, even
after EPS rounding. This conditional incompatibility cannot be removed by
improving an optimizer on the current inputs. It is not proof that the author's
unrecovered W-domain inputs or paper violate the bound. Missing gains, patterns,
geometry and normalization remain unresolved; none is fitted to the figures.

Native per-case phase/QT high-precision reports and the configured1000-draw
moment checks are bound by hashes. The24 cases share two exact channel-input
groups for moment-stream reuse, not24000 independent optimized performance
realizations. Complete original24 phase/QT tapes remain in the external local
archive. This compact public packet includes every final state and the actual
first-stage diagnostic witnesses, not every original inner trajectory. Old
Python whole-case MP false flags, original curve gaps and the outlier remain.
Full183 execution, historical publisher-input recovery, original-reference
agreement and complete paper reproduction are unfinished.

Restore the packet and replay its independent checks without optimization:

```powershell
python tools/cooperative-stable-replay/unpack_power_evidence.py --packet strict/validation/cooperative-interference24-dual-final-states-20261017 --output-dir strict/outputs/interference24
python tools/cooperative-stable-replay/audit_power_curve_states_mp.py --directory strict/outputs/interference24 --output strict/outputs/interference24-final-MP80-MP100.json
python tools/cooperative-stable-replay/audit_no_ris_input_bound.py --directory strict/outputs/interference24 --reference-directory strict/outputs/interference24/reference-comparison --output strict/outputs/interference24-bound.json
python tools/cooperative-stable-replay/compare_power_references.py --case-scope interference --reference-directory strict/outputs/interference24/reference-comparison --curve-directory strict/outputs/interference24 --output-dir strict/outputs/interference24-reference
python tools/cooperative-stable-replay/audit_phase_divergence.py audit --directory strict/outputs/interference24/case047-phase-witness --output strict/outputs/interference24-phase-cross.json
python tools/cooperative-stable-replay/run_fixed_phase_control.py audit --directory strict/outputs/interference24/case047-same-native-data-phase-controls --output strict/outputs/interference24-phase-controls.json
```

The legacy `power` tool names retain backward-compatible defaults. The source
cohort, all24 original ordinals and all eight schemes are checked during
restoration. NumPy,SciPy and mpmath are required; Matplotlib additionally renders
figures. Public CI replays the saved states and phase controls, not new optimizers.
The archive has38 payloads in four512KiB-or-smaller parts and SHA256
`0388bbebed1873d089280c0bdf462f26c0493ea3924ee1fa112f6ae9dd0a7513`.
