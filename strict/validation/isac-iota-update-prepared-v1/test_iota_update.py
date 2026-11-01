"""Finite toy checks only. Writes nothing and never launches a solver."""
import math
from iota_update import analyze

def run():
    observed=[]
    def case(name, p, desired, *, expected, reason=None, **kw):
        value=analyze(p,desired,**kw)
        assert value['status']==expected,(name,value)
        if reason: assert value.get('reason')==reason,(name,value)
        observed.append({'name':name,'status':value['status'],'reason':value.get('reason'),'change':value.get('observed_change')})
        return value

    small=case('exact_small_positive_overlap',[1e-15,1],[1,0],previous_iota=1,mode='exact',expected='ok')
    assert small['overlap']==1e-15 and math.isclose(small['new_iota'],1e15,rel_tol=1e-15)
    exact=case('exact_positive',[1,0],[1,1],previous_iota=2,mode='exact',expected='ok')
    assert exact['new_iota']==1 and exact['nmse_before']==0.625 and exact['nmse_after']==0.5
    a=case('safeguarded_increase',[1,0],[1,1],previous_iota=1,mode='safeguarded',epsilon=1,epsilon_source='toy only',expected='ok')
    assert a['new_iota']==0.5 and a['nmse_before']==0.5 and a['nmse_after']==1 and a['observed_change']=='increased'
    b=case('safeguarded_decrease',[1,0],[1,1],previous_iota=0.25,mode='safeguarded',epsilon=1,epsilon_source='toy only',expected='ok')
    assert b['nmse_before']==5 and b['nmse_after']==1 and b['observed_change']=='decreased'
    zero=case('safeguarded_zero_overlap',[1,0],[0,1],previous_iota=1,mode='safeguarded',epsilon=0.5,epsilon_source='toy only',expected='ok')
    assert zero['overlap']==0 and zero['new_iota']==2 and zero['nmse_before']==2 and zero['nmse_after']==1.25
    case('exact_zero_overlap',[1,0],[0,1],previous_iota=1,mode='exact',expected='failed',reason='exact_zero_overlap_no_finite_minimizer')
    case('zero_pattern',[0,0],[1,1],previous_iota=1,mode='safeguarded',epsilon=0.1,epsilon_source='toy',expected='failed',reason='zero_pattern_energy')
    case('zero_template',[1,0],[0,0],previous_iota=1,mode='safeguarded',epsilon=0.1,epsilon_source='toy',expected='failed',reason='zero_desired_energy')
    case('epsilon_zero',[1],[1],previous_iota=1,mode='safeguarded',epsilon=0,epsilon_source='toy',expected='failed',reason='epsilon_not_finite_positive')
    case('epsilon_infinite',[1],[1],previous_iota=1,mode='safeguarded',epsilon=float('inf'),epsilon_source='toy',expected='failed',reason='epsilon_not_finite_positive')
    case('missing_source',[1],[1],previous_iota=1,mode='safeguarded',epsilon=1,expected='failed',reason='epsilon_source_required')
    case('reject_implicit_mode',[1],[1],previous_iota=1,mode='unknown',expected='failed',reason='unknown_mode')
    case('negative_pattern',[-1],[1],previous_iota=1,mode='exact',expected='failed',reason='pattern_negative_or_nonfinite')
    case('overlap_overflow',[1e308],[1],previous_iota=1,mode='exact',expected='failed',reason='pattern_square_overflow')
    case('square_underflow',[1e-300],[1],previous_iota=1,mode='exact',expected='failed',reason='pattern_square_underflow')
    case('ratio_overflow',[1],[1],previous_iota=1e-320,mode='exact',expected='failed',reason='p_over_iota_overflow')
    case('sum_overflow',[1e154],[1e154],previous_iota=1,mode='safeguarded',epsilon=1e308,epsilon_source='toy',expected='failed',reason='update_denominator_overflow_or_nonpositive')
    rounded=case('epsilon_rounded_away',[1],[1],previous_iota=2,mode='safeguarded',epsilon=1e-20,epsilon_source='toy',expected='ok')
    assert rounded['epsilon_addition_rounded_away'] is True
    return observed

if __name__=='__main__':
    cases=run()
    print('PASS: %d toy cases; no optimization, no scientific acceptance.'%len(cases))
