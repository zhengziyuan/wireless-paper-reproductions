"""Exact algebraic counterexamples, not reduced paper simulations."""
from fractions import Fraction
import unittest
from audit_rician_source_coefficient import coefficients


class SourceCoefficient(unittest.TestCase):
    def test_declared_beta10_has_tenfold_scatter_variance_conflict(self):
        c=coefficients(10)
        self.assertEqual(c['printed_G_NLoS_power'],Fraction(10,11))
        self.assertEqual(c['normalized_NLoS_power'],Fraction(1,11))
        self.assertEqual(c['printed_G_NLoS_power']/c['normalized_NLoS_power'],10)

    def test_declared_beta100_has_hundredfold_conflict(self):
        c=coefficients(100)
        self.assertEqual(c['printed_G_NLoS_power']/c['normalized_NLoS_power'],100)
        self.assertEqual(c['LoS_power']+c['printed_G_NLoS_power'],Fraction(200,101))
        self.assertEqual(c['LoS_power']+c['normalized_NLoS_power'],1)

    def test_beta_one_coincidence_and_Rayleigh_limit_are_distinct(self):
        c=coefficients(1)
        self.assertEqual(c['printed_G_NLoS_power'],c['normalized_NLoS_power'])
        c=coefficients(0)
        self.assertEqual(c['printed_G_NLoS_power'],0)
        self.assertEqual(c['normalized_NLoS_power'],1)


if __name__=='__main__':unittest.main()
