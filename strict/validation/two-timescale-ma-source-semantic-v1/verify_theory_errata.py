"""Portable exact-rational theory controls, NOT a full-paper simulation.

Seven whole original STD mathematical test bodies are mechanically copied;
private-file source-pin test and machine-local receipt writer are excluded.
No NumPy/MATLAB/optimizer/paper-data execution or reference closeness claim.
"""
import unittest
from fractions import Fraction as F


def dot(left, right):
    return sum((F(x) * F(y) for x, y in zip(left, right)), F(0))


class ExactRationalControls(unittest.TestCase):
    def test_01_remark4_counterexample_and_exact_woodbury(self):
        n, kap = 2, F(1)
        lambda1 = 1 / (kap + 1)
        lambda2_squared = kap / (kap + 1)
        sigma = lambda1 + lambda2_squared * F(n, n)
        theta = lambda1 + lambda2_squared * F(n - 1, n)
        inv_sigma, inv_theta = 1 / sigma, 1 / theta
        subtraction = (inv_theta ** 2 * lambda2_squared) / (n + lambda2_squared * inv_theta)
        self.assertEqual((sigma, theta, inv_sigma, inv_theta), (F(1), F(3, 4), F(1), F(4, 3)))
        self.assertEqual(subtraction, F(1, 3))
        self.assertEqual(inv_theta - subtraction, inv_sigma)
        self.assertNotEqual(inv_theta, inv_sigma)  # purported FPA equality is false

    def test_02_remark4_rayleigh_degeneracy_and_positive_kappa_family(self):
        for n in (2, 3, 6):
            for kap in (F(0), F(1, 2), F(1), F(6), F(100)):
                sigma = 1 / (kap + 1) + kap / (kap + 1)
                theta = 1 / (kap + 1) + kap / (kap + 1) * F(n - 1, n)
                self.assertEqual(sigma, F(1))
                if kap == 0:
                    self.assertEqual(theta, sigma)
                else:
                    self.assertLess(theta, sigma)
                    self.assertGreater(1 / theta, 1 / sigma)

    def test_03_eq29b_psd_matrix_exact_characteristic_polynomial(self):
        a = b = c = F(1)
        printed_radicand = (a - c) ** 2 - 4 * b ** 2
        correct_radicand = (a - c) ** 2 + 4 * b ** 2
        self.assertEqual((printed_radicand, correct_radicand), (F(-4), F(4)))
        self.assertLess(printed_radicand, 0)
        for eigenvalue in (F(0), F(2)):
            self.assertEqual((a - eigenvalue) * (c - eigenvalue) - b ** 2, 0)
        self.assertEqual((a + c + F(2)) / 2, F(2))

    def test_04_mrt_common_instantaneous_coefficient_not_equal_user_power(self):
        power, channel_norms_squared = F(2), (F(1), F(3))
        common_p = power / sum(channel_norms_squared)
        physical_powers = tuple(common_p * energy for energy in channel_norms_squared)
        self.assertEqual(common_p, F(1, 2))
        self.assertEqual(physical_powers, (F(1, 2), F(3, 2)))
        self.assertEqual(sum(physical_powers), power)
        self.assertNotEqual(physical_powers, (power / 2, power / 2))
        self.assertEqual(power / (2 * sum(channel_norms_squared)), F(1, 4))

    def test_05_zf_pseudoinverse_and_projection_exact_direction(self):
        # N=3,M=2, H=[(1,0,0),(1,1,0)]; full rank. No numerical matrix library.
        h1, h2 = (1, 0, 0), (1, 1, 0)
        v1, v2 = (1, -1, 0), (0, 1, 0)
        r1 = (F(1, 2), F(-1, 2), F(0))
        r2 = (F(0), F(1), F(0))
        for h, v, desired in ((h1, v1, 1), (h2, v1, 0), (h1, v2, 0), (h2, v2, 1)):
            self.assertEqual(dot(h, v), desired)
        self.assertEqual(tuple(x / dot(r1, r1) for x in r1), tuple(F(x) for x in v1))
        self.assertEqual(tuple(x / dot(r2, r2) for x in r2), tuple(F(x) for x in v2))
        self.assertEqual((dot(v1, v1), dot(v2, v2)), (F(2), F(1)))
        self.assertEqual(sum((F(2, 2), F(2, 2))), F(2))  # normalized per-user P/M

    def test_06_power_units_and_mrt_mean_ratio_semantics(self):
        noise_watts = F(1, 10 ** 11)  # 10^((-80-30)/10)
        mistaken_dbw = F(1, 10 ** 8)
        beta0_power_gain = F(1, 10 ** 4)
        self.assertEqual(mistaken_dbw / noise_watts, F(1000))
        self.assertEqual(beta0_power_gain, F(10) ** -4)
        self.assertEqual(F(10) ** ((30 - 30) // 10), F(1))  # 30dBm=1W
        # M=1,kappa=0: design SNR rho*(N+1) exceeds the Jensen-bound SNR rho*N.
        # The expectation/log inequality is a written proof, not computed science.
        for n in (1, 2, 6):
            rho = F(1)
            self.assertGreater(rho * (n + 1), rho * n)

    def test_07_fpa_mrt_power_parameterization_and_angle_anisotropy(self):
        raw_coefficient, norm_squared = F(3, 2), F(2)
        physical_power = raw_coefficient * norm_squared
        self.assertEqual(physical_power / norm_squared, raw_coefficient)
        # Exact integrals for independent uniform theta,phi on [-pi/2,pi/2].
        sin2_mean, cos2_mean = F(1, 2), F(1, 2)
        ex_squared, ey_squared = cos2_mean * sin2_mean, sin2_mean
        self.assertEqual((ex_squared, ey_squared), (F(1, 4), F(1, 2)))
        self.assertNotEqual(ex_squared, ey_squared)



if __name__ == "__main__":
    unittest.main(verbosity=2)

