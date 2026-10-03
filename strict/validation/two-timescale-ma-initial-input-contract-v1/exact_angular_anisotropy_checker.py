"""Exact second-moment witness for declared independent angular sampling."""
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import numpy as np

HERE=Path(__file__).resolve().parent
def item(x):return {'numerator':x.numerator,'denominator':x.denominator,'decimal':float(x)}
def main():
    out=HERE/'EXACT-declared-independent-angle-anisotropy-v1.json';assert not out.exists()
    # Integral of sin² or cos² over Uniform[-pi/2,pi/2] is exactly1/2.
    x_variance=Fraction(1,2)*Fraction(1,2);y_variance=Fraction(1,2)
    assert x_variance==Fraction(1,4) and y_variance==2*x_variance
    # Concrete matrix invariance witness uses no reference or optimization.
    t=np.array([[-.25,-.5],[-.25,0],[-.25,.5],[.25,-.5],[.25,0],[.25,.5]])
    theta=np.array([-.72,-.3,.0,.24,.76]);phi=np.array([-.8,-.27,.03,.5,.91])
    directions=np.c_[np.cos(theta)*np.sin(phi),np.sin(theta)]
    H=np.exp(2j*np.pi*t@directions.T);translation=np.array([.34,-.18])
    diagonal=np.exp(2j*np.pi*translation@directions.T)
    translated=np.exp(2j*np.pi*(t+translation)@directions.T)
    error=float(np.max(abs(translated-H*diagonal)));assert error<1e-14
    gram_error=float(np.max(abs(abs(translated.conj().T@translated)**2-abs(H.conj().T@H)**2)))
    assert gram_error<1e-12
    receipt={'scope':'EXACT_analytic_distribution_witness_and_small_deterministic_phase_identity_NOT_historical_inputs_or_reoptimization',
             'assumption':'declared independent theta and phi marginal Uniform[-pi/2,pi/2]; source only gives marginal uniforms, joint independence remains reconstruction choice',
             'direction_model':['cos(theta)*sin(phi)','sin(theta)'],
             'E_ax_squared':item(x_variance),'E_ay_squared':item(y_variance),'E_ax_ay':item(Fraction(0)),
             'axis_swap_is_not_distribution_invariant_under_this_declared_sampler':True,
             'Nr2Nc3_vs_Nr3Nc2_historical_factorization_recovered':False,
             'translation_phase_identity_max_error':error,'Gram_squared_magnitudes_invariant_error':gram_error,
             'random_per_feed_mean_phase_or_gain_added':False,'reference_curve_values_used':False,
             'figure_gap_cause_uniquely_identified_or_corrected':False,
             'source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    out.write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8');print(json.dumps(receipt))

if __name__=='__main__':main()
