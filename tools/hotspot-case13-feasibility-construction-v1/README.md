# Case 13: conditional continuous feasible-point construction

For event 1327964, the existing exact audit reports the saved beam power
exceeds its limit, and its phase vector has 25 entries. Its maximum stored
binary64 squared-modulus error is the exact fraction
`14344986692602049 / 40564819207303340847894502572032`, strictly less than
one. Consequently each saved phase entry is nonzero. This conclusion uses the
previously recorded maximum; it is not a fresh audit of the event bytes.

Let `W` be the saved beam matrix, `P = ||W||_F²`, `P0 = 100`, and let `phi`
be the saved phase vector. Define `t=P0/P` and the continuous-valued point
`W_new=sqrt(t)*W`, `phi_new[m]=phi[m]/abs(phi[m])`. Its beam power is exactly
`P0` and each of its 25 phases has unit modulus. From the earlier exact
power-rescaling check, the 15 NHU QoS margins remain strictly positive for
each of the two recorded NHU moment constructions; the earlier audit asserted
positive interference denominators. Noise is positive, so the scaled
denominators remain positive as well.

The phase operation leaves those NHU constraints unchanged **only under the
implemented direct-NHU-link model**. The Python `statistical.py` and MATLAB
`strict_hotspot_statistical.m` construct the NHU moment matrices from the
NHU mean and variance, without the RIS phase. Their HU moment matrix and
sum-rate objective do depend on the RIS phase: the old HU rate cannot be
reused for `phi_new`, and no monotonicity or rate improvement is asserted.
The result concerns the implemented statistical problem's total-power,
15 full-interference NHU QoS and unit-modulus phase constraints. It relies
on the already recorded margins and does not independently check a complete
list of all constraints in the publisher's full text. In particular, it does
not resolve the original paper's K-only versus full-interference mismatch or
its different scalar-isotropic channel-moment model; the implementation's
constraints and moments must not be presented as an independently verified
literal copy of the published model.

This is an existence argument for ideal real/complex arithmetic, not a new
optimizer output and not a tested representable binary64 beam or phase vector.
The original saved beam still strictly exceeds its power limit, and the
original stored phase is not claimed to be exactly unit modulus. Historical
source binding, full event atomicity, physical units, rounding feasibility,
MATLAB execution, optimizer convergence and original figures remain
unverified. Phase normalization and beam scaling may change the objective.

For every entry, `|phi_new[m]-phi[m]| = ||phi[m]|-1| <= epsilon`, where
`epsilon` is the exact fraction above. Also
`||W_new-W||_F = (1-sqrt(t))*sqrt(P) <= (1-t)*sqrt(P)`.
These bounds establish closeness of the mathematical construction without
claiming that it was produced by the historical algorithm.

The small reader checks the event identity and shape, the retained error bound,
the scale factor and 30 retained positive margins. It does not independently
recompute the error bound, margin values or their historical provenance.
From a complete checkout of the published branch:

```text
python -I -S -B tools/hotspot-case13-feasibility-construction-v1/check_recorded_preconditions.py
```
