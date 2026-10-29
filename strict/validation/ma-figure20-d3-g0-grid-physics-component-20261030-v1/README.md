# Figure 20: one saved-grid Python physical component

This capsule records one **partial** reconstruction: Figure 20, grid size
`D=3`, geometry index 0, six antennas and five users. The previously saved
MRT and ZF statistical-objective grid winners were evaluated on the same
1,000 saved channel draws per mode. The author’s historical grid-selection
criterion is not known; the theoretical selection criterion is a disclosed
reconstruction choice. No optimization, search or random sampling was rerun
to produce this component.

The recorded original Python mean sum rates are 11.069791030425774 bit/s/Hz
for MRT and 27.74154626200885 bit/s/Hz for ZF. The independently implemented
channel/rate check used scalar user-rate calculations and QR-based ZF in place
of the original normal-equation route. Across all draws, the largest absolute
rate differences were approximately 1.60e-14 and 3.20e-14 bit/s/Hz,
respectively; the ZF maximum relative Frobenius off-diagonal residual was
5.53e-16. This is an independent implementation route on the **same NumPy
runtime and same saved draws**, not independent arithmetic precision or an
independent random experiment.

The audit used the following numerical gates: rate agreement
`1e-9 + 1e-10*abs(saved_rate)`, total-power error
`1e-12*max(1,power)`, absolute off-diagonal agreement
`1e-13 + 1e-9*abs(saved_amplitude)`, relative ZF Frobenius residual at most
`1e-10`, channel smallest/largest singular-value ratio above `1e-12`, and
spatial tolerance `1e-6`. These are stated verification tolerances, not
recovered historical author parameters. The recorded power budget is 1 W.

`evidence.json` contains the actual 1,000 saved rates, powers and maximum
absolute off-diagonal amplitudes for each mode, the positions and indices,
the independent audit's summary and the thresholds. Local source and input
digests identify the unredacted original artifacts; they are **not** hashes of
the sanitized projection. The original 1,000-channel input bank is not
included. Consequently these files allow inspection of the recorded outputs,
but do not by themselves reproduce the channel or independently recompute the
QR audit. `verify_evidence.py` performs only integrity and elementary
consistency checks on this public projection; it is not a physics, optimizer or
paper acceptance test.

The complete point, MA optimization, FPA independent physics, convergence,
independent MATLAB execution, dual-language agreement, original-figure
reference and the full figure or paper remain unverified by this capsule. A
component pass does not constitute a reproduction of the published figure.
