# Case 13: conditional saved-point hotspot matrix and rate audit

This is evidence about eight saved AO iterations from two starts of one
hotspot-satellite case (U=1, beta=20 dB). It is not a complete reproduction,
independent experiment, convergence proof, original-figure comparison, or
MATLAB validation. The projections contain only the saved binary64 fields
needed here and do not authenticate the historical source.

The historical direct, matrix and ground means and variances were used with
each saved phase to reconstruct the hotspot channel matrix. The reconstruction
and saved Q share the same historical run; they are two calculations, not two
independent experiments. The maximum real or imaginary component difference
across the eight matrices was approximately 2.23e-15; none of the 256 complex
entries in any of the eight reconstructed matrices matched exactly. Arithmetic
through Q and SINR treats stored binary64 inputs as exact rationals. The final
logarithm is a binary64 approximation, not an interval certificate. The rate
computed using reconstructed Q differed from the saved rate by approximately
-5.53e-13 to +1.43e-13; this is not a claim of bitwise equality.

Noise from each start's final record is applied to its four iterations. The
eight saved QT_begin noise values match their corresponding final records bit
for bit; see the [QT parameter evidence](../hotspot-case13-qt-parameter-evidence-v1/README.md).
The historical-source limitations described there still apply.
The recorded Q and each phase are ordered consistently in the saved candidate
source, but its historical producer binding is not authenticated. No physical
units or quadrature-error certificate is established. The trajectory blocks,
terminal records and complete events were not freshly authenticated or held as
an atomic snapshot. These boundaries apply to all reported values.

## Replay

From the repository root with Python 3.12:

```text
python -I -S -B tools/hotspot-case13-hu-evidence-v1/verify_saved_hu_q.py --expected tools/hotspot-case13-hu-evidence-v1/recorded_hu_q_result.json
```

This reader assembles the new small Q/rate supplement with existing projections
in `tools/hotspot-case13-evidence-v1`, and calls the two small computation
modules under `tools/hotspot-projector-memo-v1`. It emits its result to stdout;
it does not reproduce the original external process and storage guard.
