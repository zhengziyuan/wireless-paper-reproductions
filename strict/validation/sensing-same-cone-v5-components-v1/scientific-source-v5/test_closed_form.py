"""Independent full-size finite-field identities, not original-figure matching."""
import json
import unittest
import numpy as np

from engine import Model, closed_form
from run import evaluate_closed


def original_nine_target_model():
    return Model({"ms1":[20,20],"ms2":[16,16],
        "azimuth_deg":np.tile([0.,45.,90.],3).tolist(),
        "elevation_deg":np.repeat([30.,50.,70.],3).tolist(),
        "spacing_over_wavelength":1/3,"incidence_direction_cosines":[0,0],
        "number_of_targets":9,"echo_beta_squared":1,"noise_over_power":1})


class ClosedFormTests(unittest.TestCase):
    def test_same_coordinate_reference_no_layer_only_offset(self):
        model=original_nine_target_model()
        z=closed_form(model)
        A=np.pi/(1/3)/4
        mr=np.array([(r,c) for r in range(20) for c in range(20)])
        nr=np.array([(r,c) for r in range(16) for c in range(16)])
        phi_expected=np.exp(-1j*A/9*np.sum(mr**2,axis=1))
        theta_expected=np.exp(1j*A/9*np.sum(nr**2,axis=1))
        np.testing.assert_allclose(z["phi"],phi_expected,atol=1e-13,rtol=0)
        np.testing.assert_allclose(z["theta"],theta_expected,atol=1e-13,rtol=0)
        self.assertEqual(z["phi"][0],1)
        self.assertEqual(z["theta"][0],1)
        self.assertGreater(np.max(np.abs(z["theta"]-np.exp(1j*A/9*np.sum((nr+4)**2,axis=1)))),1)

    def test_all_nine_original_law_schedules_not_SINR_selection(self):
        model=original_nine_target_model()
        result=evaluate_closed(model)
        self.assertEqual(result["selected_positions"],[10,6,2,15,12,3,20,18,4])
        X=np.asarray(result["state"]["X"])
        self.assertEqual(X.shape,(9,25))
        np.testing.assert_array_equal(np.sum(X,axis=1),np.ones(9))
        np.testing.assert_array_equal(np.argmax(X,axis=1),result["selected_positions"])
        self.assertFalse(result["original_figure_reproduction_certified"])
        self.assertIn("not_SINR_search",result["scheduling_rule"])

    def test_full_finite_padding_field_conjugacy_all_targets_all_positions(self):
        model=original_nine_target_model()
        z=closed_form(model)
        bar,v,q,powers=model.fields(z)
        self.assertEqual(bar.shape,(25,400))
        self.assertEqual(q.shape,(9,25))
        # Independent direct field for literal Section VI negative exponent
        # paired with positive / negative chirps at a shared zero origin.
        coords=np.array([(r,c) for r in range(20) for c in range(20)])
        local=np.array([(r,c) for r in range(16) for c in range(16)])
        az=np.deg2rad(model.config["azimuth_deg"])
        el=np.deg2rad(model.config["elevation_deg"])
        direction=np.column_stack((np.sin(el)*np.cos(az),np.sin(el)*np.sin(az)))
        c_negative=np.exp(-2j*np.pi/3*(direction@coords.T))
        phi_literal=np.exp(1j*np.pi/12*np.sum(coords**2,axis=1))
        theta_literal=np.exp(-1j*np.pi/12*np.sum(local**2,axis=1))
        v_literal=np.tile(phi_literal,(25,1))
        for u in range(25):
            r,col=divmod(u,5)
            ix=np.array([(r+i)*20+col+j for i in range(16) for j in range(16)])
            np.testing.assert_array_equal(model.indices[u],ix)
            v_literal[u,ix]*=theta_literal
            outside=np.ones(400,dtype=bool);outside[ix]=False
            np.testing.assert_array_equal(bar[u,outside],np.ones(144))
        q_literal=c_negative@v_literal.T
        np.testing.assert_allclose(v_literal,np.conj(v),atol=1e-12,rtol=0)
        np.testing.assert_allclose(q_literal,np.conj(q),atol=1e-10,rtol=0)
        np.testing.assert_allclose(np.abs(q_literal)**2,powers,atol=1e-8,rtol=0)

    def test_exact_finite_overlap_linear_phase_every_admissible_shift(self):
        model=original_nine_target_model()
        z=closed_form(model)
        _,v,_,_=model.fields(z)
        A=np.pi/(1/3)/4
        for u in range(25):
            r,c=divmod(u,5)
            coords=np.array([(r+i,c+j) for i in range(16) for j in range(16)])
            # This includes the global constant omitted by first-order Taylor.
            exact=np.exp(-1j*A/9*(2*coords@np.array([r,c])-r*r-c*c))
            np.testing.assert_allclose(v[u,model.indices[u]],exact,atol=1e-12,rtol=0)
            if r*r+c*c<=16:
                s=np.array([r/4,c/4])
                positive_response=np.exp(2j*np.pi/3*(coords@s))
                coherent=np.sum(positive_response*v[u,model.indices[u]])
                self.assertAlmostEqual(abs(coherent),256,places=10)

    def test_source_A_singular_boundary_still_fails_explicitly(self):
        model=original_nine_target_model()
        model.config["ms2"]=[20,16]
        with self.assertRaisesRegex(ValueError,"singular"):
            closed_form(model)


if __name__=="__main__":
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(ClosedFormTests)
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    print(json.dumps({"scope":"independent_closed_form_identity_tests_not_original_figure_reproduction",
        "full_dimensions":{"ms1":[20,20],"ms2":[16,16],"targets":9,"positions":25},
        "tests_run":result.testsRun,"all_passed":result.wasSuccessful(),
        "original_figure_reproduction_certified":False}))
    if not result.wasSuccessful():raise SystemExit(1)
