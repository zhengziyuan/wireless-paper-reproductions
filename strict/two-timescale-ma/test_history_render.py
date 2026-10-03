"""Synthetic array-only rendering-contract test, never a paper curve receipt."""
import unittest
import numpy as np
from render_figures import terminal_hold_mean


class HistoryRenderTests(unittest.TestCase):
    def test_explicit_final_state_hold_preserves_all100_geometry_histories(self):
        histories=[[1.,2.] for _ in range(50)]+[[3.,4.,5.] for _ in range(50)]
        np.testing.assert_array_equal(terminal_hold_mean(histories),[2.,3.,3.5])

    def test_missing_or_nonfinite_history_never_becomes_zero_filled_curve(self):
        for histories in [[],[[1.],[]],[[1.],[np.nan]],[[1.],[np.inf]]]:
            with self.assertRaises(ValueError):terminal_hold_mean(histories)


if __name__=="__main__":unittest.main(verbosity=2)
