"""Full-draw position checks + no-partial-bank plotting contract.

These tests do NOT execute all300 geometries or claim full figure recovery.
"""
import json
from pathlib import Path
import unittest
import numpy as np
from corrected_figures import aggregate_records,held_matrix
from corrected_zf_position import evaluate_position,evaluator_fingerprint,position_evidence_complete
from correlated_zf import correlated_jensen_bound
from execute_bank import atomic_json
from figures import cases,make_job
from run import scenario


class CorrectedFigureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.folder=Path(__file__).parent;cls.config=json.loads((cls.folder/"full_config.json").read_text())
        (cls.folder/"outputs").mkdir(parents=True,exist_ok=True)

    def test_actual_full1000_both_original_dimensions_and_models(self):
        for figure,n in [(16,6),(14,8)]:
            job=make_job(cases(self.config,figure)[0],self.config,0)
            c,t=scenario(self.config,n,5,job["kappa"],job["power"],job["A"],job["geometry"])
            z=np.asarray(job["nlos_re"])+1j*np.asarray(job["nlos_im"])
            result=evaluate_position(t,c,z)
            result.update(mode="full1000_position_evidence_not_full_figure",figure=figure,evaluator_source_sha256=evaluator_fingerprint())
            atomic_json(self.folder/"outputs"/f"corrected-zf-position-n{n}-python.json",result)
            for model in ["iid","correlated"]:
                r=result["models"][model]
                self.assertEqual(len(r["actual_full1000_MC"]["sample_sum_rates"]),1000)
                self.assertEqual(np.shape(r["direct_MC_inverse_diagonal_samples"]),(1000,5))
                self.assertEqual(np.shape(r["exact_original_model_Jensen"]["conditional_quadrature_error_samples"]),(1000,5))
                self.assertTrue(r["all1000_times_M_Schur_identities_pass"])
                self.assertTrue(r["all1000_ZF_beamformer_rate_identities_pass"])
                self.assertFalse(r["finite_ensemble_bound_guaranteed"])
            self.assertFalse(result["trajectory_position_reoptimized"])
            self.assertTrue(position_evidence_complete(result,t,5))
            result["models"]["iid"]["actual_full1000_MC"]["sample_sum_rates"].pop()
            self.assertFalse(position_evidence_complete(result,t,5))

    def test_exact_iid_central_expectation_all1000_is_not_paper_approximation(self):
        job=make_job(cases(self.config,16)[0],self.config,0)
        c,t=scenario(self.config,6,5,0,job["power"],job["A"],job["geometry"])
        z=np.asarray(job["nlos_re"])+1j*np.asarray(job["nlos_im"])
        bound=correlated_jensen_bound(t,c,z,False)
        # Exact central iid Wishart inverse expectation: 1/(N-M)=1.
        np.testing.assert_allclose(bound["conditional_inverse_moment_samples"],np.ones((1000,5)),rtol=1e-10,atol=1e-10)
        expected=np.log2(1+c["power"]*np.asarray(c["beta"])/(5*np.asarray(c["noise"]))).sum()
        self.assertAlmostEqual(bound["sum_rate"],expected,places=10)

    def test_all100_histories_required_and_terminal_hold_explicit(self):
        with self.assertRaises(ValueError):held_matrix([[1,2]]*99)
        matrix=held_matrix([[1,2]]*50+[[3,4,5]]*50)
        np.testing.assert_allclose(matrix.mean(axis=0),[2,3,3.5])

    def test_all300_and_all_five_six_curve_panels_required(self):
        receipt={"figure":16};case_list=cases(self.config,16)
        by_case=[]
        for _ in case_list:
            items=[]
            for realization in range(100):
                model={key:[1.,2.+realization/100] for key in ["MC_mean","exact_population_Jensen_plugin","MC_minus_Jensen_plugin",
                    "Jensen_outer_MC_standard_error_delta_method","Jensen_quadrature_rate_error_estimate_first_order"]}
                items.append({"histories":{"iid":model,"correlated":model}})
            by_case.append(items)
        result=aggregate_records(receipt,case_list,by_case)
        self.assertEqual(len(result["panels"]),5)
        self.assertTrue(all(len(series)==6 for series in result["panels"].values()))
        self.assertFalse(result["historical_figure_recovery_claimed"])
        with self.assertRaises(ValueError):aggregate_records(receipt,case_list,[by_case[0],by_case[1],by_case[2][:-1]])


if __name__=="__main__":unittest.main(verbosity=2)
