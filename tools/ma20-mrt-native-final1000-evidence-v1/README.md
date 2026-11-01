# MATLAB re-evaluation at one saved MRT layout

This record concerns one Fig. 20 scenario only: D = 3, geometry 0, six
antennas, five users, Rician factor 100, and transmit power 1. MATLAB R2025b
evaluated the saved Python AO terminal layout on all 1000 held NLoS samples.
The compressed evidence contains every MATLAB rate, transmit power and maximum
off-diagonal amplitude, and the corresponding 1000 saved Python values. Both
series use their original sample order. It also retains the six coordinates,
means, a sanitized actual guard outcome and comparison. It does not duplicate
the large saved channel bank. The off-diagonal quantity is an absolute complex
amplitude, not a normalized residual.

For these retained samples, MATLAB and the earlier Python record have mean
sum rates 16.132825560362377 and 16.132825560362374 bit/s/Hz; the maximum
absolute per-sample rate difference is 1.7763568394002505e-14. The maximum
MATLAB transmit power is 1.0000000000000009; no sample exceeds 1 + 1e-6.
The independently executed guard held both existing input banks and checked
their current binary64 arrays and geometry before MATLAB started. The earlier
Python result and its recorded manifest agree on their input identifier and
configuration, but the bank and producer's historical identity were not
re-authenticated. Therefore the sample comparison is conditional on the
current input match; it does not establish the historical author's data.

The recorded MATLAB process naturally exited successfully. The 834499-byte
peak is the guard's observed task-tree peak before its terminal receipt, with
1-second polling; it is not a hard filesystem quota. Full original terminal
and failure records are retained locally, not replaced by the sanitized copy.
MATLAB startup emitted warnings about missing legacy CVX search-path directories;
the evaluated native MRT bridge does not invoke CVX, and the process exited 0.

Run `python verify_bundle.py` to recompute the complete saved-vector differences,
means, transmit power and saved-layout spacing/box checks from this bundle. This
geometry check uses a 1e-6 tolerance. The verifier does not regenerate either set of samples, independently authenticate
the original channel bank, or rerun the AO. The full channel input and MATLAB
bridge are not included in this compact evidence bundle; the numbers alone are
not a standalone physical reproduction. The MATLAB evaluation did not perform
an independent AO search. The retained sample record does not contain per-user
SINR, channel matrices or beamforming matrices and therefore is not a complete
per-user physical-feasibility certificate. Original-paper reference agreement is not established
for this point, and neither the complete figure nor the paper has passed.
