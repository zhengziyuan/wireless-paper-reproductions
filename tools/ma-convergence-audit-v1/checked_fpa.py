"""Versioned FPA entrypoint with an explicit numeric stopping boundary.

The underlying objective, updates, QCQP solver and iteration budget are
unchanged from the supplied original core.  Old source and results remain
untouched.  This code is not a claim of scientific acceptance.
"""
import numpy as np
import math
from convergence_gate import classify


class FpaNumericalFailure(RuntimeError):
    """A failing numerical condition with a serializable objective history."""
    def __init__(self, message, reason, history, tolerance):
        super().__init__(message)
        safe = [v if math.isfinite(float(v)) else str(v) for v in history]
        self.details = {"reason": reason, "previous": safe[-2] if len(safe) > 1 else None,
                        "current": safe[-1], "verification_tolerance": tolerance,
                        "iteration_one_based": len(history) - 1,
                        "objective_history": safe}


class FpaNumericalDecrease(FpaNumericalFailure):
    """The original monotonicity error with its actual numeric context."""
    def __init__(self, history, tolerance):
        super().__init__("Fixed-array QT benchmark decreased its actual sum rate.",
                         "numerical_decrease_beyond_verification_tolerance", history, tolerance)


def fixed_array_benchmark_checked(core, h, c, kind):
    if kind == "FPA-ZF":
        return core.fixed_array_benchmark(h, c, kind)
    if kind not in ("FPA-MRT", "FPA-OPT"):
        raise ValueError(kind)
    noise = np.asarray(c["noise"])
    h = h / np.sqrt(noise)[None, :]
    n, m = h.shape
    p = c["power"]
    spec = c["benchmark_solver"]
    v = h / np.linalg.norm(h, axis=0)
    w = v * np.sqrt(p / m)
    history = [core.channel_rate(h, w, np.ones(m))]
    if not math.isfinite(float(history[0])):
        raise FpaNumericalFailure("Fixed-array initial objective is nonfinite.",
                                  "nonfinite_initial_objective", history, c["verification_tolerance"])
    converged = False
    termination = "configured_iteration_cap"
    undefined = []
    for _ in range(spec["maximum_iterations"]):
        z = h.conj().T @ w
        total = np.sum(abs(z)**2, axis=1) + 1
        signal = abs(np.diag(z))**2
        mu = signal / (total - signal)
        eta = np.diag(z) / total
        if kind == "FPA-MRT":
            hv = h.conj().T @ v
            q = np.sum(((1 + mu) * abs(eta)**2)[:, None] * abs(hv)**2, axis=0) / np.log(2)
            b = (1 + mu) * np.real(np.conj(eta) * np.diag(hv)) / np.log(2)
            amp = core.power_qcqp(q, b, p, spec["bisection_tolerance"])
            w = v * amp[None, :]
        else:
            q = (h * ((1 + mu) * abs(eta)**2)[None, :]) @ h.conj().T / np.log(2)
            b = h * ((1 + mu) * eta)[None, :] / np.log(2)
            val, vec = np.linalg.eigh(q)
            projected = vec.conj().T @ b
            row_energy = np.sum(abs(projected)**2, axis=1)
            scale = max(float(val.max()), 1)
            if val.min() < -spec["spectral_zero_tolerance"] * scale:
                raise RuntimeError("QT QCQP matrix failed its PSD identity.")
            val[val < 0] = 0
            rownorm = np.sqrt(row_energy)
            diagonal = core.power_qcqp(val, rownorm, p, spec["bisection_tolerance"])
            denominator = np.divide(rownorm, diagonal, out=np.ones_like(rownorm), where=diagonal > 0)
            w = vec @ (projected / denominator[:, None])
        history.append(core.channel_rate(h, w, np.ones(m)))
        if history[-1] < history[-2] - c["verification_tolerance"]:
            raise FpaNumericalDecrease(history, c["verification_tolerance"])
        reason, _ = classify(history[-2], history[-1], spec["fractional_tolerance"])
        if reason.startswith("nonfinite_"):
            raise FpaNumericalFailure("Fixed-array stopping test is nonfinite: " + reason,
                                      reason, history, c["verification_tolerance"])
        if reason == "undefined_fractional_increase":
            undefined.append(len(history) - 1)
            continue
        if reason != "continue":
            termination = reason
            converged = reason == "fractional_increase"
            break
    result = {"iterations": len(history) - 1, "converged": converged,
              "objective": history, "termination": termination}
    if undefined:
        result["undefined_fractional_increase_iterations_one_based"] = undefined
    return history[-1], result
