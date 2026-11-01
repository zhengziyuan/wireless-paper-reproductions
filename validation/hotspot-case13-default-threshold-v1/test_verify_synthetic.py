"""Synthetic arithmetic boundary tests; no historical data is loaded."""
from fractions import Fraction as F
import sys
from pathlib import Path
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parent))
import verify_saved_threshold as m


class Tests(unittest.TestCase):
    def test_power_bound_exact_proof(self):
        self.assertLess(199**10,1000*100**10)
    def test_K_and_full_interference_are_distinct(self):
        gains=[F(100),F(2)]+[F(0)]*14
        x=m.flags(gains,F(1),1)
        self.assertFalse(x['K_only_proved_below_1_99'])  # unknown, not a pass
        self.assertTrue(x['full_J_proved_below_1_99'])
    def test_exact_threshold_is_not_strict_witness(self):
        gains=[F(0),F(199,100)]+[F(0)]*14
        x=m.flags(gains,F(1),1)
        self.assertFalse(x['K_only_proved_below_1_99'])
        self.assertFalse(x['full_J_proved_below_1_99'])
    def test_strict_below_and_invalid_inputs(self):
        gains=[F(0),F(198,100)]+[F(0)]*14
        self.assertTrue(m.flags(gains,F(1),1)['K_only_proved_below_1_99'])
        for bad in (F(0),F(-1)):
            with self.assertRaises(ValueError):m.flags(gains,bad,1)
        with self.assertRaises(ValueError):m.flags([F(-1)]+gains[1:],F(1),1)

if __name__=='__main__':unittest.main()
