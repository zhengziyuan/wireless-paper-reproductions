"""Synthetic replay framing tests; no original or retained data are read."""
import importlib.util
import json
from pathlib import Path
import unittest

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('_selected_replay_test', HERE/'verify_recorded_assessment.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class Tests(unittest.TestCase):
    def test_strict_boolean_vs_number(self):
        self.assertFalse(m.strict_equal({'v': True}, {'v': 1}))
        self.assertTrue(m.strict_equal({'a': 1, 'b': False}, {'b': False, 'a': 1}))

    def test_duplicate_and_nonfinite_json_rejected(self):
        with self.assertRaises(ValueError): m.parse(b'{"a":1,"a":2}')
        with self.assertRaises(ValueError): m.parse(b'{"a":NaN}')

    def test_valid_json(self):
        self.assertEqual(m.parse(json.dumps({'ready': True}).encode()), {'ready': True})


if __name__ == '__main__': unittest.main()
