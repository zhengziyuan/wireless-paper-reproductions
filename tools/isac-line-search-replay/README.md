# Diagnose actual original full-size ISAC failures

The [actual evidence packet](../../strict/validation/isac045-actual-line-search-20261017/README.md)
binds every tested trial and all original controls from one failed RCG block.

- `capture_failure.py` traces the original first scheme and stops at its actual
  failure; this does not claim full six-scheme execution.
- `audit_failure.py` independently evaluates all80 stored vectors at MP80/100,
  using full physics and exactly promoted original binary64 fields.
- `stable_metrics.py` evaluates algebraically identical self-excluded sums and
  derivatives. It contains no optimizer.
- `audit_stable_derivatives.py` checks every W/RIS/rotation component at the
  actual full failure state against independent MP80/100 values.
- `continue_phase.py` retains the previous PR vectors and only the129 remaining
  original iterations. Its actual result is unconverged.
- `equivalent_runtime.py` reads unchanged original strict source into a private
  module and changes only metric arithmetic and QT auxiliary interference sum.
- `run_equivalent.py` cold-runs the exact original six schemes/scenario/budget
  with a distinct source binding. The actual completed control retains one
  Armijo failure, four outer-cap outcomes and one complete configured stop.
- `audit_cold_control.py` independently reads the full actual return, all2005
  AO decisions,6015 block scalar decisions and five MP80/100 physical states.
- `audit_cold_terminal_gradients.py` checks every final W/RIS/rotation
  component. Three relative-step PGA stops remain above the gradient threshold.
- `replay_cold_control.py` replays the [compact completed-control packet](../../strict/validation/isac045-cold-six-scheme-negative-20261017/README.md),
  preserving all six outcomes and the explicit missing histories.

Fresh destinations are required. Old failures and the active original bank
are preserved. The independent oracle retains every physical path and term.
