"""Deterministic stop-semantics tests, not scientific or figure acceptance."""
import importlib.util
from pathlib import Path
import sys
import unittest
import numpy as np

HERE = Path(__file__).resolve().parent
ORIGINAL = HERE.parents[1] / "strict" / "mis-communications" / "engine.py"
spec = importlib.util.spec_from_file_location("mis_original_engine", ORIGINAL)
engine = importlib.util.module_from_spec(spec)
spec.loader.exec_module(engine)
sys.path.insert(0, str(HERE))
from boundary_stop_v1 import run_rcg

def options(policy):
    return dict(non_descent_policy=policy, line_search_policy="original_per_block_backtracking",
                initial_step=1., max_backtracks=12, backtrack_factor=.5,
                armijo_constant=1e-4, gradient_tolerance=1e-6, max_iterations=5)

def objective(z):
    g = {"X": np.array([[-1., 1.]])}
    return float(np.sum(z["X"] * g["X"])), g, {}

class Tests(unittest.TestCase):
    def test_boundary_literal_stop_is_not_reported_as_gradient(self):
        z={"X":np.array([[1.,0.]])}; opts=options("literal_printed")
        oldz, oldh, oldstop=engine.rcg(z, objective, opts)
        newz, newh, newstop=run_rcg(engine, z, objective, opts)
        self.assertEqual(oldstop["reason"],"gradient_tolerance")
        self.assertGreater(oldstop["gradient_norm"],opts["gradient_tolerance"])
        self.assertEqual(oldstop["projected_kkt_norm"],0.)
        self.assertEqual(newstop["reason"],"zero_projected_PR_direction")
        np.testing.assert_array_equal(newz["X"],oldz["X"])
        self.assertEqual(newh,oldh)
        for k in oldstop:
            if k!="reason": self.assertEqual(newstop[k],oldstop[k])
    def test_guarded_mode_preserves_valid_projected_stop(self):
        z={"X":np.array([[1.,0.]])};opts=options("documented_non_descent_restart")
        _,_,old=engine.rcg(z,objective,opts);_,_,new=run_rcg(engine,z,objective,opts)
        self.assertEqual(new,old);self.assertEqual(new["reason"],"gradient_tolerance")
        self.assertEqual(new["projected_kkt_norm"],0.)
    def test_interior_and_default_literal_are_unchanged(self):
        z={"X":np.array([[.5,.5]])};opts=options("literal_printed");opts["max_iterations"]=1
        old=engine.rcg(z,objective,opts);new=run_rcg(engine,z,objective,opts)
        np.testing.assert_array_equal(old[0]["X"],new[0]["X"])
        self.assertEqual(old[1],new[1]);self.assertEqual(old[2],new[2])
        opts.pop("non_descent_policy")
        _,_,new=run_rcg(engine,{"X":np.array([[1.,0.]])},objective,opts)
        self.assertEqual(new["reason"],"zero_projected_PR_direction")
    def test_unknown_policy_fails_before_any_evaluation(self):
        z={"X":np.array([[1.,0.]])}
        for invalid in ("typo", "", None, False, 1, []):
            opts=options(invalid); calls=[]
            def forbidden(x):
                calls.append(x)
                raise AssertionError("unexpected objective evaluation")
            with self.assertRaisesRegex(ValueError, "Unknown MIS non_descent_policy"):
                run_rcg(engine,z,forbidden,opts)
            self.assertEqual(calls,[])
            np.testing.assert_array_equal(z["X"],[[1.,0.]])

if __name__=="__main__": unittest.main()
