"""Inspect two saved author MAT files; never run the optimizer or extract files."""
import argparse
from fractions import Fraction
import json
import math
from pathlib import Path
import struct
import zipfile
import zlib

ZIP_CAP = 4 * 1024 * 1024
MAT_CAP = 131072


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def element(data, offset):
    require(offset >= 0 and offset + 8 <= len(data), 'truncated element')
    kind, size = struct.unpack_from('<II', data, offset)
    if kind >> 16:
        size = kind >> 16
        require(size <= 4, 'invalid small element')
        return kind & 65535, data[offset+4:offset+4+size], offset+8
    end = offset + 8 + size
    require(end <= len(data), 'truncated element body')
    return kind, data[offset+8:end], offset+8+((size+7)//8)*8


def parse_complex_double(raw, expected_name, expected_shape):
    require(len(raw) <= MAT_CAP and len(raw) >= 136 and raw[126:128] == b'IM', 'MAT v5 little-endian required')
    kind, body, top_next = element(raw, 128)
    if kind == 15:
        # Some MATLAB MAT-v5 files omit padding after a compressed element.
        # Accept either exact end or zero padding through its eight-byte boundary,
        # but never silently ignore another variable or trailing nonzero bytes.
        compressed_end = 136 + len(body)
        require(len(raw) in (compressed_end, top_next) and
                not any(raw[compressed_end:]), 'unexpected top-level tail')
        z = zlib.decompressobj()
        inflated = z.decompress(body, MAT_CAP+1)
        require(len(inflated) <= MAT_CAP and z.eof and not z.unused_data, 'invalid or oversized compressed MAT')
        kind, body, end = element(inflated, 0)
        require(end == len(inflated), 'unexpected compressed tail')
    else:
        require(top_next == len(raw), 'unexpected top-level tail')
    require(kind == 14, 'expected matrix')
    fields = []
    offset = 0
    while offset + 8 <= len(body):
        k, b, offset = element(body, offset)
        fields.append((k, b))
    require(offset == len(body) and len(fields) == 5, 'unexpected matrix fields')
    require(fields[0][0] == 6 and len(fields[0][1]) >= 8, 'invalid flags')
    flags = struct.unpack_from('<I', fields[0][1])[0]
    require(flags & 255 == 6 and flags & 2048 and not flags & 512, 'expected complex double')
    require(fields[1][0] == 5 and len(fields[1][1]) == 4*len(expected_shape), 'invalid dimensions')
    dims = struct.unpack('<' + 'i'*len(expected_shape), fields[1][1])
    require(dims == expected_shape and fields[2][1] == expected_name.encode('ascii'), 'name or dimensions mismatch')
    count = math.prod(dims)
    require(fields[3][0] == fields[4][0] == 9 and len(fields[3][1]) == len(fields[4][1]) == count*8, 'invalid data payload')
    real = struct.unpack('<' + str(count) + 'd', fields[3][1])
    imag = struct.unpack('<' + str(count) + 'd', fields[4][1])
    require(all(math.isfinite(x) for x in real+imag), 'nonfinite entries')
    return [(Fraction.from_float(a), Fraction.from_float(b)) for a, b in zip(real, imag)]


def ratio(x):
    return {'numerator': str(x.numerator), 'denominator': str(x.denominator), 'approx': float(x)}


def inspect(W, phi):
    require(len(W) == 16*3*6 and len(phi) == 25*6, 'unexpected element counts')
    abs2 = lambda z: z[0]*z[0] + z[1]*z[1]
    powers = [sum((abs2(W[n+16*j+48*u]) for n in range(16) for u in range(6)), Fraction(0)) for j in range(3)]
    errors = [abs(abs2(z)-1) for z in phi]
    return {'schema': 'COOPERATIVE_AUTHOR_SAVED_W_AND_PHI_EXACT_V1',
            'saved_W_shape': [16,3,6], 'saved_phi_shape': [25,6],
            'per_satellite_power_limit': 50,
            'per_satellite_power': [ratio(v) for v in powers],
            'per_satellite_power_margin': [ratio(50-v) for v in powers],
            'per_satellite_power_strictly_within_or_equal': [v <= 50 for v in powers],
            'saved_phi_elements': len(phi),
            'saved_phi_exact_unit_modulus_count': sum(e == 0 for e in errors),
            'saved_phi_max_abs_squared_modulus_error': ratio(max(errors)),
            'saved_phi_zero_count': sum(abs2(z) == 0 for z in phi),
            'source_claims': ['W.mat is saved by an initialization script.',
                              'phi.mat is saved by a subsequent AO script.',
                              'Their association with a common final solution or figure point is unverified.'],
            'not_established': ['channel-dependent SINR or GEO interference', 'historical producer identity',
                                'paired final state', 'original figure generation', 'optimizer convergence', 'full paper pass'],
            'full_paper_pass': False}


def read_zip(path):
    path = Path(path)
    require(path.is_file() and path.stat().st_size <= ZIP_CAP, 'zip input missing or oversized')
    with zipfile.ZipFile(path) as archive:
        arrays = []
        for name, shape in [('W', (16,3,6)), ('phi', (25,6))]:
            target = 'test_varsigma_316/' + name + '.mat'
            entries = [entry for entry in archive.infolist() if entry.filename == target]
            require(len(entries) == 1 and entries[0].file_size <= MAT_CAP, 'missing, duplicate or oversized member')
            arrays.append(parse_complex_double(archive.read(entries[0]), name, shape))
    return inspect(*arrays)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--author-zip', type=Path, required=True)
    args = ap.parse_args()
    print(json.dumps(read_zip(args.author_zip), indent=2, allow_nan=False))


if __name__ == '__main__':
    main()
