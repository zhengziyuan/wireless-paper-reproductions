"""Hand-solvable non-Gaussian and deterministic limits of the stable moments."""
import unittest
import numpy as np
from positive_wick import moments,evaluate_mr


def scalar_data():
    return dict(d_mean=np.zeros((1,1,1),complex),d_var=np.array([[4.]]),
        G_mean=np.ones((1,1,1,1),complex),G_var=np.array([[2.]]),
        r_mean=np.zeros((1,1),complex),r_var=np.array([3.]),
        gt_second=np.zeros((1,1,1,1),complex),geo_d_mean=np.zeros(1,complex),
        geo_d_var=np.zeros(1),geo_G_mean=np.zeros((1,1),complex),geo_G_var=np.zeros(1))


class PositiveWick(unittest.TestCase):
    def test_exact_scalar_product_preserves_nongaussian_fourth_moment(self):
        # d~CN(0,4), G~CN(1,2), r~CN(0,3), independent.
        # E|d+Gr|²=13; E|d+Gr|⁴=32+144+17*18=482.
        x=moments(scalar_data(),np.ones((1,1),complex))
        self.assertEqual(x['tts_power'][0,0],13)
        self.assertEqual(x['fourth'][0,0],482)
        self.assertEqual(x['tts_own'][0,0],313)
        self.assertNotEqual(x['fourth'][0,0],2*13**2)

    def test_same_original_penalty_and_noise_are_retained(self):
        x=evaluate_mr(scalar_data(),np.ones((1,1),complex),np.ones((1,1)),1.,np.ones(1),True)
        self.assertEqual(x['numerator'][0],169)
        self.assertEqual(x['denominator'][0],314)
        self.assertEqual(x['criterion'],169/314-1)
        np.testing.assert_array_equal(x['gradient'],np.zeros((1,1)))

    def test_deterministic_limit_has_zero_own_variance(self):
        d=scalar_data();d['d_mean'][:]=2+3j;d['r_mean'][:]=1-2j
        for key in ('d_var','G_var','r_var'):d[key][:]=0
        x=moments(d,np.array([[1j]]))
        self.assertEqual(x['tts_own'][0,0],0)
        self.assertEqual(x['fourth'][0,0],x['tts_power'][0,0]**2)


if __name__=='__main__':unittest.main()
