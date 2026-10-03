"""Small independent invariance and validator regression tests."""
from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


class MISPhysics(unittest.TestCase):
    def test_global_first_layer_phase_invariance(self):
        for paper in ("mis-communications", "mis-sensing"):
            model_module = load(ROOT / "papers" / paper / "model.py", paper.replace("-", "_"))
            model = model_module.MISModel(model_module.load_fixture())
            for shift in (-1.7, 0.42, 2.1):
                phases = model.initial.copy()
                phases[:model.M] += shift
                np.testing.assert_allclose(model.evaluate(phases)[0], model.evaluate(model.initial)[0], atol=2e-12, rtol=2e-12)

    def test_sensing_power_noise_equivalence_and_monotonicity(self):
        module = load(ROOT / "papers" / "mis-sensing" / "model.py", "sensing_power_check")
        fixture = module.load_fixture()
        original = module.MISModel(fixture)
        doubled = dict(fixture)
        doubled["noise_power"] = (np.asarray(fixture["noise_power"]) / 2).tolist()
        reduced_noise = module.MISModel(doubled)
        at_double_power = original.evaluate(original.initial, 2 * fixture["transmit_power"])[0]
        np.testing.assert_allclose(at_double_power, reduced_noise.evaluate(original.initial)[0], atol=2e-12, rtol=2e-12)
        self.assertTrue(np.all(at_double_power >= original.evaluate(original.initial)[0] - 2e-12))

    def test_static_second_layer_has_no_position_dependence(self):
        module = load(ROOT / "papers" / "mis-communications" / "model.py", "static_aperture_check")
        model = module.MISModel(module.load_fixture())
        phases = model.initial.copy()
        phases[model.M:] = 0
        values = model.evaluate(phases)[0]
        np.testing.assert_allclose(values, np.repeat(values[:, :1], model.U, axis=1), atol=2e-12, rtol=2e-12)


class ValidatorRegression(unittest.TestCase):
    def test_parity_rejects_changed_values_and_shapes(self):
        validator = load(ROOT / "scripts" / "validate_parity.py", "parity_validator_test")
        for a, b in [({"x": [1, 2]}, {"x": [1, 3]}), ({"x": [1]}, {"x": 1}),
                     ({"x": True}, {"x": 1}), ({"x": float("nan")}, {"x": 0})]:
            errors = []
            validator.compare(a, b, "test", errors, 1e-7, 1e-6)
            self.assertTrue(errors)

    def test_parity_accepts_roundoff_but_not_failed_checks(self):
        validator = load(ROOT / "scripts" / "validate_parity.py", "parity_validator_checks")
        errors = []
        validator.compare({"x": 1.0}, {"x": 1.0 + 1e-9}, "test", errors, 1e-7, 1e-6)
        self.assertFalse(errors)
        self.assertTrue(validator.false_checks({"nested": {"gradient_pass": False}}))


if __name__ == "__main__":
    unittest.main()
