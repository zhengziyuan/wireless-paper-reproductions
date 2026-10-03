"""Two-step synthetic RGD direction/sign identity, never a paper experiment."""
import numpy as np
from core import criterion_gradient,phase_rgd


def run():
    rng=np.random.default_rng(312)
    cn=lambda shape:(rng.standard_normal(shape)+1j*rng.standard_normal(shape))/np.sqrt(2)
    direct=cn((2,3));cascade=.1*cn((2,3,3));nhu=cn((1,3));phi=np.exp(1j*np.array([.2,.3,.4]))
    manual=phi.copy()
    for _ in range(2):
        value,g=criterion_gradient(direct,cascade,nhu,manual);alpha=1.;slope=np.vdot(g,g).real
        for _ in range(50):
            trial=manual+alpha*g;trial/=abs(trial);newvalue,_=criterion_gradient(direct,cascade,nhu,trial)
            if newvalue-value>=1e-4*alpha*slope:break
            alpha*=.5
        else:raise AssertionError('Synthetic RGD Armijo failed')
        manual=trial
    status={};actual,history=phase_rgd(direct,cascade,nhu,phi,2,1e-12,status)
    assert np.max(abs(manual-actual))<1e-13
    assert status['phase_method']=='author_Algorithm_3-2_RGD_minimize_negative_F'
    assert np.all(np.diff(history)>=0) and np.max(abs(abs(actual)-1))<1e-13
    literal_status={};_,literal=phase_rgd(direct,cascade,nhu,phi,2,1e-12,literal_status,literal_sign=True)
    assert np.all(np.diff(literal)<=0)
    assert literal_status['phase_method']=='literal_negative_grad_F_diagnostic_NOT_argmax_F'
    print('RGD method tests passed: both formal steps use fresh gradient only; literal opposite sign remains diagnostic.')


if __name__=='__main__':run()
