"""Read-only table route/negative guards; no optimizer or channel samples."""
from pathlib import Path
import tempfile
import unittest
from unittest import mock
import table_reproduction as tables


class TableRoutes(unittest.TestCase):
    def test_all36_rows_numeric34_patterns2_with_honest_scope(self):
        row_count = numeric_count = pattern_count = 0
        for paper, expected in (("cooperative-satcom", 16), ("hotspot-satcom", 20)):
            plan = tables.table_plan(paper, 1)
            self.assertEqual(plan["parameter_row_count"], expected)
            self.assertTrue(plan["runnable"])
            row_count += plan["parameter_row_count"]
            numeric_count += plan["numeric_parameter_row_count"]
            pattern_count += plan["unverified_external_pattern_reference_row_count"]
            for flag in ("executed", "automatic_downsizing", "table_reproduction_verified",
                         "external_pattern_rows_certified", "final_publisher_table_equivalence_verified",
                         "full_reproduction_passed", "actual_all_pairwise_realized_geometry_certified"):
                self.assertFalse(plan[flag])
            self.assertIn("no optimizer", plan["execution_scope"])
        self.assertEqual((row_count, numeric_count, pattern_count), (36, 34, 2))

    def test_absent_table_and_unsupported_id_rejected(self):
        for paper, number in (("mis-sensing", 1), ("cooperative-satcom", 2), ("hotspot-satcom", 0)):
            with self.assertRaises(ValueError):
                tables.table_plan(paper, number)

    def test_changed_frozen_manifest_and_canonical_config_rejected(self):
        with mock.patch.object(tables, "sha", return_value="0" * 64):
            with self.assertRaisesRegex(ValueError, "manifest"):
                tables.table_plan("cooperative-satcom", 1)
        actual_sha = tables.sha
        def changed_canonical(path):
            return "0" * 64 if Path(path).name == "spectral_config.json" else actual_sha(path)
        with mock.patch.object(tables, "sha", side_effect=changed_canonical):
            with self.assertRaisesRegex(ValueError, "Canonical"):
                tables.table_plan("cooperative-satcom", 1)

    def test_no_silent_matlab_substitution_or_changed_plan_execution(self):
        plan = tables.table_plan("hotspot-satcom", 1)
        with tempfile.TemporaryDirectory() as folder, mock.patch.object(tables.subprocess, "run") as run:
            output = Path(folder) / "must-not-exist"
            with self.assertRaisesRegex(ValueError, "not a MATLAB"):
                tables.execute_table(plan, "matlab", output)
            changed = dict(plan, full_reproduction_passed=True)
            with self.assertRaisesRegex(ValueError, "Changed"):
                tables.execute_table(changed, "python", output)
            run.assert_not_called()
            self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
