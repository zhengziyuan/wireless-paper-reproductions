"""Recheck three transcribed figure coordinates against retained case metrics.

This does not open the PDF, authenticate the transcriptions, or certify that
the figure and this case used the same physical model or randomness.
"""
import gzip
import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
DATA = ROOT / 'validation/hotspot-case13-final-mc-v1/recorded-projection.jsonl.gz'


def main():
    with DATA.open('rb') as stream:
        with gzip.GzipFile(fileobj=stream) as compressed:
            raw = compressed.read(131073)
    if len(raw) > 131072:
        raise ValueError('saved projection exceeds bound')
    obj = json.loads(raw)
    if obj['case']['U'] != 1 or obj['case']['kappa_satellite_db'] != 20:
        raise ValueError('unexpected case')
    # Transcribed from the rendered publisher figure; independent source
    # inspection remains required. Coordinates are in PDF points.
    y_top, y_bottom = 79.62109375, 212.921875
    positions = {'AO': 159.16015625, 'TwoStage': 151.3125, 'NoRIS': 194.49609375}
    rows = []
    for name, y in positions.items():
        mc = obj['schemes'][name]['independent_MC']
        samples = mc['hu_rate_samples']
        if len(samples) != 1000 or any(not isinstance(x, (int, float)) or not math.isfinite(x) for x in samples):
            raise ValueError('expected 1000 finite saved rates')
        rate = 2 + 12*(y_bottom-y)/(y_bottom-y_top)
        mean = math.fsum(samples) / len(samples)
        ratio = float(mc['ratio_of_empirical_expected_powers_sum_rate'])
        if not math.isfinite(ratio):
            raise ValueError('nonfinite saved empirical-power ratio rate')
        rows.append({'scheme': name, 'transcribed_y_pdf_points': y,
                     'graphical_rate_approx': rate,
                     'saved_empirical_power_ratio_rate': ratio,
                     'saved_sample_log_rate_mean': mean,
                     'ratio_minus_graphical_rate': ratio-rate,
                     'sample_mean_minus_graphical_rate': mean-rate})
    print(json.dumps({'schema': 'CASE13_FIG10_TRANSCRIBED_POINT_COMPARISON_V1',
        'paper_doi': '10.1109/TWC.2023.3309957', 'pdf_page': 15,
        'printed_page': 3662, 'figure': 10, 'U': 1, 'beta_s_linear': 100,
        'axis_y_top_pdf_points': y_top, 'axis_y_top_rate': 14,
        'axis_y_bottom_pdf_points': y_bottom, 'axis_y_bottom_rate': 2,
        'graphical_reading_allowance_approx': 0.05, 'results': rows,
        'coordinate_transcription_independently_authenticated_by_this_script': False,
        'reference_metric_and_parameters_proven_equivalent': False,
        'mathematical_convergence_or_full_paper_pass': False}, indent=2, allow_nan=False))


if __name__ == '__main__':
    main()
