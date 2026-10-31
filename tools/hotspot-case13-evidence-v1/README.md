# Case 13: conditional saved-point QoS audit

This evidence concerns eight saved AO iterations from two starts of one
hotspot-satellite case (U=1, beta=20 dB). It is not a reproduction of a full
paper, figure, optimization run, MATLAB implementation, or convergence proof.
The projections here retain only the saved binary64 inputs used for this audit;
they are not full trajectory files or independently authenticated originals.

The saved channel moments and the saved Psi matrices originate from the same
historical run. Reconstructing Psi from the moments is a separate calculation,
not an independent experiment. The noise and SINR targets were extracted from
each start's final record and applied to all four saved iterations of that
start. Their equality to the parameters used at every iteration has not been
independently established. Units are the implementation's saved normalized
units; no physical-unit or quadrature-error certificate is claimed.

The original guarded computation used exact rational arithmetic on the saved
binary64 values, all 15 other transmitted streams in each NHU denominator, and
both (1) Psi reconstructed from saved means/variances and (2) saved Psi. All
120 margins were strictly positive under each calculation; the smallest were
approximately 2.4458045423e-8 and 2.4458045391e-8, respectively. The largest
component difference between the two matrix constructions was approximately
1.9226e-16; the matrices should not be described as bitwise identical.

One saved point (start 1, iteration 3) has exact binary64 power exceeding its
saved limit of 100 by approximately 6.31263e-9. Strict comparison therefore
fails at that point. Rounding or solver tolerances may explain this small
excess, but no tolerance-based feasibility judgment is made here. The maximum
absolute deviation of a saved phase element's squared magnitude from one is
approximately 3.81e-16; it is not, by itself, a physical infeasibility claim.

The source trajectory chunks and the retained terminal records were not
freshly authenticated, and the individually locked reads do not establish an
atomic snapshot of a complete event. These limits apply to every conclusion.

## Replaying the arithmetic

With Python 3.12, run from the repository root:

```text
python -I -S -B tools/hotspot-case13-evidence-v1/verify_saved_qos.py --expected tools/hotspot-case13-evidence-v1/recorded_exact_qos_result.json
```

The four small JSON projections in this directory are the only saved inputs
needed by the arithmetic. The verifier loads
`../hotspot-projector-memo-v1/case13_eight_ao_exact_qos_prepared_v1.py`,
prints the exact rational result to stdout, and compares it to the separately
published recorded result when `--expected` is provided. It does not create
output files or rerun the original experiment. The standalone verifier does
not reproduce the original external storage guard. The projection construction
preserved the input values used by the original computation; source-level
provenance remains subject to the limits above.
