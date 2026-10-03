"""Negative and finite-difference gates, never reduced figure evidence."""
import unittest
from unittest.mock import patch
import numpy as np
from compare_communication_full_reference import compare, numeric, phases
from freeze_communication_fig7_bank import evaluate


def state(baseline='MIS'):
    encode=lambda angle:dict(real=np.cos(angle).tolist(),imag=np.sin(angle).tolist())
    return dict(phi=encode(np.array([.3,-.4])),theta=encode(np.array([.7]) if baseline=='MIS' else np.array([])),
        X=[[.6,.4],[.2,.8],[.3,.7],[.9,.1]] if baseline=='MIS' else [[1.]]*4)


class CompleteReferenceGates(unittest.TestCase):
    def test_partial_bank_rejected_before_original_evaluation(self):
        with patch('compare_communication_full_reference.pattern') as evaluator:
            with self.assertRaises(ValueError):
                compare(dict(paper_id='mis-communications',figure='fig7',full_figure_execution_complete=False,
                    overall_full_success=True),{})
            evaluator.assert_not_called()

    def test_finite_strict_numeric_shapes(self):
        self.assertEqual(numeric([1.,2.],[1.,2.],'equal'),0)
        for values in ([1.],[1.,float('nan')],[1.,2.001]):
            with self.assertRaises(ValueError):numeric(values,[1.,2.],'bad')

    def test_phase_domain_not_recovered_by_normalization(self):
        bad=state();bad['phi']['real'][0]+=1e-4
        with self.assertRaises(ValueError):phases(bad,'phi',2)

    def test_original_full_schedule_domain_required(self):
        bad=state();bad['X'][0]=[.7,.4]
        with self.assertRaises(ValueError):evaluate(bad,'MIS',.01)
        with self.assertRaises(ValueError):evaluate(state(),'MIS',float('nan'))

    def test_independent_KKT_no_projection_at_interior_finite_difference(self):
        for baseline in ('MIS','SMS'):
            z=state(baseline);mu=.013;h=1e-6;grad=[]
            for key,count in [('phi',2),('theta',1 if baseline=='MIS' else 0)]:
                for index in range(count):
                    objectives=[]
                    for sign in (-1,1):
                        zz={k:({n:list(vv) for n,vv in v.items()} if isinstance(v,dict) else [list(r) for r in v]) for k,v in z.items()}
                        value=complex(zz[key]['real'][index],zz[key]['imag'][index])*np.exp(1j*sign*h)
                        zz[key]['real'][index]=value.real;zz[key]['imag'][index]=value.imag
                        objectives.append(evaluate(zz,baseline,mu)['objective'])
                    grad.append((objectives[1]-objectives[0])/(2*h))
            xnorm=0.
            if baseline=='MIS':
                for row in range(4):
                    objectives=[]
                    for sign in (-1,1):
                        zz=dict(z,X=[list(r) for r in z['X']]);zz['X'][row][0]+=sign*h;zz['X'][row][1]-=sign*h
                        objectives.append(evaluate(zz,baseline,mu)['objective'])
                    derivative=(objectives[1]-objectives[0])/(2*h)
                    xnorm+=derivative**2/2
            oracle=np.sqrt(np.dot(grad,grad)+xnorm)
            self.assertAlmostEqual(evaluate(z,baseline,mu)['kkt'],oracle,delta=2e-10)


if __name__=='__main__':unittest.main()
