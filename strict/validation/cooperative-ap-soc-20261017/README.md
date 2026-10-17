# Actual full-size native AP QT conditioning repair

The first full183 native attempt returned eight retained failures from the
same AP QT solver route. The campaign was stopped; these points are not
successful figure results. A separate full-size cold case captured an actual
failing AP-AO QT input, including its original W, complete complex means,
covariances, ground-terminal moments, noise and all constraint limits.

For exactly that input, the previous native quadratic-form representation
failed under both existing `high` and `best` precision controls. The same
convex QT problem, expressed with scaled coordinates and explicit second-order
cones, returned `Solved` with the original solver and acceptance thresholds.
CVX itself explains the numerical scaling benefit of [equivalent norm
representations](https://cvxr.com/cvx/doc/advanced.html#eliminating-quadratic-forms).

All original complex precoder variables remain independent. The only changes
of representation are `W_j=sqrt(P_j)*V_j` and a positive objective scale.
For `F^H F=Q`, the source quadratic power is exactly `||F W||²`. With affine
`t`, `||a||² <= t` is exactly `||[2a;t-1]|| <= t+1`. Satellite power and GT
constraints use their equivalent unit-radius norm inequalities. No model,
objective, channel covariance, physical budget, QT auxiliary or stopping
rule is replaced. Only roundoff-level negative eigenvalues are clipped by
the same PSD-factor convention already used in Python; no jitter is added.

The production native core now uses `strict_satcom_ap_qt_scaled.m` for the AP
update. Its previous implementation remains available as the explicitly
named `ap_qt_update_unscaled` control. All native source bindings include the
new provider. Source-distinct old results and failures remain preserved.

## Actual independent evidence

The captured input retains3 satellites,16 feeds each,2 users and1 ground
terminal. All original finite-Rician moments are supplied; this is not a
reduced physical scenario or LoS replacement.

- Independent MP80 received-power calculations reproduce every native SINR,
  denominator, satellite power and GT interference under the unchanged
  absolute1e-9 plus relative1e-10 field policy.
- Native and independent Python solutions pass all original physical limits.
  The native QT bound and minimum-SINR nondecrease pass absolute1e-5.
- The original Python AP QT implementation independently solves the same
  complete input using its configured Clarabel solver. Its surrogate optimum
  differs from the native result by **3.2446632047822277e-9**, below the existing
  absolute1e-5 numerical-objective gate.
- The minimum physical SINR increases from about1.3781 to
  **14.874265809309973**. This is one convex update, not a complete nonconvex
  AP-AO solution or complete183-point campaign.

The two small MAT files contain the unchanged actual failed input and actual
native output. The input also retains both failed old solver attempts.
The JSON audit separately records input/output/provider hashes, every physical
comparison and acceptance flag. No private paths or source manuscript is included.

```text
python tools/cooperative-stable-replay/audit_ap_qt.py --input strict/validation/cooperative-ap-soc-20261017/actual-failed-AP-QT-input.mat --native-output strict/validation/cooperative-ap-soc-20261017/actual-scaled-AP-QT-output.mat --output new-independent-AP-QT-audit.json
```

Install `strict/requirements.txt` and `mpmath==1.4.1`. The command uses the
actual saved native result, a fresh original Python convex solve and MP80
physical reevaluation. It does not require MATLAB/CVX on the checking host.

A distinct full183 native campaign has been started with this repair and
the positive-Wick phase evaluator, retaining every original input, all8
schemes and1000 channel-moment draws per completed point. Its convergence,
full independent validation and original-reference agreement are not
certified by this one-update check. `full_reproduction_pass` remains false.

## First complete original native case and independent state replay

The first complete original case now passes all8 producer scheme gates and
an independent saved-state replay. All8 final complex precoder/power/phase
states, all47 fixed-context phase endpoints and all31 QT candidates are saved
in a MAT sidecar bound to the original result. Independent Python calculations
check every final physical metric and constraint, every saved phase gradient,
criterion and original strict1e-6 stop, and the reported physics of every QT
candidate. All pass the existing finite-precision field policy.

The recording change also has an actual same-case control: every returned
scheme evaluation/history/status, all original1000-draw moment metrics and
all point gates are **exactly equal** before and after recording. It adds
output only. The previous complete outputs and the earlier8 failures remain
preserved. This is one original case; no survivor-average or complete183
independent certificate is inferred.

The actual result, complete2.04 MB state sidecar and prior same-case result
are delivered losslessly in five transfer parts. The reconstructed archive
SHA256 is `3d32975f05c86d4ef2d2de1922aa87a55d723857f24b9e112389581360b1e7d3`.

```text
python tools/cooperative-stable-replay/unpack_evidence.py --archive strict/validation/cooperative-ap-soc-20261017/native-case000-recording.tar.gz --expected-sha256 3d32975f05c86d4ef2d2de1922aa87a55d723857f24b9e112389581360b1e7d3 --output-dir new-full-native-case
python tools/cooperative-stable-replay/audit_native_case.py --result new-full-native-case/case-000-matlab.json --before-recording new-full-native-case/before-recording-case000.json --output new-full-native-case-audit.json
```

This replay does not claim MP80 references for these new phase contexts or
independent raw replay of every MC draw. The separate actual91 MP80 endpoint
packet and one-QT MP80 check retain their own scopes. Complete native183
execution, remaining independent checks and original curves stay open.
