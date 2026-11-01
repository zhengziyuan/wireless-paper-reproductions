"""Small, fully synthetic tests of mapping and refusal cases."""
import unittest
import compare_figure as c


def inputs(variant='normal'):
    paths = [
        '<path transform="matrix(1,0,0,-1,85.5291,190.1469)" d="M -0.00175625 -0.0015375 L 191.420119 -0.0015375"/>',
        '<path transform="matrix(1,0,0,-1,85.5291,57.2172)" d="M -0.00175625 -0.00155 L 191.420119 -0.00155"/>']
    x = [-.00175625 + (191.420119 + .00175625)*i/11 for i in range(12)]
    for method, color in zip(c.METHODS, c.COLORS):
        xy = [(v, v/10) for v in x]
        if method == 'MR-TTS-NoRIS':
            xy[9] = (x[9], x[8]/10)
            xy[10] = (x[10], x[8]/10)
            del xy[9]  # Published vector has no vertex at ordinal ten.
            if variant == 'missing_neighbor':
                del xy[8]
            elif variant == 'nonhorizontal':
                xy[9] = (xy[9][0], xy[9][1] + 0.02)
            elif variant == 'wrong_x':
                xy[8] = (xy[8][0] + 0.1, xy[8][1])
        d = ' '.join(('M' if i == 0 else 'L') + ' ' + repr(v) + ' ' + repr(y)
                     for i, (v, y) in enumerate(xy))
        paths.append('<path transform="matrix(1,0,0,-1,85.5291,160)" '
                     f'style="stroke-width:0.66;stroke:rgb({color});" d="{d}"/>')
    rows = [{'figure': 5, 'method': m, 'ordinal_one_based': i+1,
             'original_mapped_y_linear_SINR':
                 (190.1484375-(160-(x[8]/10 if m == 'MR-TTS-NoRIS' and i in (9, 10)
                                      else v/10)))*4.5/132.9296875}
            for m in c.METHODS for i, v in enumerate(x)]
    return ('<svg>' + ''.join(paths) + '</svg>').encode(), {
        'schema': 'COOPERATIVE_FIG5_THESIS_EPS_96_REFERENCE_ORDINATES_V1', 'rows': rows}


class Tests(unittest.TestCase):
    def test_synthetic_matching_geometry_and_mismatch(self):
        svg, ref = inputs()
        result = c.compare(svg, ref)
        self.assertEqual(result['comparisons'], 96)
        self.assertLess(result['max_absolute_difference'], 1e-12)
        interpolated = [(s['method'], p['ordinal']) for s in result['series']
                        for p in s['publisher_ordinal_points'] if p['interpolated_on_polyline']]
        self.assertEqual(interpolated, [('MR-TTS-NoRIS', 10)])
        ref['rows'][0]['original_mapped_y_linear_SINR'] += 1
        self.assertAlmostEqual(c.compare(svg, ref)['max_absolute_difference'], 1)

    def test_missing_reference_or_wrong_color_rejected(self):
        svg, ref = inputs()
        ref['rows'].pop()
        with self.assertRaises(ValueError):
            c.compare(svg, ref)
        svg, ref = inputs()
        svg = svg.replace(c.COLORS[0].encode(), c.COLORS[1].encode(), 1)
        with self.assertRaises(ValueError):
            c.compare(svg, ref)

    def test_reject_incomplete_or_nonhorizontal_interpolation(self):
        for variant in ('missing_neighbor', 'nonhorizontal', 'wrong_x'):
            with self.subTest(variant=variant), self.assertRaises(ValueError):
                c.compare(*inputs(variant))


if __name__ == '__main__':
    unittest.main()
