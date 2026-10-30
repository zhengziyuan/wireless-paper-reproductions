"""Versioned adapter for the original MA run_job; no work occurs on import.

Caller supplies the already imported original run and core modules.  The
binding is process-local, restored even on exception, and is not thread-safe.
The project permits only one admitted scientific worker at a time.  Admission,
source/input binding, output limits and storage guard remain the caller's job.
"""
from checked_ao import AoEvaluationFailure, optimize_checked
from checked_fpa import FpaNumericalFailure, fixed_array_benchmark_checked


class CheckedRunFailure(RuntimeError):
    """Failure carrying partial in-memory evidence; never a successful result."""
    def __init__(self, message, evidence):
        super().__init__(message)
        self.evidence = evidence


def run_job_checked(run_module, core, job, config):
    old_ao, old_fpa = run_module.optimize, run_module.fixed_array_benchmark
    if old_ao is not core.optimize or old_fpa is not core.fixed_array_benchmark:
        raise ValueError("original runner functions must be bound to the supplied original core")
    counts = {}
    termination_counts = {}
    completed_ao = []
    # Only abnormal sample summaries are added; original per-sample rate output
    # and existing nonconverged-sample counts are returned by the unchanged run_job.
    abnormal = []

    def checked_ao(initial, c, mode):
        try:
            positions, hist = optimize_checked(core, initial, c, mode)
        except AoEvaluationFailure as exc:
            evidence = {"failure": exc.details, "completed_ao": list(completed_ao),
                        "successful_run": False}
            raise CheckedRunFailure(str(exc), evidence) from exc
        completed_ao.append({"mode": mode, "positions": positions.tolist(), "history": hist})
        return positions, hist

    def checked_fpa(h, c, kind):
        counts[kind] = counts.get(kind, 0) + 1
        try:
            value, hist = fixed_array_benchmark_checked(core, h, c, kind)
        except FpaNumericalFailure as exc:
            evidence = {"scheme": kind, "sample_one_based": counts[kind],
                        "failure": exc.details,
                        "completed_ao": list(completed_ao),
                        "completed_fpa_termination_counts": dict(termination_counts),
                        "completed_fpa_abnormal_samples": list(abnormal),
                        "successful_run": False}
            raise CheckedRunFailure(str(exc), evidence) from exc
        reason = hist.get("termination", "direct_noniterative")
        key = kind + ":" + reason
        termination_counts[key] = termination_counts.get(key, 0) + 1
        undefined = hist.get("undefined_fractional_increase_iterations_one_based", [])
        if hist.get("termination") not in (None, "fractional_increase", "configured_iteration_cap") or undefined:
            abnormal.append({"scheme": kind, "sample_one_based": counts[kind],
                             "termination": hist.get("termination"),
                             "converged": hist["converged"],
                             "undefined_count": len(undefined),
                             "undefined_first_iteration": undefined[0] if undefined else None,
                             "undefined_last_iteration": undefined[-1] if undefined else None})
        return value, hist

    run_module.optimize, run_module.fixed_array_benchmark = checked_ao, checked_fpa
    try:
        result = run_module.run_job(job, config)
    finally:
        run_module.optimize, run_module.fixed_array_benchmark = old_ao, old_fpa
    result["convergence_variant"] = {
        "schema": "ma-checked-fractional-stop-v1",
        "original_numerical_source_retained": True,
        "production_execution_or_scientific_acceptance_implied": False,
        "fpa_abnormal_samples": abnormal,
        "fpa_termination_counts": termination_counts,
        "warning": "Original implementation fingerprint alone does not identify this wrapper; bind all wrapper source bytes separately.",
    }
    return result
