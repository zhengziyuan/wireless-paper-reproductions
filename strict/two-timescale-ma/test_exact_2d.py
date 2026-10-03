"""Global coordinate-oracle algebra and full-size geometry checks, not figures."""
import json
from pathlib import Path
import unittest
import numpy as np
from coordinate_exact import solve,polygon
from core import mrt_statistics,zf_statistics,zf_surrogate,solve_coordinate
from run import scenario


class Exact2DTests(unittest.TestCase):
    def setUp(self):
        folder=Path(__file__).parent;self.config=json.loads((folder/"full_config.json").read_text())
        fixture=json.loads((folder/"fixture.json").read_text());self.c,self.t=scenario(self.config,6,5,fixture["rician_linear"],geometry=fixture)
        self.t=np.asarray(fixture["positions"])

    def test_flat_and_linear_singular_MRT_include_all_box_spacing_corners(self):
        for g in [np.zeros(2),np.array([.3,-.7])]:
            delta,certificate=solve(self.t,self.c,0,"MRT",gradient=g,curvature=0.,objective_before=1.)
            A,b,vertices,tolerance=polygon(self.t,self.c,0)
            self.assertLessEqual(np.max(A@delta-b),tolerance)
            self.assertAlmostEqual(g@delta,float(np.max(vertices@g)),places=11)
            self.assertLessEqual(certificate["global_objective_gap_upper_bound"],certificate["global_objective_gap_tolerance"])
            if np.linalg.norm(g)==0:self.assertEqual(float(delta@delta),0.)

    def test_full_N6_M5_original_gradient_and_hessian_independent_differences(self):
        n=0;s=zf_surrogate(self.t,self.c,n);_,_,_,eta=zf_statistics(self.t,self.c);a=s["ratio"]+1/eta;G=s["gradient"];q=s["curvature"]
        def objective(x):return np.log2(a+G@x-q/2*(x@x)).sum()
        def gradient(x):
            r=a+G@x-q/2*(x@x);return np.sum((G-q[:,None]*x)/r[:,None],axis=0)/np.log(2)
        epsilon=1e-6;x=np.array([2e-5,-3e-5]);r=a+G@x-q/2*(x@x);V=G-q[:,None]*x
        H=-(np.sum(q/r)*np.eye(2)+V.T@((1/r**2)[:,None]*V))/np.log(2)
        numerical_gradient=np.array([(objective(x+epsilon*e)-objective(x-epsilon*e))/(2*epsilon) for e in np.eye(2)])
        numerical_H=np.column_stack([(gradient(x+epsilon*e)-gradient(x-epsilon*e))/(2*epsilon) for e in np.eye(2)])
        np.testing.assert_allclose(gradient(x),numerical_gradient,rtol=1e-6,atol=2e-7)
        np.testing.assert_allclose(H,numerical_H,rtol=1e-6,atol=1e-5)
        self.assertLess(float(np.linalg.eigvalsh(H)[-1]),0.)

    def test_every_full_size_coordinate_both_original_algorithms_certified(self):
        for mode in ["MRT","ZF"]:
            for n in range(6):
                trial,record=solve_coordinate(self.t,self.c,n,mode);cert=record["certificate"]
                self.assertLessEqual(cert["global_objective_gap_upper_bound"],cert["global_objective_gap_tolerance"])
                self.assertLessEqual(cert["maximum_normalized_constraint_violation"],cert["normalized_constraint_tolerance"])
                self.assertGreaterEqual(record["lower_bound_gap"],-self.c["verification_tolerance"])

    def test_infeasible_coincident_antenna_does_not_get_ridge_or_clamp(self):
        t=self.t.copy();t[1]=t[0]
        with self.assertRaises(ValueError):solve(t,self.c,0,"MRT",gradient=np.ones(2),curvature=1.,objective_before=1.)


if __name__=="__main__":unittest.main(verbosity=2)
