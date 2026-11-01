"""Verify the retained sample comparisons; does not rerun MATLAB or AO."""
import gzip
import json
import math
from pathlib import Path


def require(condition, reason):
    if condition is not True:
        raise ValueError(reason)


def main():
    p=Path(__file__).with_name('sample_evidence.json.gz')
    with gzip.open(p,'rt',encoding='utf-8') as stream:
        doc=json.load(stream)
    require(doc['schema']=='MA20_MRT_FINAL1000_PUBLIC_SAMPLE_EVIDENCE_V1','bundle schema')
    native=doc['native']; donor=doc['prior_python_saved_MRT']; values=native['native_instantaneous_return']
    comparison=doc['guard_comparison']; history=doc['history'];guard=doc['sanitized_guard']
    require(native['schema']=='MA20_D3G0_MRT_AO_NATIVE_FINAL1000_V1' and native['sample_count']==1000,
            'native schema and count')
    for name in ('native_AO_rerun','native_original_grid_search','historical_input_reauthenticated',
                 'independent_physical_certificate','full_figure_or_paper_pass'):
        require(native[name] is False,'scope: '+name)
    require(history=={'same_current_channel_arrays_compared_under_guard':True,
        'historical_bank_or_producer_reauthenticated':False,'matlab_independent_AO':False,
        'original_reference_agreement_established':False,'full_figure_pass':False},'history scope')
    require(guard['reason']=='natural_exit' and guard['returncode']==0 and not guard['errors'] and
            guard['hard_filesystem_quota'] is False,'guard outcome')
    require(comparison['schema']=='MA20_D3G0_MRT_AO_NATIVE_FINAL1000_COMPARISON_V1' and
            comparison['sample_count']==1000 and comparison['comparison_is_conditional_on_current_input_identity'] is True and
            comparison['historical_producer_or_bank_reauthenticated'] is False and
            comparison['independent_AO_search'] is False and comparison['original_reference_agreement'] is False and
            comparison['full_figure_or_paper_pass'] is False and
            comparison['matlab_mean']==values['mean_sum_rate'] and comparison['python_saved_mean']==donor['mean_sum_rate'],
            'recorded comparison scope and means')
    maxima={}
    for name in ('sample_sum_rates','powers','off_diagonal_amplitude'):
        x=values[name];y=donor[name]
        require(type(x) is list and type(y) is list and len(x)==len(y)==1000 and
                all(type(v) in (int,float) and math.isfinite(v) for v in x+y),'sample vectors: '+name)
        maxima[name]=max(abs(a-b) for a,b in zip(x,y))
        require(maxima[name]==comparison[name+'_maximum_absolute_difference'],'recorded difference: '+name)
    for source in (values,donor):
        require(all(v>=0 for v in source['sample_sum_rates']+source['powers']),'nonnegative rate/power')
        require(abs(sum(source['sample_sum_rates'])/1000-source['mean_sum_rate'])<1e-12,'saved mean')
    require(max(values['powers'])==comparison['matlab_maximum_power'] and
            sum(v>1+1e-6 for v in values['powers'])==comparison['matlab_power_above_1_plus_1e_6'],
            'recorded power')
    positions=native['positions']
    require(len(positions)==6 and all(len(p)==2 and all(math.isfinite(v) for v in p) for p in positions),
            'saved layout')
    spacing=min(math.dist(positions[i],positions[j]) for i in range(6) for j in range(i))
    excess=max(max(-1.6-p[0],p[0]-1.6,-1.6-p[1],p[1]-2.4,0.) for p in positions)
    require(spacing>=.5-1e-6 and excess<=1e-6,'saved layout feasibility at 1e-6')
    print(json.dumps({'sample_count_each':1000,'matlab_mean':values['mean_sum_rate'],
        'prior_python_mean':donor['mean_sum_rate'],'maximum_absolute_differences':maxima,
        'matlab_maximum_power':max(values['powers']),'matlab_power_above_1_plus_1e_6':comparison['matlab_power_above_1_plus_1e_6'],
        'minimum_saved_layout_spacing':spacing,'maximum_saved_layout_box_excess':excess,
        'historical_producer_or_bank_reauthenticated':False,'original_reference_agreement_established':False,
        'matlab_independent_AO':False,'full_figure_pass':False},sort_keys=True))


if __name__=='__main__':main()
