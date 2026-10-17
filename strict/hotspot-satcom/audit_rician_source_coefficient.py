"""Exact author-source G-scatter coefficient contradiction; no optimization."""
import argparse
from fractions import Fraction
import hashlib
import json
from pathlib import Path

SOURCE_SHA='684b2de6bb9dd18828fcec33a378d886a085aab7367fb535bac401f51b496794'


def coefficients(beta):
    beta=Fraction(beta)
    return dict(LoS_power=beta/(1+beta),printed_G_NLoS_power=beta/(1+beta),
                normalized_NLoS_power=1/(1+beta))


def audit(source=None,contexts=None):
    rows=[]
    for db,beta in ((0,1),(10,10),(20,100)):
        c=coefficients(beta)
        rows.append(dict(beta_db=db,beta_linear=beta,
            printed_G_NLoS_variance_per_mu=str(c['printed_G_NLoS_power']),
            Eq3_1_NLoS_variance_per_mu=str(c['normalized_NLoS_power']),
            printed_to_Eq3_1_scatter_variance_multiplier=str(c['printed_G_NLoS_power']/c['normalized_NLoS_power']),
            unit_modulus_LoS_entry_witness_total_power_per_mu=str(c['LoS_power']+c['printed_G_NLoS_power']),
            contradiction_for_beta_not_one=(c['printed_G_NLoS_power']!=c['normalized_NLoS_power'])))
    actual=False;anchors=dict(early_Rician_line=40,late_G_expansion_line=489,unit_variance_NLoS_line=492,total_power_line=101,power_table_line=681)
    if source is not None:
        raw=source.read_bytes()
        if hashlib.sha256(raw).hexdigest()!=SOURCE_SHA:raise ValueError('Different author source; review its anchors separately')
        lines=raw.decode('utf-8-sig').splitlines()
        if lines[488].count(r'\sqrt{\frac{\beta _S}{1+\beta _S}}')!=2:raise ValueError('Late G coefficient source differs')
        if r'\sqrt{1/\left( 1+\beta _S \right)}' not in lines[39]:raise ValueError('Early normalized source differs')
        if '方差为1' not in lines[491] or '最大总波束功率' not in lines[100]:raise ValueError('Source interpretation differs')
        actual=True
    native=[];components=0
    if contexts is not None:
        import numpy as np
        def decode(value):
            return (np.asarray(value['real'])+1j*np.asarray(value['imag'])).reshape(value['shape'],order='F')
        index=json.loads((contexts/'index.json').read_bytes())['cases']
        if len(index)!=18 or {(r['U'],r['beta_db']) for r in index}!={(u,b) for u in range(1,7) for b in (0,10,20)}:raise ValueError('All18 contexts required')
        for entry in index:
            x=json.loads((contexts/entry['context_file']).read_bytes())['mean_inputs']
            mean=decode(x['matrix_mean']);variance=decode(x['matrix_variance'])
            if mean.shape!=(25,16) or np.max(abs(variance.imag))!=0 or np.min(variance.real)<=0:raise ValueError('Invalid finite-Rician context')
            beta=10**(entry['beta_db']/10);ratio=abs(mean)**2/variance.real
            error=float(np.max(abs(ratio-beta))/max(1,beta))
            if error>1e-12:raise ValueError('Constructor does not follow normalized Eq3-1 Rician convention')
            components+=mean.size;native.append(dict(U=entry['U'],beta_db=entry['beta_db'],components=mean.size,maximum_relative_K_factor_error=error))
    return dict(scope='supplied_author_source_G_NLoS_coefficient_conflict_and_constructor_convention',
                source_basename='ch_third.tex',source_sha256=SOURCE_SHA,source_anchors=anchors,
                actual_private_source_read=actual,final_publisher_equation_equivalence_verified=False,
                exact_rational_counterexamples=rows,native_constructor_components_checked=components,native_contexts=native,
                mathematical_conclusion='Late G expression repeats sqrt(beta/(1+beta)) for scatter; Eq3-1 and unit-variance CN require sqrt(1/(1+beta)).',
                current_implemented_branch='Normalized Eq3-1 Rician convention; no optimizer changed by this audit',
                total_power_interpretation='P_T is a total beam-power budget, not per-feed power',
                explains_NoRIS_original_reference_gap=False,
                limitation='G is absent from NoRIS; this source contradiction cannot by itself explain that baseline discrepancy.',
                new_simulations_or_optimizations=0,full_reproduction_pass=False)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',type=Path)
    p.add_argument('--native-contexts',type=Path);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    if a.output.exists():raise ValueError('Preserve prior source evidence')
    result=audit(a.source,a.native_contexts);a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:result[k] for k in ('actual_private_source_read','native_constructor_components_checked','new_simulations_or_optimizations','full_reproduction_pass')}))
