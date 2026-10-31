"""Small synthetic regressions, not reproduction or optimizer acceptance."""
import importlib.util
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
from types import SimpleNamespace

import numpy as np

from convergence_gate import audit_history, classify
from checked_ao import AoEvaluationFailure, optimize_checked
from checked_fpa import FpaNumericalDecrease, FpaNumericalFailure, fixed_array_benchmark_checked
from checked_run import CheckedRunFailure, run_job_checked


class FakeCore:
    def __init__(self, objective, step):
        self.objective = objective
        self.step = step

    def mrt_statistics(self, t, c):
        return (float(self.objective(t[0, 0])),)

    zf_statistics = mrt_statistics

    def solve_coordinate(self, t, c, n, mode):
        out = t.copy()
        out[n, 0] += self.step
        return out, {"before": float(t[n, 0]), "after": float(out[n, 0])}


class ConvergenceTests(unittest.TestCase):
    @staticmethod
    def original_core():
        source = Path(__file__).resolve().parents[2] / "strict/two-timescale-ma/core.py"
        spec = importlib.util.spec_from_file_location("original_ma_core", source)
        original = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(original)
        return original

    def test_stop_classification(self):
        self.assertEqual(classify(1, 1 - 1e-7, 1e-5), ("numerical_decrease", None))
        self.assertEqual(classify(0, 0, 1e-5), ("undefined_fractional_increase", None))
        self.assertEqual(classify(0, 1, 1e-5), ("undefined_fractional_increase", None))
        self.assertEqual(classify(float("nan"), 1, 1e-5), ("nonfinite_value", None))
        self.assertEqual(classify(1, 2, float("inf")), ("nonfinite_value", None))
        self.assertEqual(classify(-1e308, 1e308, 1e-5), ("nonfinite_increment", None))
        self.assertEqual(classify(5e-324, 1e308, 1e-5), ("nonfinite_fractional_increase", None))
        self.assertEqual(classify(1, 1, 1e-5), ("fractional_increase", 0.0))
        self.assertEqual(classify(1, 2, 1e-5), ("continue", 1.0))
        with self.assertRaises(ValueError):
            classify(1, 1, -1)

    def test_abnormal_stop_and_original_history_retained(self):
        c = {"maximum_AO_iterations": 3, "fractional_increase_threshold": 1e-5}
        core = FakeCore(lambda x: 1 - x * 1e-7, 1.)
        _, h = optimize_checked(core, [[0., 0.]], c, "MRT")
        self.assertEqual(h["termination"], "numerical_decrease")
        self.assertFalse(h["converged"])
        self.assertEqual(len(h["objective"]), 2)
        self.assertLess(h["objective"][-1], h["objective"][0])
        bad = audit_history(h["objective"], c["fractional_increase_threshold"], True)
        self.assertFalse(bad["numeric_stop_consistent"])
        self.assertEqual(bad["anomalies"][0]["reason"], "numerical_decrease")
        _, zero = optimize_checked(FakeCore(lambda x: 0., 0.), [[0., 0.]], c, "ZF")
        self.assertFalse(zero["converged"])
        self.assertEqual(zero["termination"], "configured_iteration_cap")
        self.assertEqual(zero["undefined_fractional_increase_sweeps_one_based"], [1, 2, 3])

    def test_unchanged_positive_trajectory_and_stop(self):
        original = self.original_core()
        fake = FakeCore(lambda x: 4. + x * 0.1, 1.)
        original.mrt_statistics = fake.mrt_statistics
        original.zf_statistics = fake.zf_statistics
        original.solve_coordinate = fake.solve_coordinate
        c = {"maximum_AO_iterations": 4, "fractional_increase_threshold": 0.03}
        for mode in ("MRT", "ZF"):
            a, ah = original.optimize([[0., 0.]], c, mode)
            b, bh = optimize_checked(fake, [[0., 0.]], c, mode)
            np.testing.assert_array_equal(a, b)
            self.assertEqual(ah, bh)
            self.assertTrue(audit_history(bh["objective"], c["fractional_increase_threshold"],
                                          bh["converged"])["numeric_stop_consistent"])

    def test_fpa_same_updates_on_positive_trajectory(self):
        core = self.original_core()
        h = np.array([[1.0 + 0.2j, 0.4], [0.2j, 1.1 - 0.3j]])
        c = {"noise": [1., 1.], "power": 2., "verification_tolerance": 1e-8,
             "benchmark_solver": {"maximum_iterations": 4, "bisection_tolerance": 1e-10,
                                  "fractional_tolerance": 1e-8, "spectral_zero_tolerance": 1e-12}}
        for kind in ("FPA-MRT", "FPA-OPT", "FPA-ZF"):
            old_rate, old_hist = core.fixed_array_benchmark(h, c, kind)
            new_rate, new_hist = fixed_array_benchmark_checked(core, h, c, kind)
            self.assertEqual(new_rate, old_rate)
            if kind != "FPA-ZF":
                new_hist = dict(new_hist)
                new_hist.pop("termination")
            self.assertEqual(new_hist, old_hist)

    def test_fpa_negative_and_zero_transitions(self):
        core = self.original_core()
        h = np.eye(2, dtype=complex)
        c = {"noise": [1., 1.], "power": 1., "verification_tolerance": 1e-6,
             "benchmark_solver": {"maximum_iterations": 3, "bisection_tolerance": 1e-9,
                                  "fractional_tolerance": 1e-5, "spectral_zero_tolerance": 1e-12}}
        for kind in ("FPA-MRT", "FPA-OPT"):
            with patch.object(core, "channel_rate", side_effect=[1., 1. - 1e-7]):
                _, old = core.fixed_array_benchmark(h, c, kind)
            self.assertTrue(old["converged"])
            with patch.object(core, "channel_rate", side_effect=[1., 1. - 1e-7]):
                _, new = fixed_array_benchmark_checked(core, h, c, kind)
            self.assertFalse(new["converged"])
            self.assertEqual(new["termination"], "numerical_decrease")
            self.assertEqual(new["objective"], old["objective"])
            with patch.object(core, "channel_rate", side_effect=[0., 0.]):
                with self.assertRaises(ZeroDivisionError):
                    core.fixed_array_benchmark(h, c, kind)
            with patch.object(core, "channel_rate", side_effect=[0., 0., 0., 0.]):
                _, zero = fixed_array_benchmark_checked(core, h, c, kind)
            self.assertFalse(zero["converged"])
            self.assertEqual(zero["termination"], "configured_iteration_cap")
            self.assertEqual(zero["objective"], [0., 0., 0., 0.])
            self.assertEqual(zero["undefined_fractional_increase_iterations_one_based"], [1, 2, 3])
            with patch.object(core, "channel_rate", side_effect=[0., 1., 1.]):
                _, later = fixed_array_benchmark_checked(core, h, c, kind)
            self.assertTrue(later["converged"])
            self.assertEqual(later["termination"], "fractional_increase")
            self.assertEqual(later["undefined_fractional_increase_iterations_one_based"], [1])

    def test_history_audit_does_not_erase_anomaly(self):
        report = audit_history([1., 0.9999999, 1.0000000], 1e-5, True)
        self.assertFalse(report["numeric_stop_consistent"])
        self.assertEqual(report["anomalies"], [{"transition_one_based": 1,
                                                "reason": "numerical_decrease"}])
        resumed = audit_history([0., 1., 1.], 1e-5, True)
        self.assertTrue(resumed["numeric_stop_consistent"])
        self.assertEqual(resumed["anomalies"][0]["reason"], "undefined_fractional_increase")
        premature = audit_history([1., 1., 1.], 1e-5, True)
        self.assertFalse(premature["numeric_stop_consistent"])
        self.assertEqual(premature["anomalies"][0]["reason"],
                         "termination_criterion_met_before_final_transition")

    def test_checked_run_propagates_and_restores_bindings(self):
        core = self.original_core()
        runner = SimpleNamespace(optimize=core.optimize, fixed_array_benchmark=core.fixed_array_benchmark)
        c = {"noise": [1., 1.], "power": 1., "verification_tolerance": 1e-6,
             "benchmark_solver": {"maximum_iterations": 3, "bisection_tolerance": 1e-9,
                                  "fractional_tolerance": 1e-5, "spectral_zero_tolerance": 1e-12}}
        def fake_run(job, config):
            with patch.object(core, "channel_rate", side_effect=[1., 1. - 1e-7]):
                _, hist = runner.fixed_array_benchmark(np.eye(2, dtype=complex), c, "FPA-MRT")
            return {"checks": {"nonconverged_samples": int(not hist["converged"])}}
        runner.run_job = fake_run
        result = run_job_checked(runner, core, {}, {})
        self.assertEqual(result["checks"]["nonconverged_samples"], 1)
        self.assertEqual(result["convergence_variant"]["fpa_termination_counts"],
                         {"FPA-MRT:numerical_decrease": 1})
        self.assertEqual(result["convergence_variant"]["fpa_abnormal_samples"][0]["sample_one_based"], 1)
        self.assertIs(runner.optimize, core.optimize)
        self.assertIs(runner.fixed_array_benchmark, core.fixed_array_benchmark)
        runner.run_job = lambda job, config: (_ for _ in ()).throw(RuntimeError("synthetic"))
        with self.assertRaisesRegex(RuntimeError, "synthetic"):
            run_job_checked(runner, core, {}, {})
        self.assertIs(runner.optimize, core.optimize)
        self.assertIs(runner.fixed_array_benchmark, core.fixed_array_benchmark)

    def test_beyond_tolerance_fpa_failure_retains_context(self):
        core = self.original_core()
        runner = SimpleNamespace(optimize=core.optimize, fixed_array_benchmark=core.fixed_array_benchmark)
        c = {"noise": [1., 1.], "power": 1., "verification_tolerance": 1e-6,
             "benchmark_solver": {"maximum_iterations": 3, "bisection_tolerance": 1e-9,
                                  "fractional_tolerance": 1e-5, "spectral_zero_tolerance": 1e-12}}
        h = np.eye(2, dtype=complex)
        with patch.object(core, "channel_rate", side_effect=[1., 0.99]):
            with self.assertRaises(FpaNumericalDecrease) as cm:
                fixed_array_benchmark_checked(core, h, c, "FPA-MRT")
        self.assertEqual(cm.exception.details["objective_history"], [1., 0.99])
        self.assertEqual(cm.exception.details["verification_tolerance"], 1e-6)
        def fake_run(job, config):
            with patch.object(core, "channel_rate", side_effect=[1., 1., 1., 0.99]):
                runner.fixed_array_benchmark(h, c, "FPA-MRT")
                runner.fixed_array_benchmark(h, c, "FPA-MRT")
        runner.run_job = fake_run
        with self.assertRaises(CheckedRunFailure) as cm:
            run_job_checked(runner, core, {}, {})
        evidence = cm.exception.evidence
        self.assertFalse(evidence["successful_run"])
        self.assertEqual(evidence["scheme"], "FPA-MRT")
        self.assertEqual(evidence["sample_one_based"], 2)
        self.assertEqual(evidence["failure"]["objective_history"], [1., 0.99])
        self.assertEqual(evidence["completed_fpa_termination_counts"], {"FPA-MRT:fractional_increase": 1})
        self.assertIs(runner.fixed_array_benchmark, core.fixed_array_benchmark)

    def test_ao_failure_context_and_chained_error(self):
        core = FakeCore(lambda x: 1., 0.1)
        c = {"maximum_AO_iterations": 2, "fractional_increase_threshold": 1e-5}
        prior = core.solve_coordinate
        def fail_second(t, config, n, mode):
            if n == 1:
                raise ValueError("synthetic coordinate failure")
            return prior(t, config, n, mode)
        core.solve_coordinate = fail_second
        with self.assertRaises(AoEvaluationFailure) as cm:
            optimize_checked(core, [[0., 0.], [1., 0.]], c, "MRT")
        details = cm.exception.details
        self.assertEqual(details["sweep_one_based"], 1)
        self.assertEqual(details["antenna_one_based"], 2)
        self.assertEqual(len(details["coordinate_updates"]), 1)
        self.assertIsInstance(cm.exception.__cause__, ValueError)
        self.assertEqual(details["objective"], [1.])
        with patch.object(core, "mrt_statistics", side_effect=[(1.,), ValueError("synthetic objective")]), \
             patch.object(core, "solve_coordinate", side_effect=prior):
            with self.assertRaises(AoEvaluationFailure) as cm:
                optimize_checked(core, [[0., 0.]], c, "MRT")
        self.assertEqual(cm.exception.details["phase"], "sweep_objective")
        self.assertEqual(len(cm.exception.details["coordinate_updates"]), 1)
        self.assertIsInstance(cm.exception.__cause__, ValueError)

    def test_nonfinite_objectives_fail_with_serializable_evidence(self):
        import json
        core = FakeCore(lambda x: float("nan"), 0.)
        c = {"maximum_AO_iterations": 1, "fractional_increase_threshold": 1e-5}
        with self.assertRaises(AoEvaluationFailure) as cm:
            optimize_checked(core, [[0., 0.]], c, "MRT")
        json.dumps(cm.exception.details, allow_nan=False)
        core = self.original_core()
        config = {"noise": [1., 1.], "power": 1., "verification_tolerance": 1e-6,
                  "benchmark_solver": {"maximum_iterations": 1, "bisection_tolerance": 1e-9,
                                       "fractional_tolerance": 1e-5, "spectral_zero_tolerance": 1e-12}}
        with patch.object(core, "channel_rate", side_effect=[1., float("nan")]):
            with self.assertRaises(FpaNumericalFailure) as cm:
                fixed_array_benchmark_checked(core, np.eye(2, dtype=complex), config, "FPA-MRT")
        self.assertEqual(cm.exception.details["reason"], "nonfinite_value")
        json.dumps(cm.exception.details, allow_nan=False)

    def test_actual_run_job_with_synthetic_numeric_dependencies(self):
        source_dir = Path(__file__).resolve().parents[2] / "strict/two-timescale-ma"
        sys.path.insert(0, str(source_dir))
        try:
            import core
            import run as runner
            c = {"noise": [1., 1.], "power": 1., "verification_tolerance": 1e-6,
                 "rician": [1., 1.], "beta": [1., 1.], "region_lower": [-10., -10.],
                 "region_upper": [10., 10.], "maximum_AO_iterations": 2,
                 "fractional_increase_threshold": 1e-5,
                 "benchmark_solver": {"maximum_iterations": 3, "bisection_tolerance": 1e-9,
                                      "fractional_tolerance": 1e-5, "spectral_zero_tolerance": 1e-12}}
            positions = np.array([[0., 0.], [1., 0.]])
            job = {"N": 2, "M": 2, "kappa": 1., "power": 1., "A": 2., "figure": 10,
                   "point": 0, "realization": 0, "geometry": {},
                   "nlos_re": [np.zeros((2, 2)).tolist()], "nlos_im": [np.zeros((2, 2)).tolist()]}
            def coordinate(t, config, n, mode):
                result = t.copy(); result[n, 0] += 0.1
                return result, {"synthetic": True}
            # One FPA-MRT decrease, a direct FPA-ZF value, and a normal FPA-OPT stop.
            with patch.object(runner, "scenario", return_value=(c, positions)), \
                 patch.object(runner, "instantaneous", return_value={"mean_sum_rate": 1.}), \
                 patch.object(runner, "los", return_value=np.eye(2, dtype=complex)), \
                 patch.object(core, "mrt_statistics", side_effect=lambda t, cfg: (1. - 1e-7 * t[:, 0].sum(),)), \
                 patch.object(core, "zf_statistics", return_value=(1.,)), \
                 patch.object(core, "solve_coordinate", side_effect=coordinate), \
                 patch.object(core, "channel_rate", side_effect=[1., 1. - 1e-7, 1., 1., 1.]):
                out = run_job_checked(runner, core, job, {"nlos_realizations_per_geometry": 1})
            self.assertFalse(out["checks"]["mrt_converged"])
            self.assertEqual(out["history"]["mrt"]["termination"], "numerical_decrease")
            self.assertEqual(out["metrics"]["schemes"]["FPA-MRT"]["nonconverged_samples"], 1)
            self.assertEqual(out["convergence_variant"]["fpa_termination_counts"]["FPA-MRT:numerical_decrease"], 1)
            self.assertEqual(out["convergence_variant"]["fpa_abnormal_samples"][0]["sample_one_based"], 1)
            self.assertIs(runner.optimize, core.optimize)
            self.assertIs(runner.fixed_array_benchmark, core.fixed_array_benchmark)
        finally:
            sys.path.remove(str(source_dir))


if __name__ == "__main__":
    unittest.main()
