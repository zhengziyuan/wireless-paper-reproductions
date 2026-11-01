# Synthetic MATLAB check of stopping-record audit

This check uses synthetic inputs only. It does **not** run a wireless-paper
scenario, an optimizer, or a stored case; it is not evidence of convergence,
physical feasibility, original-paper agreement, or completion of a paper.

One guarded MATLAB R2025b `-batch` execution completed naturally with exit code
zero; the guard observed both the launcher exit and all processes in its Job
exiting. The two expected completion markers appeared in captured standard
output; standard error was empty. The guard recorded peak accounted output of
559,977 bytes. The monitor polls and is not a hard filesystem quota; it watches
the task tree and cannot establish that MATLAB or licence services never write
elsewhere. The actual output also contained warnings about stale, unavailable
MATLAB search-path entries from an older local project. Those warnings are
retained locally; they do not certify that CVX is available or correct.

The five MATLAB source files were bound in the single-run manifest, held while
the child ran, and matched those bindings after it exited. The entry checks
the resolved MATLAB functions before testing. Its synthetic cases include:

* Positive, zero and negative objective increments, including a small negative
  increment that triggers the production signed stop but fails the independent
  recorded-nondecrease check.
* Incomplete, empty or singleton histories; invalid values and tolerances;
  and a negative reported gradient norm that the independent check rejects.
* Comparison of the synthetic negative-increment and negative-norm cases with
  the existing MATLAB production stopping function.

These results concern the selected synthetic cases only. The independent audit
does not change the production stopping rule, is not integrated into that
production runner, and treats a caller's `complete` flag as an assertion rather
than proof that a saved history is complete. Previous Python synthetic tests
covered comparable finite binary64 examples, but this execution does not
directly compare the languages on a real scientific trajectory.

The task-specific MATLAB source files are in
`tools/hotspot-recorded-monotonic-audit-v1/`; the existing production stopping
function is `strict/hotspot-satcom/strict_hotspot_termination.m`. Given an
appropriately configured MATLAB installation, the synthetic entry can be run
from the repository root using:

```matlab
toolDir = fullfile(pwd,'tools','hotspot-recorded-monotonic-audit-v1');
productionDir = fullfile(pwd,'strict','hotspot-satcom');
setenv('HOTSPOT_STOP_AUDIT_TOOLS',toolDir);
setenv('HOTSPOT_STOP_AUDIT_PRODUCTION',productionDir);
addpath(toolDir,'-begin');
matlab_synthetic_entry_prepared();
```

This replay is a standalone MATLAB test invocation and does not recreate the
original external resource guard or authenticate a historical scientific run.
