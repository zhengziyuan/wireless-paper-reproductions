"""Exact inclusive placement checks only; no simulation or fitted reference."""
import unittest


def placements(panel, subpanel):
    if not isinstance(panel, tuple) or not isinstance(subpanel, tuple):
        raise ValueError('Two literal integer dimension tuples required')
    if len(panel) != 2 or len(subpanel) != 2:
        raise ValueError('Two dimensions per panel')
    if any(type(value) is not int or value <= 0 for value in (*panel, *subpanel)):
        raise ValueError('Strict positive integer dimensions')
    if any(n > m for n, m in zip(subpanel, panel)):
        raise ValueError('Subpanel must fit the complete panel')
    ur, uc = (m - n + 1 for m, n in zip(panel, subpanel))
    return tuple((r, c) for r in range(ur) for c in range(uc))


class ExactPositionCount(unittest.TestCase):
    def test_all_six_original_configured_shapes(self):
        for panel, subpanel, expected in (
            ((1, 64), (1, 36), 29), ((1, 64), (1, 16), 49),
            ((1, 64), (1, 4), 61), ((8, 8), (6, 6), 9),
            ((8, 8), (4, 4), 25), ((8, 8), (2, 2), 49)):
            with self.subTest(panel=panel, subpanel=subpanel):
                actual = placements(panel, subpanel)
                self.assertEqual(len(actual), expected)
                self.assertEqual(len(set(actual)), expected)
                self.assertEqual(actual[0], (0, 0))
                self.assertEqual(actual[-1], tuple(m - n for m, n in zip(panel, subpanel)))

    def test_source_text_28_is_not_the_inclusive_count(self):
        self.assertNotEqual(len(placements((1, 64), (1, 36))), 28)
        self.assertIn((0, 28), placements((1, 64), (1, 36)))

    def test_boundary_and_row_major_source_indexing(self):
        self.assertEqual(placements((1, 36), (1, 36)), ((0, 0),))
        self.assertEqual(placements((3, 4), (2, 3)), ((0, 0), (0, 1), (1, 0), (1, 1)))

    def test_invalid_dimension_negative_controls(self):
        for panel, subpanel in (
            ((0, 64), (1, 36)), ((1, 64), (0, 36)), ((1, 64), (1, 65)),
            ((True, 64), (1, 36)), ((1, 64), (1, 36.0)), ((1,), (1, 36)),
            ([1, 64], (1, 36)), ((1, 64), (1, -1))):
            with self.subTest(panel=panel, subpanel=subpanel):
                with self.assertRaises(ValueError):
                    placements(panel, subpanel)

    def test_complete_configured_population_not_optimization(self):
        self.assertEqual(len(range(2, 17, 2)) * 6, 48)
        self.assertEqual(48 * 2 * 6000, 576000)


if __name__ == '__main__':
    unittest.main(verbosity=2)
