"""Synthetic structure checks: no paper, author file or scientific run."""
import importlib.util
from pathlib import Path
import unittest

path = Path(__file__).resolve().parent / 'check_fig4.py'
spec = importlib.util.spec_from_file_location('_fig4_tested', path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def toy(*, duplicate=False, bad_x=False):
    svg = ['<svg xmlns="http://www.w3.org/2000/svg">']
    edge = 'stroke:rgb(14.898682%,14.898682%,14.898682%);fill:none'
    for y in (427.5, 560.4):
        svg.append(f'<path style="{edge}" transform="matrix(1,0,0,-1,346.8,{y})" d="M 0 0 L 193.15 0"/>')
    for _, _, color in module.METHODS:
        points = []
        for i in range(12):
            x = 193.15*i/11 + (0.02 if bad_x and i == 5 else 0)
            points.append(('M' if i == 0 else 'L') + f' {x} {i}')
        item = f'<path style="stroke:{color}" transform="matrix(1,0,0,-1,346.8,550)" d="{" ".join(points)}"/>'
        svg.append(item)
        if duplicate and color == module.METHODS[0][2]:
            svg.append(item)
    return (''.join(svg) + '</svg>').encode()


class PlotPathsTests(unittest.TestCase):
    def test_mapped_axes_and_twelve_points(self):
        top, bottom, curves = module.plot_paths(toy())
        self.assertEqual((top, bottom), (427.5, 560.4))
        self.assertEqual(len(curves), 3)
        self.assertEqual(len(curves['AP-AO']), 12)
        self.assertAlmostEqual(curves['AP-AO'][0], 14*10.4/132.9)

    def test_duplicate_curve_rejected(self):
        with self.assertRaises(ValueError):
            module.plot_paths(toy(duplicate=True))

    def test_irregular_ordinal_rejected(self):
        with self.assertRaises(ValueError):
            module.plot_paths(toy(bad_x=True))


if __name__ == '__main__':
    unittest.main()
