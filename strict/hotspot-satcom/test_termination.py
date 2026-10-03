"""Pure receipt regression tests; no paper results are manufactured."""
from termination import relative_stop,gradient_stop,scheme_status


def run():
    settings={'solver_primal_relative_tolerance':1e-5,'qt_bound_tolerance':1e-5}
    capped=relative_stop([1.,2.],1,1e-4);done=relative_stop([1.,1.00001],1,1e-4)
    stationary=gradient_stop(1e-8,500,500,1e-6);nonstationary=gradient_stop(1e-3,500,500,1e-6)
    assert not capped['converged'] and done['converged'] and stationary['converged'] and not nonstationary['converged']
    assert gradient_stop(1e-6,500,500,1e-6)['converged']
    active={'constraint_max_relative_violation':0.,'qt_bound_max_violation':0.}
    phase={'constraint_max_relative_violation':0.,'sdr_bound_max_violation':0.}
    records=[{'active':active,'phase':phase}]
    assert scheme_status([done,stationary],records,settings)['algorithm_success']
    assert not scheme_status([done,nonstationary],records,settings)['algorithm_success']
    assert not scheme_status([capped],records,settings)['algorithm_success']
    assert not scheme_status([done],[dict(active,qt_bound_max_violation=1e-3)],settings)['algorithm_success']
    assert not scheme_status([done],[dict(phase,sdr_bound_max_violation=1e-3)],settings)['algorithm_success']
    assert not scheme_status([done],[dict(active,constraint_max_relative_violation=1e-3)],settings)['algorithm_success']
    assert not scheme_status([],[],settings)['algorithm_success']
    assert not scheme_status([{}],records,settings)['algorithm_success']
    assert not scheme_status([{'converged':True}],records,settings)['algorithm_success']
    assert not scheme_status([done],[],settings)['algorithm_success']
    assert not scheme_status([done],[{}],settings)['algorithm_success']
    for nonfinite in (float('nan'),float('inf'),float('-inf')):
        assert not relative_stop([1.,nonfinite],1,1e-4)['converged']
        assert not gradient_stop(nonfinite,1,1,1e-4)['converged']
        assert not scheme_status([dict(done,final_residual=nonfinite)],records,settings)['algorithm_success']
        assert not scheme_status([done],[dict(active,qt_bound_max_violation=nonfinite)],settings)['algorithm_success']
        assert not scheme_status([done],[dict(phase,sdr_bound_max_violation=nonfinite)],settings)['algorithm_success']
        assert not scheme_status([done],[dict(active,constraint_max_relative_violation=nonfinite)],settings)['algorithm_success']
    print('Hotspot receipt tests passed: caps, phase gradient, primal, QT and SDR bound failures cannot imply success.')


if __name__=='__main__':run()
