"""Describe all fixed geometry trajectories, never select one to fit a plot."""
from pathlib import Path
import argparse
import hashlib
import json
import numpy as np


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def distribution(values):
    values=np.asarray(values,dtype=float)
    assert values.shape==(100,) and np.isfinite(values).all()
    return {"count":100,"mean":float(values.mean()),
            "quantiles0_25_50_75_100":np.quantile(values,[0,.25,.5,.75,1]).tolist()}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--native-bank',required=True,type=Path)
    p.add_argument('--source-input-bank',required=True,type=Path)
    p.add_argument('--rendered-curves',required=True,type=Path)
    p.add_argument('--output',required=True,type=Path)
    a=p.parse_args();assert not a.output.exists()
    rendered=json.loads(a.rendered_curves.read_bytes())
    assert rendered['all200_native_MC_histories_actually_evaluated']
    assert not rendered['original_curve_closeness_verified']
    frozen={a.rendered_curves.name:sha(a.rendered_curves),Path(__file__).name:sha(__file__)}
    rows=[];all_sources=[];same_geometry=[]
    for case,kappa in [(0,6),(1,100)]:
        data={name:[] for name in ['initial_MC','final_MC','plot_x599_MC','initial_design','final_design','plot_x599_design','stopped_sweeps']}
        for realization in range(100):
            stem=f'case-{case:03d}-mc-{realization:03d}'
            path=a.native_bank/(stem+'-native-figure04.json')
            jobpath=a.source_input_bank/'jobs'/(stem+'.json')
            r=json.loads(path.read_bytes());job=json.loads(jobpath.read_bytes())
            assert r['kappa']==kappa and r['realization']==realization and r['nlos_per_position']==1000
            mc=np.asarray(r['actual_full1000_MC_history']);design=np.asarray(r['original_statistical_objective_history'])
            assert len(mc)==len(design)==r['accepted_ZF_positions']
            assert np.isfinite(mc).all() and np.isfinite(design).all()
            assert r['source_stop_and_domains_checked']
            for key,values in [('MC',mc),('design',design)]:
                data['initial_'+key].append(values[0]);data['final_'+key].append(values[-1])
                data['plot_x599_'+key].append(values[min(599,len(values)-1)])
            data['stopped_sweeps'].append(len(mc)-1)
            all_sources.append({'native_record_filename':path.name,'native_record_sha256':sha(path),
                                'job_filename':jobpath.name,'job_sha256':sha(jobpath)})
            if case==1:
                paired=a.source_input_bank/'jobs'/f'case-000-mc-{realization:03d}.json'
                earlier=json.loads(paired.read_bytes())
                assert all(earlier[key]==job[key] for key in ['geometry','nlos_re','nlos_im','N','M','power','A'])
                same_geometry.append({'geometry_id':realization,'both_original_geometry_and1000_NLoS_arrays_equal':True})
        group={key:distribution(value) for key,value in data.items()}
        comparisons=rendered['unfitted_reference_comparisons'][1]['rows']
        authorMC=next(v['author_first_last']for v in comparisons if v['author_curve']==f'actual_ergodic_kappa{kappa}')
        authorDesign=next(v['author_first_last']for v in comparisons if v['author_curve']==f'surrogate_kappa{kappa}')
        for quantity,values,author in [('MC',data['final_MC'],authorMC),('design',data['final_design'],authorDesign)]:
            group[quantity+'_author_first_last_reference']=author
            group[quantity+'_author_final_inside_all100_final_range']=bool(min(values)<=author[-1]<=max(values))
            group[quantity+'_geometries_final_below_author_endpoint']=int(sum(v<author[-1]for v in values))
        group['kappa']=kappa
        group['geometries_stopped_within500_sweeps']=int(sum(v<=500 for v in data['stopped_sweeps']))
        group['all100_geometries_kept_equally_weighted']=True
        rows.append(group)
    assert len(all_sources)==200 and len(same_geometry)==100
    assert frozen=={a.rendered_curves.name:sha(a.rendered_curves),Path(__file__).name:sha(__file__)}
    for binding in all_sources:
        assert sha(a.native_bank/binding['native_record_filename'])==binding['native_record_sha256']
        assert sha(a.source_input_bank/'jobs'/binding['job_filename'])==binding['job_sha256']
    result={'scope':'actual_native_Fig4_all200_geometry_ensemble_protocol_distribution_not_historical_curve_recovery',
            'source_hashes':frozen,'all200_original_record_and_input_hashes':all_sources,
            'both_kappas_use_the_same_fixed100_geometries_and1000_NLoS_arrays':True,
            'paired_geometries':same_geometry,'groups':rows,
            'all_source_inputs_and_native_MC_records_unchanged':True,
            'plot_x599_uses_completed_terminal_hold_not_fictitious_updates':True,
            'final_state_distribution_mean_is_not_the_599_sweep_plotted_mean':True,
            'original_paper_MC_count_seed_and_convergence_averaging_protocol_unreported':True,
            'source_endpoint_inside_geometry_range_does_not_identify_author_geometry':True,
            'no_geometry_chosen_removed_or_reweighted_to_reduce_reference_discrepancy':True,
            'not_a_unique_explanation_of_historical_curve_discrepancy':True,
            'original_curve_closeness_verified':False,'full_reproduction_pass':False}
    a.output.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    print(json.dumps(rows),flush=True)


if __name__=='__main__':main()
