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
  with a distinct source binding. Its existence does not prove convergence.

Fresh destinations are required. Old failures and the active original bank
are preserved. The independent oracle retains every physical path and term.
