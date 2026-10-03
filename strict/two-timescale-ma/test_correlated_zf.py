"""Analytic tests of exact original-model inverse moments; no paper-bank claim."""
import json
import unittest
import numpy as np
from correlated_zf import reciprocal_gaussian_quadratic,correlated_jensen_bound
from run import scenario
from pathlib import Path


class CorrelatedZFTests(unittest.TestCase):
    def test_iid_central_exact_Wishart_limit_not_a_fit(self):
        for r in [2,3,4,6]:
            value,error=reciprocal_gaussian_quadratic(np.zeros(r),.7*np.eye(r))
            self.assertAlmostEqual(value,1/(.7*(r-1)),places=10)
            self.assertLess(error,1e-8)

    def test_unitary_and_channel_scale_invariance(self):
        mu=np.array([.3+.2j,-.5+.1j]);C=np.array([[.7,.1j],[-.1j,.4]])
        Q=np.array([[1,1j],[1j,1]])/np.sqrt(2)
        base,_=reciprocal_gaussian_quadratic(mu,C)
        rotated,_=reciprocal_gaussian_quadratic(Q@mu,Q@C@Q.conj().T)
        scaled,_=reciprocal_gaussian_quadratic(3*mu,9*C)
        self.assertAlmostEqual(base,rotated,places=11)
        self.assertAlmostEqual(base/9,scaled,places=11)

    def test_schur_complement_identity_full_N6_M5(self):
        rng=np.random.default_rng(241005912)
        H=(rng.normal(size=(6,5))+1j*rng.normal(size=(6,5)))/np.sqrt(2)
        inverse=np.linalg.inv(H.conj().T@H)
        for m in range(5):
            Q,_=np.linalg.qr(np.delete(H,m,axis=1),mode="complete")
            projected=Q[:,4:].conj().T@H[:,m]
            self.assertAlmostEqual(inverse[m,m].real,1/np.vdot(projected,projected).real,places=10)

    def test_original_full_1000_draw_covariance_scenario(self):
        folder=Path(__file__).parent;c0=json.loads((folder/"full_config.json").read_text())
        fixture=json.loads((folder/"fixture.json").read_text())
        c,t=scenario(c0,6,5,fixture["rician_linear"],geometry=fixture);t=np.asarray(fixture["positions"])
        rng=np.random.default_rng(777);z=(rng.normal(size=(1000,6,5))+1j*rng.normal(size=(1000,6,5)))/np.sqrt(2)
        result=correlated_jensen_bound(t,c,z)
        self.assertEqual(result["outer_expectation_samples"],1000)
        self.assertEqual(result["projected_complex_dimension"],2)
        self.assertFalse(result["modified_channel_or_Wishart_approximation"])
        self.assertFalse(result["printed_Eq74_closed_form_recovered"])
        self.assertTrue(np.isfinite(result["sum_rate"]))

    def test_rank_and_psd_errors_are_not_ridged(self):
        for C in [np.diag([1.,0.]),np.diag([1.,-1.])]:
            with self.assertRaises(ValueError):reciprocal_gaussian_quadratic(np.zeros(2),C)
        with self.assertRaises(ValueError):reciprocal_gaussian_quadratic(np.zeros(1),np.eye(1))


if __name__=="__main__":unittest.main(verbosity=2)
