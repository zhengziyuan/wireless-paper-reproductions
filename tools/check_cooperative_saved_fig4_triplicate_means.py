"""Compare saved author Fig.4 triplicate means with existing EPS vector ordinates.

Reads the author's unmodified ZIP and an existing saved native-24 reference
report. No scientific rerun, fitting, scaling, interpolation, or data copies.
A pointwise match indicates compatibility with the retained three-value mean;
it does not establish random seeds, independent draws, all methods, Figure 5,
or full-paper/reference acceptance.
"""
import argparse
import hashlib
import json
import math
import struct
import zipfile
import zlib
from pathlib import Path

ENTRY = 'test_varsigma_316/plot_record0120.mat'
METHODS = [('AP-AO', 0), ('MR-S-PA', 3), ('MR-TTS-PA', 6)]

def require(condition, message):
    if not condition:
        raise ValueError(message)

def digest(data):
    return hashlib.sha256(data).hexdigest()

def tag(data, offset):
    require(offset + 8 <= len(data), 'MAT element header truncated')
    kind, length = struct.unpack_from('<II', data, offset)
    if kind >> 16:
        length = kind >> 16
        require(length <= 4, 'Bad small MAT element')
        return kind & 65535, data[offset+4:offset+4+length], offset+8
    end = offset + 8 + length
    require(end <= len(data), 'MAT element body truncated')
    return kind, data[offset+8:end], offset+8+((length+7)//8)*8

def matrix(data):
    require(len(data) >= 136 and data[126:128] == b'IM', 'Only little-endian MAT v5')
    kind, content, _ = tag(data, 128)
    if kind == 15:
        decompressor = zlib.decompressobj()
        content = decompressor.decompress(content, 65537)
        require(len(content) <= 65536 and decompressor.eof, 'Bounded MAT inflation')
        kind, content, _ = tag(content, 0)
    require(kind == 14, 'Expected MAT matrix')
    elements = []
    pos = 0
    while pos + 8 <= len(content):
        kind, value, pos = tag(content, pos)
        elements.append((kind, value))
    require(len(elements) == 4 and elements[0][0] == 6 and len(elements[0][1]) >= 8,
            'Expected real numeric array fields')
    flags = struct.unpack_from('<I', elements[0][1])[0]
    require(flags & 255 == 6 and not flags & 2048, 'Expected real double')
    require(elements[1][0] == 5 and len(elements[1][1]) == 12 and
            struct.unpack('<iii', elements[1][1]) == (18,20,5), 'Original full array dimensions')
    require(elements[2][1] == b'plot_record' and elements[3][0] == 9 and
            len(elements[3][1]) == 18*20*5*8, 'Original variable and full double payload')
    return struct.unpack('<'+'d'*(18*20*5), elements[3][1])

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--author-zip', type=Path, required=True)
    ap.add_argument('--saved-eps-report', type=Path, required=True)
    args = ap.parse_args()
    raw_zip = args.author_zip.read_bytes()
    raw_report = args.saved_eps_report.read_bytes()
    require(len(raw_zip) <= 2*1024*1024 and len(raw_report) <= 2*1024*1024, 'Input size bounds')
    from io import BytesIO
    with zipfile.ZipFile(BytesIO(raw_zip)) as archive:
        matches = [i for i in archive.infolist() if i.filename == ENTRY]
        require(len(matches) == 1 and matches[0].file_size <= 65536, 'Unique bounded author MAT entry')
        original_mat = archive.read(matches[0])
    values = matrix(original_mat)
    report = json.loads(raw_report)
    require(report['actual_point_count'] == 24 and report['actual_method_ordinates'] == 192,
            'Existing complete native-24 EPS comparison report')
    results = []
    for name, first in METHODS:
        rows = sorted((r for r in report['rows'] if r['figure'] == 4 and r['method'] == name),
                      key=lambda r:r['ordinal_one_based'])
        require(len(rows) == 12 and [r['ordinal_one_based'] for r in rows] == list(range(1,13)),
                'Exactly twelve original Fig.4 ordinates')
        steps = [r['EPS_full_y_ordinate_rounding_step'] for r in rows]
        require(all(s == steps[0] and math.isfinite(s) and s > 0 for s in steps), 'One EPS rounding step')
        means = []
        for col in range(12):
            triple = [values[first+rep+18*col+360] for rep in range(3)]
            require(all(math.isfinite(x) and x != 0 for x in triple), 'Three complete original saved values')
            means.append(sum(triple)/3)
        deltas = [abs(mean-r['original_mapped_y_linear_SINR']) for mean,r in zip(means,rows)]
        results.append(dict(method=name,one_based_mat_rows=[first+1,first+2,first+3],
                            points=12,maximum_absolute_difference=max(deltas),
                            RMS_difference=math.sqrt(sum(x*x for x in deltas)/12),
                            full_EPS_ordinate_step=steps[0],
                            every_point_within_half_EPS_step=all(x <= steps[0]/2 for x in deltas)))
    require(args.author_zip.read_bytes() == raw_zip and args.saved_eps_report.read_bytes() == raw_report,
            'Both input bytes unchanged across comparison')
    outcome = dict(schema='COOPERATIVE_AUTHOR_SAVED_FIG4_THREE_VALUE_MEANS_V1',
        source_zip_SHA256=digest(raw_zip), source_mat_entry=ENTRY, source_mat_SHA256=digest(original_mat),
        eps_report_SHA256=digest(raw_report), source_array_shape=[18,20,5], one_based_slice=2,
        columns=list(range(1,13)), matched_methods=results,
        all_36_within_half_EPS_step=all(x['every_point_within_half_EPS_step'] for x in results),
        construction='Unweighted arithmetic mean of each specified three saved rows; direct ordinal EPS comparison',
        inference='Saved values are consistent with the EPS ordinates after coordinate rounding; their exact publication provenance remains unproven.',
        limitations=['No claim about RNG seed, independence, full averaging protocol, other methods or Fig.5.',
                     'No optimizer, Monte Carlo simulation or raw author data modification.',
                     'A match is not full-paper or original-reference acceptance.'], full_paper_PASS=False)
    print(json.dumps(outcome,ensure_ascii=False,indent=2,allow_nan=False))
    return 0 if outcome['all_36_within_half_EPS_step'] else 1

if __name__ == '__main__':
    raise SystemExit(main())
