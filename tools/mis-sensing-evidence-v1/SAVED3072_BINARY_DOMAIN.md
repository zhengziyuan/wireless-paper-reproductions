# MIS sensing: exact checks on a saved phase and schedule

This check reads the already published saved native Figure 3 state for original
start 3072. The previous capsule reports its domain and binary-feasibility
flags as true and its combined convergence certificate as false. This check
adds independent exact-rational comparisons on the saved binary64 values; it
does not rerun the model, optimizer or samples.

The saved 9 by 25 assignment is strictly one-hot, and equals the separately
saved binary schedule. All nine saved multipliers are nonnegative. For the
400 saved `phi` and 256 saved `theta` complex values, the largest absolute
deviations in squared modulus from one are approximately 3.2805e-16 and
3.1865e-16, respectively. These deviations imply modulus error below the saved
1e-6 feasibility tolerance, but every serialized complex pair has a nonzero
exact squared-modulus residual. A tolerance-based check is not exact unit
modulus of the stored decimal/binary64 representation.

The saved scalar difference between eta and the saved minimum binary metric
is approximately 1.1071e-8, also below that tolerance. The SINR values are
not recomputed here; therefore this comparison cannot prove physical SINR
agreement. It also does not establish stationarity, convergence, MATLAB/Python
agreement, the full figure, or paper acceptance.

From the repository root, use Python 3 and a fresh output path:

```sh
python -B tools/mis-sensing-evidence-v1/check_saved3072_domain_exact_v1.py \
  strict/validation/mis-sensing-fig3-5-6-saved6000-20261019-v1/data/selected-fixed-final-state.json \
  /path/to/new-domain-check.json
```

These exact comparisons apply to saved binary64 numbers; they are not an
interval certificate for the forward physical model.
