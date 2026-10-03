"""Pure receipt regression tests; no paper curves or Monte Carlo runs."""
from termination import relative_stop,gradient_stop,scheme_status


def run():
    settings={'solver_primal_relative_tolerance':1e-5,'qt_bound_tolerance':1e-5}
    capped=relative_stop([1.,2.],1,1e-4);done=relative_stop([1.,1.00001],1,1e-4)
    assert not capped['converged'] and done['converged']
    stationary=gradient_stop(1e-8,500,500,1e-6);nonstationary=gradient_stop(1e-3,500,500,1e-6)
    assert stationary['converged'] and not nonstationary['converged']
    valid={'solver_diagnostics':{'constraint_max_relative_violation':0.},'qt_bound_max_violation':0.}
    assert scheme_status([done,stationary],[valid],settings)['algorithm_success']
    assert not scheme_status([done,nonstationary],[valid],settings)['algorithm_success']
    assert not scheme_status([done],[dict(valid,qt_bound_max_violation=1e-3)],settings)['algorithm_success']
    bad={'solver_diagnostics':{'constraint_max_relative_violation':1e-3},'qt_bound_max_violation':0.}
    assert not scheme_status([done],[bad],settings)['algorithm_success']
    assert not scheme_status([],[],settings)['algorithm_success']
    assert not scheme_status([{}],[valid],settings)['algorithm_success']
    assert not scheme_status([{'converged':True}],[valid],settings)['algorithm_success']
    assert not scheme_status([done],[],settings)['algorithm_success']
    assert not scheme_status([done],[{}],settings)['algorithm_success']
    for nonfinite in (float('nan'),float('inf'),float('-inf')):
        assert not relative_stop([1.,nonfinite],1,1e-4)['converged']
        assert not gradient_stop(nonfinite,1,1,1e-4)['converged']
        assert not scheme_status([dict(done,final_residual=nonfinite)],[valid],settings)['algorithm_success']
        assert not scheme_status([done],[dict(valid,qt_bound_max_violation=nonfinite)],settings)['algorithm_success']
        assert not scheme_status([done],[{'solver_diagnostics':{'constraint_max_relative_violation':nonfinite},'qt_bound_max_violation':0.}],settings)['algorithm_success']
    print('JSAC receipt tests passed: caps, gradient failure, primal failure and QT-bound failure cannot imply success.')


if __name__=='__main__':run()
