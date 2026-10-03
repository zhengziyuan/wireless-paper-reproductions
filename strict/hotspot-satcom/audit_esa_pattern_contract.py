"""Amplitude-versus-power convention counterexample, not historical fitting."""
import json
from pathlib import Path
import numpy as np
from scipy.special import jv
from scenario_geometry import esa_power_pattern,cluster_positions
from run_support import save_receipt,source_hashes,unchanged


def amplitude(nu):
    nu=np.asarray(nu,float);result=np.ones_like(nu);nonzero=abs(nu)>1e-8;x=nu[nonzero]
    result[nonzero]=jv(1,x)/(2*x)+36*jv(3,x)/x**3
    return result


if __name__=='__main__':
    base=Path(__file__).parent;c=json.loads((base/'statistical_geometry_config.json').read_text());p=c['reported'];t=c['tuned_not_reported']
    nu=np.asarray([0.,1.,4.,6.,7.,8.,10.,12.]);a=amplitude(nu)
    centers=np.asarray([[x,y] for x in (-1.5,-.5,.5,1.5) for y in (-1.5,-.5,.5,1.5)])*t['feed_center_spacing_m']
    U=p['U'];K=p['K'];hu=cluster_positions(U,t['hu_cluster_radius_m']);order=sorted(range(16),key=lambda n:float(np.linalg.norm(centers[n])))
    pos=np.vstack((hu,centers[order[-K:]],[[p['ris_hu_distance_m'],0.]]));lam=299792458/p['frequency_hz']
    theta=np.arctan(np.linalg.norm(centers[None,:,:]-pos[:,None,:],axis=2)/p['leo_height_m'])
    actual_nu=np.pi*p['antenna_diameter_m']/lam*np.sin(theta);actual_a=amplitude(actual_nu)
    hashes=source_hashes(['audit_esa_pattern_contract.py','scenario_geometry.py','statistical_geometry_config.json'])
    result={'scope':'source_amplitude_vs_power_pattern_contract_audit_NOT_figures_or_original_pattern_recovery',
        'source_anchors':{'D_sqrt_of_power_gain':'ch_third.tex44-48','printed_unsquared_normalized_G_T':'ch_third.tex49-52'},
        'literal_printed_formula_can_be_negative_as_power_gain':bool(np.any(a<0)),
        'counterexamples':[{'nu':float(x),'printed_Bessel_sum':float(y),'normalized_squared_power_pattern':float(y*y)} for x,y in zip(nu,a)],
        'current_generator_contract':'G_T=10^(satellite_gain_dbi/10)*abs(Bessel_sum)^2; D contains sqrt(G_R*G_T). This is an explicit physically nonnegative amplitude-to-power interpretation, NOT literal unsquared Eq3-3 recovery.',
        'current_full_dimension_geometry_negative_literal_entries':int(np.sum(actual_a<0)),
        'current_full_dimension_geometry_total_entries':int(actual_a.size),
        'current_generator_nonnegative_pass':bool(np.all(esa_power_pattern(actual_nu)>=0)),
        'broadside_amplitude_limit':1.,'normalized_power_and_maximum_gain_distinction':True,
        'primary_power_pattern_example':{'url':'https://link.springer.com/article/10.1186/s13638-020-01749-7','location':'Section2.1 equation3','supports':'squared Bessel sum times Gmax as gain, not proof of the user author actual numerical convention'},
        'classification':'supplied-thesis amplitude-versus-power convention omitted/inconsistent; potential typography or unstated normalization, publisher text and historical implementation unverified',
        'publisher_version_and_author_historical_convention_verified':False,'reference_ordinates_used':False,
        'executed_source_hashes':hashes,'source_unchanged_during_run':unchanged(hashes),'full_reproduction_pass':False}
    save_receipt(base/'outputs'/'esa-pattern-contract-audit.json',result)
    print(json.dumps({'literal_power_negative':result['literal_printed_formula_can_be_negative_as_power_gain'],
        'actual_scene_negative_literal_entries':result['current_full_dimension_geometry_negative_literal_entries'],
        'source_unchanged_during_run':result['source_unchanged_during_run']}),flush=True)
