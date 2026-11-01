"""Compare a retained thesis vector summary with publisher Fig. 5 in memory."""
import argparse
import json
import math
import re
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path


def require(ok, reason):
    if not ok:
        raise ValueError(reason)


# The manually checked published legend and PDF curve order. These names do
# not authenticate either original simulation or the retained thesis summary.
METHODS = ['AP-NoRIS', 'MR-S-NoRIS', 'MR-TTS-NoRIS', 'AP-AO',
           'MR-S-PA', 'MR-TTS-PA', 'MR-S-TS', 'MR-TTS-TS']
COLORS = ['37.599182%,44.699097%,45.498657%', '70.098877%,70.098877%,70.098877%',
          '43.899536%,38.398743%,19.999695%', '44.299316%,11.399841%,68.998718%',
          '76.098633%,7.099915%,57.299805%', '100%,65.499878%,19.599915%',
          '37.298584%,74.099731%,100%', '93.699646%,25.099182%,25.099182%']
NUMBER = r'[-+]?(?:\d*\.\d+|\d+\.?\d*)(?:[eE][-+]?\d+)?'


def compare(svg, ref):
    require(len(svg) <= 3_000_000, 'SVG exceeds source bound')
    require(ref['schema'] == 'COOPERATIVE_FIG5_THESIS_EPS_96_REFERENCE_ORDINATES_V1',
            'unexpected reference schema')
    values = {}
    for row in ref['rows']:
        key = (row['method'], row['ordinal_one_based'])
        require(row['figure'] == 5 and key not in values and
                math.isfinite(row['original_mapped_y_linear_SINR']), 'invalid reference row')
        values[key] = row['original_mapped_y_linear_SINR']
    require(set(values) == {(m, i) for m in METHODS for i in range(1, 13)},
            'expected eight methods and twelve ordinals')

    root = ET.fromstring(svg)
    curves, frame_bottom, frame_top = [], False, False
    for element in root.iter():
        if not element.tag.endswith('path'):
            continue
        d, tr, style = (element.get(k, '') for k in ('d', 'transform', 'style'))
        if tr == 'matrix(1,0,0,-1,85.5291,190.1469)' and d.startswith(
                'M -0.00175625 -0.0015375 L 191.420119 -0.0015375'):
            frame_bottom = True
        if tr == 'matrix(1,0,0,-1,85.5291,57.2172)' and d.startswith(
                'M -0.00175625 -0.00155 L 191.420119 -0.00155'):
            frame_top = True
        transform = re.fullmatch(r'matrix\(1,0,0,-1,85\.5291,([0-9.]+)\)', tr)
        if not transform or 'stroke-width:0.66;' not in style or d.count(' L ') < 8:
            continue
        tokens = re.findall(r'[ML]|' + NUMBER, d)
        require(len(tokens) % 3 == 0 and all(tokens[j] in ('M', 'L')
                for j in range(0, len(tokens), 3)), 'unsupported polyline')
        points = [(float(tokens[j+1]), float(tokens[j+2])) for j in range(0, len(tokens), 3)]
        color = re.search(r'stroke:rgb\(([^)]*)\)', style)
        require(color is not None, 'missing color')
        curves.append((float(transform.group(1)), points, color.group(1)))
    require(frame_bottom and frame_top and len(curves) == 8, 'unexpected publisher figure layout')

    result, all_errors = [], []
    for method, expected_color, (vertical_shift, points, color) in zip(METHODS, COLORS, curves):
        require(color == expected_color, 'publisher curve/legend color mapping changed')
        require(len(points) == (11 if method == 'MR-TTS-NoRIS' else 12),
                'unexpected publisher polyline vertex count')
        require(abs(points[0][0]) < .01 and abs(points[-1][0] - 191.420119) < .01 and
                all(a[0] < b[0] for a, b in zip(points, points[1:])), 'unexpected curve extent')
        errors, ordinates = [], []
        for ordinal in range(1, 13):
            x = points[0][0] + (points[-1][0] - points[0][0]) * (ordinal-1)/11
            is_vertex = any(abs(px-x) < 0.01 for px, _ in points)
            require(is_vertex or (method == 'MR-TTS-NoRIS' and ordinal == 10),
                    'unexpected absent ordinal vertex')
            for (x1, y1), (x2, y2) in zip(points, points[1:]):
                if x <= x2 + 1e-6:
                    if not is_vertex:
                        step = (points[-1][0]-points[0][0])/11
                        require(abs(x1 - (points[0][0] + 8*step)) < 0.01 and
                                abs(x2 - (points[0][0] + 10*step)) < 0.01 and
                                abs(y2-y1) < 1e-5,
                                'unexpected interpolation neighbors or nonhorizontal segment')
                    height = y1 + (y2-y1) * (x-x1)/(x2-x1)
                    break
            else:
                raise ValueError('curve does not cover ordinal')
            # PDF frame was independently read as y=0 to 4.5. Coordinates
            # are derived from its two verified horizontal frame lines.
            y = (190.1484375 - (vertical_shift-height)) * 4.5 / 132.9296875
            errors.append(abs(y - values[method, ordinal]))
            ordinates.append({'ordinal': ordinal, 'x': ordinal / 100, 'y': y,
                              'interpolated_on_polyline': not is_vertex})
        all_errors.extend(errors)
        result.append({'method': method, 'publisher_rgb_percent': color,
                       'publisher_polyline_vertices': len(points),
                       'publisher_ordinal_points': ordinates,
                       'max_absolute_difference': max(errors),
                       'rms_difference': math.sqrt(sum(e*e for e in errors)/len(errors))})
    return {'schema': 'COOPERATIVE_FIG5_IEEE_VS_THESIS_EPS_SUMMARY_V1',
            'publisher_page': 14, 'publisher_x_ticks': [0.01, 0.12, 0.01],
            'publisher_y_limits': [0, 4.5], 'comparisons': len(all_errors),
            'max_absolute_difference': max(all_errors),
            'rms_difference': math.sqrt(sum(e*e for e in all_errors)/len(all_errors)),
            'series': result,
            'limitations': ['Original thesis EPS colors and x coordinates are not in the retained summary.',
                            'One horizontal line point is obtained by polyline interpolation.',
                            'Numerical closeness does not establish identity of underlying data, historical generation or paper reproduction.']}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--paper-pdf', required=True, type=Path)
    ap.add_argument('--thesis-summary', required=True, type=Path)
    args = ap.parse_args()
    ref = json.loads(args.thesis_summary.read_text(encoding='utf8'))
    proc = subprocess.run(['pdftocairo', '-f', '14', '-l', '14', '-svg', str(args.paper_pdf), '-'],
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    print(json.dumps(compare(proc.stdout, ref), indent=2, allow_nan=False))


if __name__ == '__main__':
    main()
