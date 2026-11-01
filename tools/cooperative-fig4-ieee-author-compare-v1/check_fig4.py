"""Compare three author MAT row means to a locally generated Fig.4 SVG.

The PDF, SVG, author ZIP, and thesis-reference report are caller supplied.
This parser neither writes an artifact nor authenticates historic source data.
"""
import argparse
import importlib.util
import json
import math
from pathlib import Path
import re
import xml.etree.ElementTree as ET
import zipfile

NAMESPACE = '{http://www.w3.org/2000/svg}'
NUMBER = re.compile(r'[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?')
TRANSFORM = re.compile(r'matrix\(1,0,0,-1,([\d.]+),([\d.]+)\)')
METHODS = [('AP-AO', 0, 'rgb(44.299316%,11.399841%,68.998718%)'),
           ('MR-S-PA', 3, 'rgb(76.098633%,7.099915%,57.299805%)'),
           ('MR-TTS-PA', 6, 'rgb(100%,65.499878%,19.599915%)')]


def require(condition, detail):
    if not condition:
        raise ValueError(detail)


def bounded_read(path, cap):
    with Path(path).open('rb') as stream:
        data = stream.read(cap + 1)
    require(len(data) <= cap, 'input size bound')
    return data


def load_matrix_parser():
    path = Path(__file__).resolve().parents[1] / 'check_cooperative_saved_fig4_triplicate_means.py'
    spec = importlib.util.spec_from_file_location('_cooperative_mat_parser', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.matrix


def plot_paths(svg):
    root = ET.fromstring(svg)
    candidates = {name: [] for name, _, _ in METHODS}
    horizontal = []
    for path in root.iter(NAMESPACE + 'path'):
        style = path.attrib.get('style', '')
        match = TRANSFORM.fullmatch(path.attrib.get('transform', ''))
        if not match:
            continue
        x, y = map(float, match.groups())
        desc = path.attrib.get('d', '')
        nums = [float(v) for v in NUMBER.findall(desc)]
        if 345 < x < 348 and 540 < y < 556 and len(nums) == 24:
            for name, _, color in METHODS:
                if 'stroke:' + color in style:
                    candidates[name].append((x, y, nums))
        if (345 < x < 348 and 420 < y < 565 and len(nums) == 4 and
                'stroke:rgb(14.898682%,14.898682%,14.898682%)' in style and
                193 < abs(nums[0]-nums[2]) < 194 and abs(nums[1]-nums[3]) < 0.01):
            horizontal.append(y-nums[1])
    require(len(horizontal) == 2, 'expected exactly two Fig.4 horizontal axis edges')
    top, bottom = sorted(horizontal)
    require(427 < top < 428 and 560 < bottom < 561, 'unexpected Fig.4 vertical bounds')
    output = {}
    for name, values in candidates.items():
        require(len(values) == 1, 'missing or ambiguous Fig.4 curve: ' + name)
        origin_x, origin_y, pts = values[0]
        xs = [origin_x + pts[2*i] for i in range(12)]
        require(all(abs(xs[i]-(xs[0]+i*(xs[-1]-xs[0])/11)) < 0.006 for i in range(12)),
                'curve x positions not twelve uniform ordinals')
        require(346 < xs[0] < 348 and 539 < xs[-1] < 541, 'curve x bounds')
        output[name] = [14.0*(bottom-origin_y+pts[2*i+1])/(bottom-top) for i in range(12)]
    return top, bottom, output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--fig4-svg', required=True, type=Path)
    parser.add_argument('--author-zip', required=True, type=Path)
    parser.add_argument('--eps-report', required=True, type=Path)
    args = parser.parse_args()
    top, bottom, pdf_curves = plot_paths(bounded_read(args.fig4_svg, 4*1024*1024))
    require(args.author_zip.stat().st_size <= 2*1024*1024, 'author ZIP bound')
    with zipfile.ZipFile(args.author_zip) as archive:
        entry = 'test_varsigma_316/plot_record0120.mat'
        matching = [v for v in archive.infolist() if v.filename == entry]
        require(len(matching) == 1 and matching[0].file_size <= 65536, 'MAT member identity or size')
        matrix = load_matrix_parser()(archive.read(matching[0]))
    old = json.loads(bounded_read(args.eps_report, 2*1024*1024))
    require(old.get('actual_point_count') == 24 and old.get('actual_method_ordinates') == 192,
            'unexpected EPS comparison report')
    methods = []
    for name, first, _ in METHODS:
        subset = sorted((v for v in old['rows'] if v['figure'] == 4 and v['method'] == name),
                        key=lambda v:v['ordinal_one_based'])
        require([v['ordinal_one_based'] for v in subset] == list(range(1, 13)), 'EPS ordinal coverage')
        triples = [[matrix[first+rep+18*col+360] for rep in range(3)] for col in range(12)]
        require(all(math.isfinite(v) and v != 0 for triple in triples for v in triple),
                'author triplicate invalid')
        means = [sum(triple)/3.0 for triple in triples]
        eps = [v['original_mapped_y_linear_SINR'] for v in subset]
        require(all(math.isfinite(v) for v in eps), 'EPS input invalid')
        dmat = [v-m for v,m in zip(pdf_curves[name], means)]
        deps = [v-e for v,e in zip(pdf_curves[name], eps)]
        methods.append({'method':name,'mat_rows_one_based':list(range(first+1,first+4)),
                        'sample_count':12,'max_absolute_pdf_minus_mat':max(map(abs,dmat)),
                        'rms_pdf_minus_mat':math.sqrt(sum(x*x for x in dmat)/12),
                        'max_absolute_pdf_minus_thesis_eps':max(map(abs,deps))})
    print(json.dumps({'schema':'COOPERATIVE_FIG4_FINAL_PDF_AUTHOR_MEAN_SCREEN_V1',
        'pdf_page_one_based':13,'vertical_plot_bounds':[top,bottom],
        'vertical_axis_min_max':[0,14],'methods':methods,
        'input_source_authenticated':False,'final_figure_provenance_proven':False,
        'full_paper_pass':False},indent=2,allow_nan=False))


if __name__ == '__main__':
    main()
