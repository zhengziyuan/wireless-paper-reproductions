# Actual sensing correctness evidence, revision 2

These are actual computed MATLAB/Python outputs, not copied original curves.
This folder does **not** certify that every paper figure or the full 6000-start
bank has been reproduced.

- Component receipts and parity compare actual metrics, checks, histories and
  finite states at the original declared numerical tolerances.
- Stable-increment receipts contain all 11 independent high-precision identity
  cases in each language. Neither objective-acceptance slack nor relaxed stop
  thresholds was added.
- Closed-form receipts check the original finite-array identities, common
  coordinate reference, analytic displacement schedule and phase-convention
  equivalence. The nine-panel images use all independently computed angular
  samples; dual full-grid consistency is not agreement with the original paper.
- The inferred-reference images overlay computed candidate curves with clearly
  labelled original EPS reference vectors. The candidate executes all four
  targets and all six power points using one deterministic original-RALM start
  per target/point and unchanged full per-start budgets. It is not the complete
  6000-start experiment, and the physical origin of its 100-fold effective
  normalization remains unverified.
- Compact candidate JSON keeps every point's phase, SINR, quantized SINR,
  original outer updates, residuals and actual stopping flags. Only inner RCG
  histories are omitted. Compact beam JSON omits large dense maps but keeps
  finite solved phases, positions, target metrics and the full raw-output hash.

`manifest.json` binds current executed module/settings/test-fixture hashes,
actual raw-output hashes, verified comparisons and all public file hashes.
Raw author manuscripts and source artwork are not included. Convergence and
feasibility flags are preserved independently for each language even when the
computed curves are numerically almost identical. No apparent curve closeness
is used to turn a failed stopping condition into a successful one.

Regenerate this evidence set after actual dual-language runs using
`python strict/freeze_sensing_correctness.py`. The freezer validates source
bindings, comparisons and false original-reproduction status before copying
artifacts into this folder; it does not run or replace the paper algorithms.
