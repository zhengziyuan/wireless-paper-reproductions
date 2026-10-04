"""Exact source-NMSE raw-PR counterexample. No optimizer or paper simulation.

Only integer/Fraction arithmetic is needed. The counterexample concerns an
unconditional mathematical ascent claim, not the captured positive-slope
iteration 4614, a full scene, or the author's historical channels.
"""
from fractions import Fraction as F
from pathlib import Path
import argparse
import hashlib
import json
import unittest


def mul(a,b):
    return (a[0]*b[0]-a[1]*b[1],a[0]*b[1]+a[1]*b[0])


def add(a,b):
    return (a[0]+b[0],a[1]+b[1])


def scale(a,s):
    return (a[0]*s,a[1]*s)


def inner(a,b):
    return a[0]*b[0]+a[1]*b[1]


def project(theta,v):
    return add(v,scale(theta,-inner(theta,v)))


def evidence():
    # theta0=(1+10i)/sqrt(101); original quartic tangent gradient
    # g0=(-200+20i)/(101*sqrt(101)). At alpha=1 the normalized
    # theta1=(-99+1030i)/sqrt(1070701).
    q=99**2+1030**2
    assert q==1070701==101*10601
    gain=F(1,101)-F(99**2,q)
    old_norm2=F(200**2+20**2,101**3)
    requirement=F(1,10000)*old_norm2
    a1=F(-2*99*1030,q)
    # t0=20/sqrt(10601). This bracket is the EXACT second
    # raw-PR slope divided by a1^2, with the OLD norm denominator.
    # sqrt(10601)<103 => replace it by 103 for a strict upper bound.
    bracket_upper=F(400,10601)-F(203940*10201,2020*10601*103)
    slope_upper=a1*a1*bracket_upper
    return {'objective_on_unit_circle':'-Re(theta)^2',
        'source_amplitude':'1+conj(theta)','pd':1,'iota':2,'rho':1,
        'communication_power':0,'initial_alpha':1,'Armijo_c':'1/10000',
        'first_original_Armijo_gain_exact':str(gain),
        'first_original_Armijo_requirement_exact':str(requirement),
        'old_gradient_norm_squared_exact':str(old_norm2),
        'second_phase_gradient_coordinate_exact':str(a1),
        'second_raw_PR_slope_strict_rational_upper':str(slope_upper),
        'strict_integer_square_comparison':'10601 < 103^2',
        'first_original_Armijo_pass':gain>requirement>0,
        'second_raw_PR_direction_provably_non_ascent':10601<103**2 and slope_upper<0,
        'raw_PR_clipped_or_direction_restarted':False,
        'physical_scene_or_optimizer_executed':False,
        'actual_iteration4614_classified_non_ascent':False}


class ExactRawPRScope(unittest.TestCase):
    def test_source_quartic_reduces_to_claimed_circle_objective(self):
        theta=(F(3,5),F(4,5))
        self.assertEqual(inner(theta,theta),1)
        # |1+conj(theta)|^2 - iota*pd = 2*Re(theta), on the circle.
        amp=(1+theta[0],-theta[1])
        residual=inner(amp,amp)-2
        self.assertEqual(-residual**2/4,-theta[0]**2)
        original_ambient=scale(add(theta,(F(1),F(0))),-residual)
        simplified_ambient=(-2*theta[0],F(0))
        self.assertEqual(project(theta,original_ambient),project(theta,simplified_ambient))

    def test_first_original_step_normalization_and_Armijo_exact(self):
        # Common positive denominator cancels in element normalization.
        original_point_numerator=(101,1010)
        original_gradient_numerator=(-200,20)
        self.assertEqual(add(original_point_numerator,original_gradient_numerator),(-99,1030))
        e=evidence()
        self.assertEqual(F(e['old_gradient_norm_squared_exact']),F(400,10201))
        self.assertEqual(F(e['first_original_Armijo_gain_exact']),F(800,1070701))
        self.assertEqual(F(e['first_original_Armijo_requirement_exact']),F(1,255025))
        self.assertTrue(e['first_original_Armijo_pass'])

    def test_second_raw_PR_slope_is_strictly_negative_without_rounding(self):
        e=evidence()
        self.assertTrue(e['second_raw_PR_direction_provably_non_ascent'])
        self.assertEqual(F(e['second_raw_PR_slope_strict_rational_upper']),
                         F(-399237035036400,12152993093482001))
        # The square comparison, not a rounded sqrt/sign evaluation, proves it.
        self.assertLess(10601,103**2)
        self.assertLess(F(e['second_raw_PR_slope_strict_rational_upper']),0)

    def test_transport_is_original_projection_not_parallel_isometry(self):
        old_theta=(F(1),F(0));new_theta=(F(3,5),F(4,5))
        old_tangent=(F(0),F(1))
        actual=project(new_theta,old_tangent)
        cos_delta=inner(old_theta,new_theta)
        lifted=scale((-new_theta[1],new_theta[0]),cos_delta)
        self.assertEqual(actual,lifted)
        self.assertEqual(inner(actual,actual),F(9,25))
        self.assertEqual(inner(old_tangent,old_tangent),1)

    def test_negative_raw_beta_must_not_be_clipped(self):
        a_old=F(1);b_old=F(1);a_new=F(1,2);cos_delta=F(1)
        beta=a_new*(a_new-a_old*cos_delta)/(a_old*a_old)
        self.assertEqual(beta,F(-1,4))
        self.assertEqual(a_new+beta*b_old*cos_delta,F(1,4))

    def test_normalization_retraction_is_atan_not_exponential_step(self):
        # alpha*b=3/4, exact normalized tangent step (1+3i/4)/(5/4).
        theta=(F(3,5),F(4,5));tangent=scale((-theta[1],theta[0]),F(3,4))
        direct=scale(add(theta,tangent),F(4,5))
        self.assertEqual(direct,mul(theta,(F(4,5),F(3,5))))
        self.assertEqual(inner(direct,direct),1)
        delta=add(direct,scale(theta,-1))
        self.assertEqual(delta,mul(theta,(F(-1,5),F(3,5))))
        self.assertEqual(add(theta,(F(0),F(0))),theta)


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path)
    args=parser.parse_args()
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(ExactRawPRScope)
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    receipt={'scope':'ACTUAL exact integer/rational mathematical component, NOT a reduced or complete paper reproduction',
        'source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'actual_test_count':result.testsRun,'all_tests_pass':result.wasSuccessful(),
        'exact_counterexample':evidence(),'optimizer_RNG_MATLAB_or_new_MC_called':False,
        'actual_fullscene_gradient_stop_or_original_figure_certified':False}
    if args.output:
        args.output.parent.mkdir(parents=True,exist_ok=True)
        with args.output.open('x',encoding='utf-8') as stream:
            json.dump(receipt,stream,indent=2,allow_nan=False);stream.write('\n')
    if not result.wasSuccessful():
        raise SystemExit(1)


if __name__=='__main__':
    main()
