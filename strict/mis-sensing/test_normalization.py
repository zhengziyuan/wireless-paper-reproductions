"""Exact full-size power/reference/waveform identities, not original figures."""
import copy
import json
import math
import unittest
import numpy as np
import run
from normalization import normalization_contract, matched_filter_effective_ratio


class NormalizationTests(unittest.TestCase):
    def setUp(self):
        self.settings=json.loads((run.HERE/"settings.json").read_text())
        self.point=dict(ms1=[10,10],ms2=[8,8],Kphi=2,Ktheta=2,power_dbm=30)
        model=run.make_model(self.point,self.settings)
        self.state=dict(phi=np.exp(1j*np.arange(model.M)*.347),
                        theta=np.exp(1j*np.arange(model.N)*.127))

    def test_watt_milliwatt_reference_invariance(self):
        mw=copy.deepcopy(self.settings);mw["reference_echo_unit"]="inverse_milliwatt"
        watt=copy.deepcopy(mw);watt.update(reference_echo_unit="inverse_watt",reference_echo_db=-43.88)
        first=normalization_contract(mw);second=normalization_contract(watt)
        self.assertEqual(first["physical_power_watt"],1.)
        self.assertEqual(first["reference_echo_ratio_per_watt"],second["reference_echo_ratio_per_watt"])
        np.testing.assert_allclose(run.make_model(self.point,mw).metric(self.state,"sinr"),
                                   run.make_model(self.point,watt).metric(self.state,"sinr"),rtol=1e-13)

    def test_raw_and_processed_matched_filter_equivalence(self):
        raw=copy.deepcopy(self.settings);raw["effective_reference_gain_factor"]=100
        processed=copy.deepcopy(self.settings)
        processed.update(reference_echo_db=-53.88,reference_echo_noise_domain="processed",
                         effective_reference_gain_factor=1)
        np.testing.assert_allclose(run.make_model(self.point,raw).metric(self.state,"sinr"),
                                   run.make_model(self.point,processed).metric(self.state,"sinr"),rtol=1e-12)
        model=run.make_model(self.point,raw)
        powers=model.beta[:,None]*model.fields(self.state)[3]**2
        Tp=100;P=1.;noise_sample=1.
        direct=Tp**2*P*powers/(Tp**2*P*(np.sum(powers,axis=0)[None,:]-powers)+Tp*noise_sample)
        np.testing.assert_allclose(direct,model.metric(self.state,"sinr"),rtol=1e-13)
        self.assertAlmostEqual(matched_filter_effective_ratio(10**(-73.88/10),Tp),10**(-53.88/10),places=17)

    def test_beta_squared_power_coefficient_is_not_squared_twice(self):
        model=run.make_model(self.point,self.settings)
        expected=10**(-73.88/10)
        np.testing.assert_array_equal(model.beta,np.full(model.K,expected))
        self.assertNotEqual(model.beta[0],expected**2)

    def test_default_literal_and_candidate_are_distinct_explicit_contracts(self):
        candidate=json.loads((run.HERE/"settings_reference_candidate.json").read_text())
        self.assertEqual(self.settings["effective_reference_gain_factor"],1)
        self.assertEqual(candidate["effective_reference_gain_factor"],100)
        self.assertIn("NOT_author_PRI_count_verified",candidate["normalization_status"])
        for key in ["number_of_starts","outer_iterations","rcg_max_iterations","epsilon_min","line_search"]:
            self.assertEqual(candidate[key],self.settings[key])
        norm=normalization_contract(candidate)
        self.assertEqual(norm["physical_power_watt"],1.)
        self.assertEqual(norm["noise_over_power"],.01)
        self.assertFalse(norm["physical_processing_origin_verified"])

    def test_double_counting_invalid_gain_and_missing_units_are_rejected(self):
        variants=[]
        x=copy.deepcopy(self.settings);x.update(reference_echo_noise_domain="processed",effective_reference_gain_factor=100);variants.append(x)
        x=copy.deepcopy(self.settings);x.pop("reference_echo_unit");variants.append(x)
        for value in [0,-1,math.nan,math.inf]:
            x=copy.deepcopy(self.settings);x["effective_reference_gain_factor"]=value;variants.append(x)
        for value in variants:
            with self.assertRaises(ValueError):normalization_contract(value)

    def test_effective_products_cannot_overflow_or_underflow(self):
        for changes in [dict(reference_echo_db=1000,effective_reference_gain_factor=1e300),
                        dict(reference_echo_db=-1000,effective_reference_gain_factor=1e-300),
                        dict(power_dbm=1000,effective_reference_gain_factor=1e300),
                        dict(power_dbm=-2000,effective_reference_gain_factor=1e-300),
                        dict(reference_echo_db=4000),dict(power_dbm=4000)]:
            settings=copy.deepcopy(self.settings);settings.update(changes)
            with self.assertRaises(ValueError):normalization_contract(settings)


if __name__=="__main__":unittest.main()
