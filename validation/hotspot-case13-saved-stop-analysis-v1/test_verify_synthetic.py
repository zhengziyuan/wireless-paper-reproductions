"""Synthetic replay tests; does not read historical or retained real records."""
import gzip
import importlib.util
import json
from pathlib import Path
import sys
import unittest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import verify_report as v

spec = importlib.util.spec_from_file_location('synthetic_consumer', v.SOURCE)
consumer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(consumer)


class Tests(unittest.TestCase):
    def test_empty_stream_and_incomplete_summary_not_a_pass(self):
        got = v.replay(gzip.compress(b''), {}, consumer)
        self.assertFalse(got['expected_events_and_histories_present'])
        self.assertFalse(got['full_paper_pass'])

    def test_partial_last_line_is_disclosed(self):
        got = v.replay(gzip.compress(b'{"action":'), {}, consumer)
        self.assertTrue(got['partial_final_line'])
        self.assertFalse(got['expected_events_and_histories_present'])

    def test_gzip_corruption_rejected(self):
        raw = gzip.compress(b'hello')[:-2]
        with self.assertRaises((EOFError, OSError)):
            v.decompress_limited(raw)

    def test_decompressed_limit_rejected(self):
        raw = gzip.compress(b'x' * (v.MAX_PLAIN + 1))
        with self.assertRaisesRegex(ValueError, 'decompressed'):
            v.decompress_limited(raw)

    def test_duplicate_json_keys_rejected(self):
        with self.assertRaisesRegex(ValueError, 'duplicate'):
            consumer.parse(b'{"action":"a","action":"b"}')

    def test_exact_report_comparison_respects_json_types(self):
        self.assertTrue(v.exact_equal({'ok': True, 'count': 1}, {'ok': True, 'count': 1}))
        self.assertFalse(v.exact_equal({'ok': True}, {'ok': 1}))
        self.assertFalse(v.exact_equal({'count': 1}, {'count': 1.0}))


if __name__ == '__main__':
    unittest.main()
