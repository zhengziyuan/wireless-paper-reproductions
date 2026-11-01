"""Read saved case-13 projections; do not run a simulation or read the PDF."""
import base64
import gzip
import json
import math
from pathlib import Path
import struct

ROOT = Path(__file__).resolve().parents[2]


def need(ok, message):
    if not ok:
        raise ValueError(message)


def read_json(path, cap):
    with path.open('rb') as f:
        data = f.read(cap + 1)
    need(len(data) <= cap, 'input size')
    return json.loads(data)


def vector(desc, n):
    need(desc.get('shape') == [n, 1] and desc.get('order') == 'MATLAB_column_major' and
         desc.get('encoding') == 'ieee754_binary64_little_endian_base64' and
         'imag_base64' not in desc, 'SINR ABI')
    b = base64.b64decode(desc['real_base64'], validate=True)
    need(len(b) == 8 * n, 'SINR byte length')
    x = struct.unpack('<' + str(n) + 'd', b)
    need(all(math.isfinite(v) and v >= 0 for v in x), 'SINR domain')
    return x


def main():
    p = read_json(ROOT / 'tools/hotspot-case13-evidence-v1/final_parameters_projection.json', 16384)
    g = read_json(ROOT / 'tools/hotspot-case13-hu-evidence-v1/hu_input_projection.json', 65536)
    need(p['schema'] == 'CASE13_AO_FINAL_PARAMETERS_IDENTITY_V1' and len(p['events']) == 2, 'parameters schema')
    targets = []
    for start, ev in enumerate(p['events']):
        c = ev['context']; d = ev['fields']['target']
        need(c['case_id'] == 13 and c['geometry_id'] == 12013 and c['start_id'] == start and
             c['U'] == 1 and c['beta'] == 20 and d['shape'] == [15, 1] and
             d['order'] == 'MATLAB_column_major' and len(d['real']) == 15, 'target identity')
        vals = d['real']
        need(all(type(v) in (float, int) and math.isfinite(v) and v > 0 for v in vals), 'target values')
        targets.extend(float(v) for v in vals)
    need(all(x == targets[0] for x in targets), 'not a common recorded target')
    ev = g['event']; c = ev['context']; fields = ev['fields']['x']
    need(g['schema'] == 'CASE13_HU_INPUTS_IDENTITY_V1' and c['case_id'] == 13 and
         c['geometry_id'] == 12013 and c['U'] == 1 and c['beta'] == 20, 'ground identity')
    mu, var = fields['ground_mean'], fields['ground_variance']
    need(mu['shape'] == var['shape'] == [1, 25] and mu['order'] == var['order'] == 'MATLAB_column_major', 'ground ABI')
    need(len(mu['real']) == len(mu['imag']) == len(var['real']) == 25, 'ground count')
    factors = []
    for re, im, v in zip(mu['real'], mu['imag'], var['real']):
        need(all(type(z) in (int, float) and math.isfinite(z) for z in (re, im, v)) and v > 0, 'ground values')
        factors.append((re*re + im*im) / v)
    with gzip.open(ROOT / 'validation/hotspot-case13-selected-physical-v1/selected-input.jsonl.gz', 'rb') as f:
        raw = f.read(512*1024 + 1)
    need(len(raw) <= 512*1024 and raw.endswith(b'\n'), 'selected stream')
    rows = [json.loads(x) for x in raw.splitlines()]
    need([(x['scheme'], x['selected_start_id']) for x in rows] ==
         [('NoRIS', 1), ('TwoStage', 0), ('AO', 0)], 'selected identities')
    threshold = 10.0 ** (3.0 / 10.0)
    schemes = []
    for row in rows:
        need(row['selected_W_bitwise_equals_final'] and row['selected_phi_bitwise_equals_final'] and
             row['selected_no_ris_equals_final'] and row['no_ris_flags_match_scheme'], 'state identity')
        x = vector(row['evaluation']['sinr'], 16)[1:]
        schemes.append({'scheme': row['scheme'], 'recorded_nhu_count': len(x),
                        'reported_nhu_below_3dB_count': sum(v < threshold for v in x),
                        'min_reported_nhu_sinr': min(x), 'max_reported_nhu_sinr': max(x)})
    print(json.dumps({'schema': 'CASE13_FINAL_DEFAULT_PARAMETER_EVIDENCE_V1',
        'saved_target_count': len(targets), 'saved_common_target_linear': targets[0],
        'saved_common_target_db_approx': 10*math.log10(targets[0]),
        'saved_ground_component_count': len(factors),
        'saved_ground_mean_square_over_variance_min': min(factors),
        'saved_ground_mean_square_over_variance_max': max(factors),
        'IEEE_VI_reported_global_nhu_default_db': 3,
        'IEEE_VI_reported_global_ground_rician_default_db': 0,
        'paper_figure10_specific_override_found_in_manual_reviewed_scope': False,
        'paper_figure10_override_search_scope': 'figure caption, legend and Section VI.G text; text-extraction caveats apply',
        'paper_pdf_read_or_verified_by_this_script': False,
        'default_nhu_threshold_linear_approx': threshold, 'schemes': schemes,
        'constraints_of_reported_sinr': 'implementation full-J interference; paper Eq.32b uses K-only interference',
        'historical_producer_authenticated': False,
        'paper_figure_mismatch_cause_proved': False,
        'paper_or_full_science_pass': False}, indent=2, allow_nan=False))


if __name__ == '__main__':
    main()
