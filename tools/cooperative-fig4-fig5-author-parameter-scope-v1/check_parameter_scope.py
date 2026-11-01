"""Check the visible author working script against the IEEE figure context.

Neither the PDF nor ZIP is redistributed.  Saved MAT arrays are inspected
only for top-level variable names and dimensions; their producer is unknown.
"""
import argparse
import io
import json
import math
import re
import struct
import subprocess
import zipfile
import zlib
from pathlib import Path


def require(value, detail):
    if not value:
        raise ValueError(detail)


def mat_tag(data, offset):
    require(offset + 8 <= len(data), 'truncated MAT tag')
    first, size = struct.unpack_from('<II', data, offset)
    if first >> 16:
        size = first >> 16
        require(size <= 4, 'bad MAT small tag')
        return first & 65535, data[offset + 4:offset + 4 + size], offset + 8
    end = offset + 8 + size
    require(end <= len(data), 'truncated MAT payload')
    return first, data[offset + 8:end], offset + 8 + ((size + 7) // 8) * 8


def mat_variables(data):
    require(len(data) <= 65536 and data[126:128] == b'IM', 'unsupported MAT file')
    offset, result = 128, []
    while offset + 8 <= len(data):
        kind, content, offset = mat_tag(data, offset)
        if kind == 15:
            dec = zlib.decompressobj()
            expanded = dec.decompress(content, 65537)
            require(dec.eof and len(expanded) <= 65536, 'MAT inflate bound')
            kind, content, _ = mat_tag(expanded, 0)
        require(kind == 14, 'unexpected top-level MAT element')
        fields, inner = [], 0
        while inner + 8 <= len(content):
            k, value, inner = mat_tag(content, inner)
            fields.append((k, value))
        require(len(fields) == 4 and fields[0][0] == 6 and len(fields[0][1]) >= 8 and
                fields[1][0] == 5 and len(fields[1][1]) % 4 == 0 and fields[3][0] == 9,
                'unexpected MAT matrix header')
        dims = list(struct.unpack('<' + 'i' * (len(fields[1][1]) // 4), fields[1][1]))
        flags = struct.unpack_from('<I', fields[0][1])[0]
        require(flags & 255 == 6 and not flags & 2048 and all(d > 0 for d in dims) and
                len(fields[3][1]) == 8 * math.prod(dims), 'expected complete real-double matrix')
        result.append({'name': fields[2][1].decode('ascii'), 'shape': dims})
    return result


def check(author_zip, pdf):
    data = Path(author_zip).read_bytes()
    require(len(data) <= 2 * 1024 * 1024, 'archive bound')
    prefix = 'test_varsigma_316/'
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        def member(name):
            items = [i for i in archive.infolist() if i.filename == prefix + name]
            require(len(items) == 1 and items[0].file_size <= 65536, 'missing or oversized member')
            return archive.read(items[0])
        # Preserve the ASCII MATLAB syntax without guessing the legacy
        # encoding used in unrelated comments.
        main = member('main.m').decode('latin-1')
        init = member('INIT_S_AO_beta_N_100_SCSI_u2_k1_j2.m').decode('latin-1')
        mats = {name: mat_variables(member(name)) for name in ('plot_record0119.mat', 'plot_record0120.mat')}
    # This source uses no block comments. Reject them rather than risk
    # mistaking a multi-line comment for a MATLAB script invocation.
    require('%{' not in main and '%}' not in main and '%{' not in init and '%}' not in init,
            'unsupported MATLAB block comments')
    strip = lambda s: '\n'.join(line.split('%', 1)[0] for line in s.splitlines())
    main, init = strip(main), strip(init)
    sweeps = re.findall(r'^\s*for\s+test_variable_2\s*=\s*([^\n;]+)\s*;?\s*$', main, re.M)
    sat = re.findall(r'^\s*beta_N\s*=\s*([^;\n]+)\s*;', init, re.M)
    ground = re.findall(r'^\s*beta_R\s*=\s*([^;\n]+)\s*;', init, re.M)
    require([s.strip() for s in sweeps] == ['2'], 'unexpected working sweep')
    calls = re.findall(r'^\s*INIT_S_AO_beta_N_100_SCSI_u2_k1_j2\s*;?\s*$', main, re.M)
    require(len(calls) == 1, 'expected explicit uncommented INIT script invocation')
    require(len(sat) == 1 and re.fullmatch(r'10\s*\^\s*test_variable_2', sat[0].strip()),
            'unexpected satellite factor')
    require([s.strip() for s in ground] == ['1'], 'unexpected ground factor')
    require(all(v == [{'name': 'plot_record', 'shape': [18, 20, 5]}] for v in mats.values()),
            'unexpected saved MAT metadata')
    proc = subprocess.run(['pdftotext', '-f', '13', '-l', '14', str(pdf), '-'],
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    require(len(proc.stdout) <= 65536 and len(proc.stderr) <= 65536, 'PDF text bound')
    text = proc.stdout.decode('utf-8')
    text = re.sub(r'-\s*\n\s*', '', text)
    text = re.sub(r'\s+', ' ', text)
    # This is a narrow assertion on two page snippets, not a full-text search.
    figure_context = r'Fig\. 4 and Fig\. 5 present .*?κN\s*=\s*20\s*dB,\s*κR\s*=\s*10\s*dB\s+and\s+κN\s*=\s*0\s*dB,\s*κR\s*=\s*10\s*dB'
    require(re.search(figure_context, text), 'expected Fig. 4/5 context not found')
    return {
        'schema': 'COOPERATIVE_FIG4_FIG5_WORKING_PARAMETER_SCOPE_V1',
        'visible_main_has_explicit_init_call': True,
        'visible_script_execution_proved': False,
        'visible_working_script': {'satellite_rician_linear': 100, 'satellite_rician_db': 20,
                                   'terrestrial_rician_linear': 1, 'terrestrial_rician_db': 0},
        'paper_figure_context': {'Fig4': {'satellite_rician_db': 20, 'terrestrial_rician_db': 10},
                                 'Fig5': {'satellite_rician_db': 0, 'terrestrial_rician_db': 10}},
        'saved_plot_mat_top_level_variables': mats,
        'mat_has_top_level_rician_metadata': False,
        'working_script_produced_retained_mats_proved': False,
        'published_plot_producer_recovered': False,
        'figure5_data_identified': False,
        'full_paper_pass': False,
    }


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--author-zip', required=True)
    parser.add_argument('--paper-pdf', required=True)
    args = parser.parse_args()
    print(json.dumps(check(args.author_zip, args.paper_pdf), indent=2))
