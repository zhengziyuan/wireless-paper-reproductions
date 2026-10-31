# MA fractional-stop numerical boundary

The historical Python and MATLAB source files and all prior output remain
unchanged. The original AO algorithms stop on fractional objective increase;
their theoretical monotonicity does not, by itself, certify that a numerically
negative step is convergence. The old Python AO and iterative FPA code can
label a small accepted negative step as converged and can divide by zero when
the previous objective is zero. This is an implementation boundary, not an
identified error in the paper or evidence that any particular saved run was
affected. Some prior FPA runs do not retain the per-sample objective histories
needed to determine whether they were affected.

`checked_ao.py` and `checked_fpa.py` are separately versioned entrypoints.
They preserve the original coordinate or QT updates and the original stopping
threshold for nonnegative increments with a defined denominator. A negative
increment stops with `numerical_decrease` and `converged=false`. If the prior
objective is zero, the ratio is recorded as undefined and iteration continues
within the existing budget; a later defined ratio uses the original threshold.
The FPA-ZF closed-form branch delegates to the original implementation.

`checked_run.run_job_checked(run_module, core, job, config)` calls the original
complete `run_job` after temporarily binding those checked functions in the
calling process, and restores the bindings even on failure. It retains the AO
history in the original return and adds FPA termination counts and summaries
of affected samples. A decrease beyond the existing verification tolerance
still fails; the raised `CheckedRunFailure` carries the scheme, sample index,
offending objective history and completed FPA summaries in its `evidence`
attribute. A guarded caller must persist that failure evidence. This does not
convert an exception into a successful run. The temporary binding is not
thread-safe. The returned
variant explicitly warns that the old implementation fingerprint alone does
not identify this code: any future job must bind all original and wrapper
sources and inputs, use the existing storage limits and receive separate
admission. It does not authorize or start an experiment.

An exception during an AO coordinate solve or objective evaluation also
propagates as a failure, with its original exception chained and completed AO
records, position and sweep/antenna context in the exception evidence. This
does not assert that every possible physical or process failure is captured;
the separately admitted caller must persist the failure evidence.

`convergence_gate.audit_history` can inspect retained objective histories
without changing them. A consistent numeric stopping test alone does not prove
physical feasibility, mathematical convergence, or agreement with the paper.
It cannot reconstruct histories that were never saved.

Run the small synthetic regressions from this folder with
`python -B test_convergence_gate.py`. They check negative/zero cases, normal
micro-examples against the unchanged Python routines, and wrapper cleanup;
they are not a complete scenario or dual-language numerical acceptance. The
existing resumable AO kernel and MATLAB implementation require their own
separately reviewed integration.
