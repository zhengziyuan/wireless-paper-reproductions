"""Independent finite-grid MIS model; no author code or data are copied."""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np


class MISModel:
    def __init__(self, fixture):
        self.f = fixture
        mr, mc = fixture["ms1_shape"]
        nr, nc = fixture["ms2_shape"]
        self.M, self.N = mr * mc, nr * nc
        self.K = len(fixture["cascaded_spatial_frequencies"])
        self.P = self.M + self.N
        self.positions = [(r, c) for r in range(mr - nr + 1) for c in range(mc - nc + 1)]
        self.U = len(self.positions)
        self.mapping = np.asarray([[(r + i) * mc + c + j for i in range(nr) for j in range(nc)]
                                   for r, c in self.positions], dtype=int)
        coordinates = np.asarray([(r, c) for r in range(mr) for c in range(mc)], dtype=float)
        frequency = np.asarray(fixture["cascaded_spatial_frequencies"], dtype=float)
        # Row-major planar aperture; c_k^T v_u, not c_k^H v_u.
        self.C = np.exp(2j * np.pi * (frequency @ coordinates.T))
        self.initial = np.asarray(fixture["initial_ms1_phases"] + fixture["initial_ms2_phases"], float)

    def evaluate(self, angles, power=None):
        phi = np.exp(1j * angles[:self.M])
        theta = np.exp(1j * angles[self.M:])
        padding = np.ones((self.M, self.U), complex)
        for u in range(self.U):
            padding[self.mapping[u], u] = theta
        V = phi[:, None] * padding
        amplitude = self.C @ V
        derivative = np.zeros((self.K, self.U, self.P), complex)
        for u in range(self.U):
            derivative[:, u, :self.M] = 1j * self.C * V[:, u]
            derivative[:, u, self.M:] = 1j * self.C[:, self.mapping[u]] * V[self.mapping[u], u]
        gain = np.abs(amplitude) ** 2
        gain_jac = 2 * np.real(np.conj(amplitude)[:, :, None] * derivative)
        if self.f["mode"] == "communications":
            scale = np.asarray(self.f["reference_snr"])[:, None]
            rate = scale * gain
            jac = scale[:, :, None] * gain_jac
            echo = np.zeros_like(gain)
        else:
            beta2 = np.asarray(self.f["beta_squared"])[:, None]
            echo = beta2 * gain ** 2
            echo_jac = 2 * beta2[:, :, None] * gain[:, :, None] * gain_jac
            transmit_power = self.f["transmit_power"] if power is None else power
            noise = np.asarray(self.f["noise_power"])[:, None] / transmit_power
            denominator = np.sum(echo, axis=0)[None, :] - echo + noise
            denominator_jac = np.sum(echo_jac, axis=0)[None, :, :] - echo_jac
            rate = echo / denominator
            jac = echo_jac / denominator[:, :, None] - (
                echo / denominator ** 2)[:, :, None] * denominator_jac
        return rate, jac, V, gain, echo

    def selected(self, angles, power=None):
        rate, jac, *_ = self.evaluate(angles, power)
        maximum = np.max(rate, axis=1)
        # Break BLAS-roundoff ties by the smallest index, not a parity tolerance.
        tie = 32 * np.finfo(float).eps * np.maximum(
            np.max(np.abs(rate), axis=1), np.finfo(float).tiny)
        schedule = np.argmax(rate >= (maximum - tie)[:, None], axis=1)
        return rate[np.arange(self.K), schedule], jac[np.arange(self.K), schedule], schedule

    def softmin(self, angles, mu, log_metric=False):
        selected, jac, _ = self.selected(angles)
        if log_metric:
            jac = jac / (selected[:, None] + 1e-14)
            selected = np.log(selected + 1e-14)
        minimum = np.min(selected)
        unnormalized = np.exp(-(selected - minimum) / mu)
        weights = unnormalized / np.sum(unnormalized)
        value = minimum - mu * np.log(np.sum(unnormalized))
        return float(value), weights @ jac

    def quadratic_phases(self):
        mr, mc = self.f["ms1_shape"]
        nr, nc = self.f["ms2_shape"]
        curvature = self.f["quadratic_curvature"]
        alpha = [curvature * (r * r + c * c) for r in range(mr) for c in range(mc)]
        theta = [-curvature * (r * r + c * c) for r in range(nr) for c in range(nc)]
        return np.asarray(alpha + theta, float)

    def diagnostics(self, angles):
        rate, jac, V, gain, echo = self.evaluate(angles)
        h = 1e-6
        fd = np.zeros_like(jac)
        for p in range(self.P):
            offset = np.zeros(self.P)
            offset[p] = h
            fd[:, :, p] = (self.evaluate(angles + offset)[0] -
                           self.evaluate(angles - offset)[0]) / (2 * h)
        quad_error = 0.0
        quartic_error = 0.0
        for k in range(self.K):
            G = np.outer(np.conj(self.C[k]), self.C[k])
            for u in range(self.U):
                quadratic = np.real(np.vdot(V[:, u], G @ V[:, u]))
                quad_error = max(quad_error, abs(quadratic - gain[k, u]))
                if self.f["mode"] == "sensing":
                    reconstructed = self.f["beta_squared"][k] * quadratic ** 2
                    quartic_error = max(quartic_error, abs(reconstructed - echo[k, u]))
        selected, _, schedule = self.selected(angles)
        onehot = np.zeros((self.K, self.U))
        onehot[np.arange(self.K), schedule] = 1
        checks = {
            "finite_outputs": bool(np.all(np.isfinite(rate))),
            "unit_modulus_error": float(np.max(np.abs(np.abs(V) - 1))),
            "one_hot_row_sum_error": float(np.max(np.abs(np.sum(onehot, axis=1) - 1))),
            "quadratic_amplitude_identity_error": float(quad_error),
            "rate_gradient_relative_error": float(np.max(np.abs(fd - jac)) /
                                                  max(1.0, float(np.max(np.abs(jac))))),
            "selected_rate_identity_error": float(np.max(np.abs(selected -
                                                       np.sum(onehot * rate, axis=1)))),
            "number_of_positions_correct": bool(self.U ==
                (self.f["ms1_shape"][0] - self.f["ms2_shape"][0] + 1) *
                (self.f["ms1_shape"][1] - self.f["ms2_shape"][1] + 1)),
        }
        if self.f["mode"] == "sensing":
            checks["quartic_echo_identity_error"] = float(quartic_error)
        return checks


