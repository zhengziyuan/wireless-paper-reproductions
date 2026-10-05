"""Exact source-theory witnesses; no solver, scientific imports or curve inputs.

These are mathematical counterexamples, not a reduced reproduction campaign.
They do not identify the cause of any current full-scene failure.
"""
from fractions import Fraction as Q
import math
import unittest


def complex_product(a, b):
    return (a[0]*b[0]-a[1]*b[1], a[0]*b[1]+a[1]*b[0])


def complex_norm_squared(z):
    return z[0]*z[0]+z[1]*z[1]


def phase_pr_witness():
    """Original physical SMS phase objective, original projection and PR.

    M64, K1, U1, c_m=1, X=1, theta empty, iota=169/10240.
    Half the phases are z0 and half conjugate(z0). The iota is a
    declared theorem witness, not Fig11's fixed .01 production setting.
    F=-iota*|sum(phi)|^2 is precisely the minimized negative softmin at K1.
    """
    M = 64
    iota = Q(169, 10240)
    z0 = (Q(12, 13), Q(5, 13))
    a0 = 2*iota*M*z0[0]*z0[1]
    factor = (Q(4, 5), Q(-3, 5))
    z1 = complex_product(z0, factor)
    F0 = -iota*(M*z0[0])**2
    F1 = -iota*(M*z1[0])**2
    a1 = 2*iota*M*z1[0]*z1[1]
    cosine = factor[0]
    old_direction_transported = -a0*cosine
    beta = (a1*a1-a1*a0*cosine)/(a0*a0)
    d1 = -a1+beta*old_direction_transported
    raw_slope1 = M*a1*d1
    raw_prediction0 = -M*a0*a0
    chord_prediction0 = -M*a0*(-factor[1])
    c = Q(1, 10000)
    return {
        'M': M, 'K': 1, 'U': 1, 'iota': iota,
        'z0': z0, 'z1': z1, 'a0': a0, 'a1': a1,
        'F0': F0, 'F1': F1, 'difference0': F1-F0,
        'raw_prediction0': raw_prediction0,
        'chord_prediction0': chord_prediction0,
        'armijo_constant': c, 'beta': beta,
        'old_direction_transported': old_direction_transported,
        'direction1': d1, 'raw_slope1': raw_slope1,
        'first_step_raw_armijo': F1-F0 <= c*raw_prediction0,
        'first_step_chord_armijo': F1-F0 <= c*chord_prediction0,
        'raw_PR_is_non_descent': raw_slope1 > 0,
        'all_0_lt_alpha_le_1_increase_F':
            z1[0] > d1*z1[1] > 0 and d1 < 0 and z1[1] < 0,
        'current_guard_would_restart': raw_slope1 >= 0,
        'not_current_Fig11_configuration': True,
        'not_actual_failure_cause': True,
    }


def json_exact(value):
    if isinstance(value, Q):
        return {'numerator': value.numerator, 'denominator': value.denominator}
    if isinstance(value, dict):
        return {k: json_exact(v) for k, v in value.items()}
    if isinstance(value, (tuple, list)):
        return [json_exact(v) for v in value]
    return value


