"""Exact coordinate-subproblem identities and conditioning regressions."""
import json
from pathlib import Path
import unittest
import numpy as np
from core import mrt_statistics,zf_statistics,zf_surrogate,solve_coordinate
from run import scenario


class CoordinateScalingTests(unittest.TestCase):
    def setUp(self):
        self.folder=Path(__file__).parent
        self.config=json.loads((self.folder/"full_config.json").read_text())
        self.fixtures=json.loads((self.folder/"conditioning_fixtures.json").read_text())

    def test_source_objective_identities_on_full_N6_M5(self):
        for fixture in self.fixtures:
            c,_=scenario(self.config,fixture["N"],fixture["M"],fixture["kappa"],fixture["power"],fixture["A"],fixture["geometry"])
            t=np.asarray(fixture["positions"]);n=fixture["antenna"]
            for delta in [np.zeros(2),np.array([1e-5,-2e-5]),np.array([-3e-5,4e-5])]:
                if fixture["mode"]=="MRT":
                    value,g,curvature,_=mrt_statistics(t,c,n);scale=np.sqrt(max(curvature,1));u=scale*delta
                    original=value+g[n]@delta-curvature/2*(delta@delta)
                    transformed=g[n]@(u/scale)-curvature/2*((u/scale)@(u/scale))+value
                else:
                    _,_,_,eta=zf_statistics(t,c);s=zf_surrogate(t,c,n);scale=np.sqrt(max(s["curvature"].max(),1));u=scale*delta
                    original_minor=s["chi"]+s["f0"]+s["gradient"]@delta-s["curvature"]/2*(delta@delta)
                    transformed_minor=s["ratio"]+s["gradient"]@(u/scale)-s["curvature"]/2*((u/scale)@(u/scale))
                    original=np.log2(1+eta*original_minor).sum()
                    transformed=np.log2(transformed_minor+1/eta).sum()+np.log2(eta).sum()
                self.assertAlmostEqual(original,transformed,places=10)

    def test_original_failed_coordinates_solve_without_relaxation(self):
        for fixture in self.fixtures:
            c,_=scenario(self.config,fixture["N"],fixture["M"],fixture["kappa"],fixture["power"],fixture["A"],fixture["geometry"])
            t=np.asarray(fixture["positions"]);trial,record=solve_coordinate(t,c,fixture["antenna"],fixture["mode"])
            self.assertEqual(record["solver_status"],"certified_global_2d")
            self.assertTrue(record["original_subproblem_unchanged"])
            self.assertGreaterEqual(record["after"],record["before"]-c["verification_tolerance"])
            self.assertGreaterEqual(record["lower_bound_gap"],-c["verification_tolerance"])
            self.assertLessEqual(record["certificate"]["global_objective_gap_upper_bound"],record["certificate"]["global_objective_gap_tolerance"])
            distance=np.linalg.norm(trial[:,None]-trial[None,:],axis=2)+np.eye(len(t))*1e9
            self.assertGreaterEqual(distance.min(),.5-c["verification_tolerance"])


if __name__=="__main__":unittest.main(verbosity=2)