def phase_ascent(model, initial, iterations, mu, static=False, log_metric=False):
    """Exponential circle update with Armijo; exact per-target position selection."""
    x = np.asarray(initial, float).copy()
    if static:
        x[model.M:] = 0
    best = x.copy()
    best_min = float(np.min(model.selected(x)[0]))
    history = []
    for iteration in range(iterations):
        value, gradient = model.softmin(x, mu, log_metric)
        if static:
            gradient[model.M:] = 0
        norm = float(np.linalg.norm(gradient))
        direction = gradient / max(1.0, norm)
        step = 1.0
        accepted = False
        for _ in range(32):
            trial = x + step * direction
            trial_value = model.softmin(trial, mu, log_metric)[0]
            if trial_value >= value + 1e-4 * step * float(gradient @ direction):
                x, accepted = trial, True
                break
            step *= 0.5
        minimum = float(np.min(model.selected(x)[0]))
        if minimum > best_min:
            best_min, best = minimum, x.copy()
        history.append({"iteration": iteration + 1, "softmin": float(model.softmin(x, mu, log_metric)[0]),
                        "minimum_metric": minimum, "incumbent_minimum": best_min,
                        "gradient_norm": norm, "step": float(step if accepted else 0)})
    return best, history


def dump_output(result, output):
    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def load_fixture():
    return json.loads(Path(__file__).with_name("fixture.json").read_text(encoding="utf-8"))
