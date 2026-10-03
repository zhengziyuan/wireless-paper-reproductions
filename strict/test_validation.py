"""Regression tests for evidence comparisons, not simulation results."""
import unittest

from compare_components import compare
from validate_components import nonfinite_paths


class EvidenceComparisonTests(unittest.TestCase):
    def failures(self, a, b, path="metrics", atol=1e-7, rtol=1e-6):
        failures = []
        compare(a, b, path, failures, atol, rtol)
        return failures

    def test_missing_field_is_not_ignored(self):
        self.assertTrue(self.failures({"x": 1}, {"x": 1, "y": 2}))

    def test_unmatched_array_length_is_not_ignored(self):
        self.assertTrue(self.failures([1, 2], [1]))

    def test_boolean_is_not_numeric_success(self):
        self.assertTrue(self.failures(True, 1))

    def test_nonfinite_is_not_agreement(self):
        self.assertTrue(self.failures(float("nan"), float("nan")))
        self.assertTrue(self.failures(float("inf"), float("inf")))
        self.assertEqual(nonfinite_paths({"x": [float("inf")]}), ["result.x[0]"])

    def test_numeric_tolerance_does_not_replace_values(self):
        self.assertFalse(self.failures(1.0, 1.0 + 1e-8))
        self.assertTrue(self.failures(1.0, 1.01))

    def test_only_named_matlab_struct_collections_are_adapted(self):
        self.assertFalse(self.failures({"error": 0}, [{"error": 0}], "history.QCQP"))
        self.assertTrue(self.failures({"error": 0}, [{"error": 0}], "metrics.result"))


if __name__ == "__main__":
    unittest.main()
