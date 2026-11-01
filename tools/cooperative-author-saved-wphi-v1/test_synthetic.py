"""Pure synthetic tests; no author file is read or written."""
from fractions import Fraction as F
import math
import struct
import unittest
import zlib
from check_saved_wphi import element, inspect, parse_complex_double


def node(kind, data):
    return struct.pack('<II', kind, len(data)) + data + b'\0'*((-len(data)) % 8)


def matrix(name, dims, real, imag, compressed=True):
    flags = node(6, struct.pack('<II', 6 | 2048, 0))
    sizes = node(5, struct.pack('<' + 'i'*len(dims), *dims))
    payload = flags + sizes + node(1, name.encode('ascii'))
    payload += node(9, struct.pack('<' + 'd'*len(real), *real))
    payload += node(9, struct.pack('<' + 'd'*len(imag), *imag))
    inner = node(14, payload)
    return b'\0'*126 + b'IM' + (node(15, zlib.compress(inner)) if compressed else inner)


class Tests(unittest.TestCase):
    def test_complex_column_major_power_and_phase(self):
        W = [(F(0), F(0)) for _ in range(16*3*6)]
        W[0+16*0+48*0] = (F(3), F(4))
        W[1+16*0+48*5] = (F(0), F(5))
        W[0+16*1+48*2] = (F(6), F(0))
        W[0+16*2+48*4] = (F(8), F(0))
        phi = [(F(1), F(0)) for _ in range(150)]
        phi[17] = (F(0), F(0))
        out = inspect(W, phi)
        self.assertEqual([x['numerator'] for x in out['per_satellite_power']], ['50', '36', '64'])
        self.assertEqual(out['per_satellite_power_strictly_within_or_equal'], [True, True, False])
        self.assertEqual(out['saved_phi_exact_unit_modulus_count'], 149)
        self.assertEqual(out['saved_phi_zero_count'], 1)

    def test_compressed_and_uncompressed_complex_mat(self):
        real = [float(i) for i in range(150)]
        imag = [-0.25] * 150
        for compressed in (False, True):
            with self.subTest(compressed=compressed):
                out = parse_complex_double(matrix('phi', (25,6), real, imag, compressed), 'phi', (25,6))
                self.assertEqual(out[26], (F(26), F(-1, 4)))

    def test_reject_wrong_shape_name_and_nonfinite(self):
        x = [1.0]*150
        for raw, name, shape in [
            (matrix('phi', (25,6), x, x), 'W', (25,6)),
            (matrix('phi', (25,6), x, x), 'phi', (6,25)),
            (matrix('phi', (25,6), [math.nan]+x[1:], x), 'phi', (25,6)),
            (matrix('phi', (25,6), x, x)[:-5], 'phi', (25,6)),
        ]:
            with self.assertRaises(ValueError):
                parse_complex_double(raw, name, shape)

    def test_top_level_accepts_compressed_optional_padding_but_rejects_tail(self):
        values = [1.0] * 150
        padded = matrix('phi', (25,6), values, values)
        size = struct.unpack_from('<I', padded, 132)[0]
        raw = padded[:136+size]
        for good in (raw, padded):
            self.assertEqual(len(parse_complex_double(good, 'phi', (25,6))), 150)
        for bad in (raw + b'x', padded + b'x', raw + node(14, b''),
                    matrix('phi', (25,6), values, values, False) + b'x'):
            with self.assertRaises(ValueError):
                parse_complex_double(bad, 'phi', (25,6))

    def test_invalid_tag(self):
        with self.assertRaises(ValueError):
            element(b'\0'*7, 0)
        with self.assertRaises(ValueError):
            element(struct.pack('<II', 9, 100), 0)


if __name__ == '__main__':
    unittest.main()