class ExactControls(unittest.TestCase):
    def test_original_physical_gradient_and_normalization(self):
        w = phase_pr_witness()
        self.assertEqual(w['a0'], Q(3, 4))
        self.assertEqual(w['a1'], Q(-63, 125))
        self.assertEqual(w['z1'], (Q(63, 65), Q(-16, 65)))
        self.assertEqual(complex_norm_squared(w['z0']), 1)
        self.assertEqual(complex_norm_squared(w['z1']), 1)
        self.assertEqual(w['F0'], Q(-288, 5))
        self.assertEqual(w['F1'], Q(-7938, 125))

    def test_actual_previous_Armijo_then_original_PR_ascent(self):
        w = phase_pr_witness()
        self.assertEqual(w['difference0'], Q(-738, 125))
        self.assertEqual(w['raw_prediction0'], -36)
        self.assertEqual(w['chord_prediction0'], Q(-144, 5))
        self.assertTrue(w['first_step_raw_armijo'])
        self.assertTrue(w['first_step_chord_armijo'])
        self.assertEqual(w['beta'], Q(15456, 15625))
        self.assertEqual(w['direction1'], Q(-6993, 78125))
        self.assertEqual(w['raw_slope1'], Q(28195776, 9765625))
        self.assertTrue(w['raw_PR_is_non_descent'])
        self.assertTrue(w['all_0_lt_alpha_le_1_increase_F'])
        self.assertTrue(w['current_guard_would_restart'])

    def test_wrong_PR_sign_and_missing_transport_are_detectable(self):
        w = phase_pr_witness()
        wrong_beta_sign_d = -w['a1']-w['beta']*w['old_direction_transported']
        self.assertLess(w['a1']*wrong_beta_sign_d, 0)
        without_transport = -w['a1']+w['beta']*(-w['a0'])
        self.assertNotEqual(without_transport, w['direction1'])
        self.assertNotEqual(w['F1']-w['F0'], w['F0']-w['F1'])

    def test_stationary_does_not_imply_local_SNR_maximum(self):
        q_before = (Q(0), Q(0))
        q_after = (Q(-2, 5), Q(4, 5))
        self.assertEqual(complex_norm_squared(q_before), 0)
        self.assertEqual(complex_norm_squared(q_after), Q(4, 5))
        self.assertEqual(complex_norm_squared((Q(3, 5), Q(4, 5))), 1)

    def test_open_simplex_and_closed_projection_are_distinct(self):
        x = (Q(1, 2), Q(1, 2))
        tangent = (Q(1), Q(-1))
        trial = tuple(a+b for a, b in zip(x, tangent))
        projected = tuple(max(v-Q(1, 2), Q(0)) for v in trial)
        self.assertEqual(sum(tangent), 0)
        self.assertEqual(projected, (Q(1), Q(0)))
        self.assertFalse(all(v > 0 for v in projected))

    def test_exact_field_increment_identity_not_objective_substitution(self):
        oldbar, newbar = (Q(3, 5), Q(4, 5)), (Q(5, 13), Q(12, 13))
        oldphi, newphi = (Q(12, 13), Q(5, 13)), (Q(4, 5), Q(-3, 5))
        oldv = complex_product(oldbar, oldphi)
        newv = complex_product(newbar, newphi)
        dv1 = complex_product(oldbar, tuple(b-a for a, b in zip(oldphi, newphi)))
        dv2 = complex_product(tuple(b-a for a, b in zip(oldbar, newbar)), newphi)
        dv = tuple(a+b for a, b in zip(dv1, dv2))
        self.assertEqual(dv, tuple(b-a for a, b in zip(oldv, newv)))
        da = 2*(oldv[0]*dv[0]+oldv[1]*dv[1])+complex_norm_squared(dv)
        self.assertEqual(da, complex_norm_squared(newv)-complex_norm_squared(oldv))
        self.assertEqual(da, 0)

    def test_binary64_small_candidate_can_be_identical_without_stationarity(self):
        alpha = 2.0**-59
        z, a = (0.6, 0.8), 1e-6
        d = (-0.8*a, 0.6*a)
        candidate = tuple(v+alpha*s for v, s in zip(z, d))
        h = math.hypot(*candidate)
        candidate = tuple(v/h for v in candidate)
        self.assertEqual(h, 1.0)
        self.assertEqual(candidate, z)
        self.assertGreater(sum(v*v for v in d), 0)
        self.assertEqual(sum((b-a)*s for a, b, s in zip(z, candidate, d)), 0)

    def test_naive_binary64_offset_cancellation_not_stable_increment_failure(self):
        base, exact_increment = Q(64), Q(-1, 2**60)
        self.assertEqual(float(base+exact_increment)-float(base), 0)
        self.assertLess(exact_increment, 0)
        self.assertNotEqual(float(exact_increment), 0)

    def test_last_trial_and_post_failure_recorded_alpha_are_different(self):
        alpha, last_trial = Q(1), None
        for _ in range(60):
            last_trial = alpha
            alpha *= Q(1, 2)
        self.assertEqual(last_trial, Q(1, 2**59))
        self.assertEqual(alpha, Q(1, 2**60))

    def test_MIS_lift_has_strict_positive_X_and_zero_other_block_gradients(self):
        # M1x64, N1x1, U64, K1; all c=1, theta=1, all X=1/64.
        # A one-element transmitting surface shifted through64 positions
        # gives bar_theta=ones64; every beam has the same field q.
        w = phase_pr_witness()
        U, x = 64, Q(1, 64)
        self.assertGreater(x, 0)
        self.assertEqual(U*x, 1)
        for z, expected_F in ((w['z0'], w['F0']), (w['z1'], w['F1'])):
            phases = [z]*32+[(z[0], -z[1])]*32
            field = tuple(sum(phi[k] for phi in phases) for k in (0, 1))
            self.assertEqual(field, (64*z[0], Q(0)))
            gamma = w['iota']*complex_norm_squared(field)
            self.assertEqual(-sum(x*gamma for _ in range(U)), expected_F)
            self.assertEqual(gamma-sum(gamma for _ in range(U))/U, 0)
            mean_conjugate_phase = (sum(phi[0]*x for phi in phases),
                                    -sum(phi[1]*x for phi in phases))
            theta_ambient = tuple(-2*w['iota']*v for v in
                                  complex_product(field, mean_conjugate_phase))
            theta_projected = (theta_ambient[0]-theta_ambient[0], theta_ambient[1])
            self.assertEqual(theta_projected, (Q(0), Q(0)))
            ambient = (-2*w['iota']*field[0], Q(0))
            expected_a = w['a0'] if z == w['z0'] else w['a1']
            for index, phi in enumerate(phases):
                radial = ambient[0]*phi[0]+ambient[1]*phi[1]
                gradient = tuple(ambient[k]-radial*phi[k] for k in (0, 1))
                tangent = (-phi[1], phi[0])
                coefficient = sum(a*b for a, b in zip(gradient, tangent))
                self.assertEqual(coefficient, expected_a if index < 32 else -expected_a)


def run_controls():
    result = unittest.TestResult()
    unittest.defaultTestLoader.loadTestsFromTestCase(ExactControls).run(result)
    return dict(tests_run=result.testsRun, errors=len(result.errors),
        failures=len(result.failures), error_details=result.errors,
        failure_details=result.failures, passed=result.wasSuccessful(),
        witness=json_exact(phase_pr_witness()),
        scope='exact theory plus explicitly synthetic host controls; not a scientific campaign',
        actual_current_failure_cause='UNKNOWN', production_changed=False,
        full_figure_scientific_success=False, reference_agreement_verified=False)


if __name__ == '__main__':
    import json
    result = run_controls()
    print(json.dumps(result, indent=2, ensure_ascii=False))
    raise SystemExit(0 if result['passed'] else 1)
