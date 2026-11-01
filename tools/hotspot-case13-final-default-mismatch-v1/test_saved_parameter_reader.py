"""Synthetic ABI and threshold checks; no scientific data is read."""
import base64
import math
from pathlib import Path
import struct
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parent))
from verify_recorded_parameters import vector


def desc(values):
    return {'shape':[len(values),1], 'order':'MATLAB_column_major',
            'encoding':'ieee754_binary64_little_endian_base64',
            'real_base64':base64.b64encode(struct.pack('<' + str(len(values)) + 'd',*values)).decode('ascii')}


class Tests(unittest.TestCase):
    def test_binary64_shape_and_threshold(self):
        self.assertEqual(vector(desc([10**(-3/10)]*15),15),tuple([10**(-3/10)]*15))
        self.assertLess(10**(-3/10),10**(3/10))

    def test_reject_bad_records(self):
        for a in (desc([math.nan]*15),desc([-1.0]*15),desc([0.0]*14)):
            with self.assertRaises(ValueError):vector(a,15)
        a=desc([1.0]*15);a['order']='row_major'
        with self.assertRaises(ValueError):vector(a,15)


if __name__ == '__main__':
    unittest.main()
