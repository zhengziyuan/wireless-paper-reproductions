# Saved ISAC endpoint: independent channel and power check

`check_saved_physical_state.py --job JOB.json --result RESULT.json` directly
reconstructs the BS, RIS, and bridge fields from the supplied directions,
rotations, gains and stored phases, then calculates each communication SINR,
the sensing pattern, sensing scale, and joint utility. It uses every other
transmitted stream in the interference denominator. It does not call the
project's channel/evaluation functions or run an optimizer.

For the supplied compact `saved_case_000_mc_004_projection.json`, both inputs
can point to the same projection. The independent floating calculation gives
utility `24.591913786388247`, within `7.71e-12` of the saved value; it gives
the sensing scale within `2.35e-13` of the saved value. These comparisons
cover two communication users and all 66 saved sensing directions (11 by 6),
assume the saved geometry and current model, and are not interval proofs.

The exact rational sum of squared serialized binary64 beam components exceeds
the similarly serialized power limit by about `1.12e-16 W`, well inside the
saved `1e-7 W` checking tolerance. The maximal exact squared-modulus discrepancy
of the RIS phases is `4.06e-16`; the fixed RIS angles are exactly zero, and the
BS angles lie inside the scenario's numerical bounds. These statements describe
the saved floating-point numbers and should not be interpreted as proof of a
physical constraint violation or rigorous interval feasibility.

The stored outer, inner, and full convergence flags are false: the recorded
termination was the maximum iteration limit. This single-state diagnostic does
not authenticate the historic source, replay its iterations, verify MATLAB or
the original figure, or certify the paper.
