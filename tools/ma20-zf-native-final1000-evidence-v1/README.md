# MATLAB re-evaluation at one saved ZF layout

This record covers one Fig. 20 scenario: D = 3, geometry 0, six antennas,
five users, Rician factor 100, and transmit power 1 W. MATLAB R2025b evaluated
the currently saved Python ZF layout on all 1,000 held NLoS samples. The
compressed record preserves every MATLAB rate, total transmit power and
maximum off-diagonal amplitude alongside the corresponding saved Python values,
in original sample order, together with the six coordinates, comparison and a
sanitized actual guard outcome. It does not duplicate the input channel bank.
Off-diagonal amplitude is an absolute complex amplitude, not a normalized
zero-forcing residual.

The MATLAB and saved Python mean sum rates are `31.70262417294929` and
`31.70262417294928` bit/s/Hz. Their maximum absolute per-sample difference is
`1.4210854715202004e-14`; the maximum MATLAB power is `1.0000000000000004` W,
and no sample exceeds `1 + 1e-6` W. The guard held both current input banks
against write/delete and compared all 1,000 complex samples and geometry; the
saved nominal and realized ZF positions matched as currently read. These are
conditional comparisons, not authentication of the historical author or
producer's data or environment.

A separate earlier record checked 198 coordinates under the current model:
[`ma20-zf-fig5-donor-evidence-v1`](../ma20-zf-fig5-donor-evidence-v1/).
Its audit result and guard terminal are bound here, but that audit did not
retain a durable content identity for its input donor. The same historical
object across that audit and this evaluation is therefore **not proven**.
The audit used current-source floating-point polygon gaps, not a rigorous
interval certificate, and did not authenticate the historical producer.

The MATLAB process naturally exited successfully. The reported 833,769-byte
peak is the observed task-tree peak before the terminal receipt, sampled once
per second; it is not a hard filesystem quota. Startup emitted warnings about
missing legacy CVX search paths; this native ZF evaluation does not call CVX.
The full original terminal and logs remain retained locally.

Run `python verify_bundle.py` to recompute the saved-vector differences,
means, powers and geometry checks. The saved-layout spacing and box checks
use a `1e-6` tolerance. This reader does not regenerate channels, authenticate
the old bank or rerun any optimization; the input bank and bridge are not
in this compact bundle. MATLAB did not independently perform AO here. The
retained outputs contain no per-user SINR, per-sample channel or beamforming
matrices, so they do not constitute a full physical-feasibility certificate.
Original-paper reference agreement, the full figure and the paper remain
unverified.
