"""Render complete source-mapped satellite results, never survivor averages.

No optimizer, reference ordinate or model fitting is used here. Statistical
curves are explicitly the corrected original-model QT branch, not the printed
invalid SOC. Timing is actual local timing, not recovered author hardware time.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import numpy as np

HERE=Path(__file__).resolve().parent
GATES=('physical_constraint_pass','convergence_pass','solver_primal_pass','qt_sdr_bound_pass')
COOP_GATES=('constraint_pass','convergence_pass','solver_primal_pass','qt_bound_pass')

def require(condition,message):
    if not condition:raise ValueError(message)

def numbers(values):
    a=np.asarray(values,float)
    require(a.ndim==1 and len(a)>0 and np.all(np.isfinite(a)),'All computed curve values must be finite and nonempty')
    return a

def ecdf(values):
    """Exact empirical step distribution, merging ties without interpolation."""
    unique,counts=np.unique(numbers(values),return_counts=True)
    return unique.tolist(),(np.cumsum(counts)/np.sum(counts)).tolist()

def curve(label,x,y,**extra):
    x=numbers(x);y=numbers(y)
    require(x.shape==y.shape,'Computed abscissas/ordinates must have the same length')
    return dict(label=label,x=x.tolist(),y=y.tolist(),**extra)

def terminal_hold_mean(histories):
    arrays=[numbers(h) for h in histories]
    require(len(arrays)==1000,'All1000 actual trajectories required')
    n=max(map(len,arrays))
    return np.mean([np.pad(a,(0,n-len(a)),mode='edge') for a in arrays],axis=0)

def point_results(documents,sweep,grid):
    points=[p for d in documents for p in d.get('results',[]) if p.get('sweep')==sweep]
    require(len(points)==len(grid),'Missing/duplicate source sweep points; partial sweeps are not figures')
    result=[]
    for value in grid:
        matches=[p for p in points if p['value']==value]
        require(len(matches)==1,'Exact source abscissa missing or duplicated; no interpolation')
        result.append(matches[0])
    return result

def verify_hotspot_points(points):
    for point in points:
        samples=point.get('samples',[])
        require(len(samples)==1000 and sorted(s.get('index',-1) for s in samples)==list(range(1000)),
                'Every original1000 realization index required, no survivor means')
        require(point.get('valid_figure_point') is True,'An invalid/capped full point is not renderable as successful')
        for sample in samples:
            require(sample.get('valid_sample') is True and all(sample.get(k) is True for k in GATES),
                    'Every original sample must pass physical/stop/primal/bound gates')

def eval_scheme(sample,name):
    require(name in sample,'Required original baseline evaluation missing')
    if name in ('AO20','AO100'):
        endpoint=sample.get('reported_budget_endpoints',{}).get(name,{})
        require(endpoint.get('valid_budget_endpoint') is True,'Original20/100 iteration endpoint missing or invalid')
        require(endpoint.get('convergence_not_required_for_reported_fixed_budget') is True,
                'Finite source-budget endpoints must not be silently relabelled stationary')
    return sample[name]

def hu_rates(e,count):
    sinr=numbers(e['sinr'])
    require(len(sinr)>=count and np.all(sinr[:count]>=0),'Full nonnegative physical HU SINRs required')
    return np.log2(1+sinr[:count])

def hotspot_panel(item,coverage,documents):
    identifier=item['source_id'];sweep=item.get('sweep_id')
    # The source captions/filenames swap these two Rician labels. Both explicit
    # interpretations are preserved; a numerical result cannot prove the label.
    correction=None
    if identifier in ('3-7a','3-7b'):
        sweep='cdf_kS20' if identifier=='3-7a' else 'cdf_kS10'
        correction='filename_Rician_interpretation_caption_conflict_not_uniquely_resolved'
    require(sweep is not None,'This source panel has no validated sweep mapping')
    if identifier=='3-9':
        require(all(d.get('source_element_count_contract',{}).get('count_changes_centers_or_phase') is False and
                    d.get('source_element_count_contract',{}).get('factorization_needed') is False and
                    d.get('source_element_count_contract',{}).get('original_author_geometry_recovered') is False
                    for d in documents),'Exact original count-only aperture/frozen-center contract required; no legacy shape-changing candidate plot')
    if identifier=='3-2':
        # Reuse the exactly matching U6/beta20 bank, not an invented trace.
        sweep='cdf_kS20'
    relevant=[p for d in documents for p in d.get('results',[]) if p.get('sweep')==sweep]
    grid=item['x'].get('values') if identifier not in ('3-6','3-7a','3-7b') else None
    if grid is None:grid=sorted({p['value'] for p in relevant})
    points=point_results(documents,sweep,grid);verify_hotspot_points(points)
    names=item.get('curves',[])
    if isinstance(names,str):names=coverage[names]
    out=[]
    if identifier in ('3-5','3-7a','3-7b'):
        require(len(points)==1,'One complete source CDF population required')
        for name in names:
            values=[]
            for sample in points[0]['samples']:
                e=eval_scheme(sample,name)
                values.extend(hu_rates(e,6) if identifier.startswith('3-7') else [e['hu_sum_rate']])
            x,y=ecdf(values);out.append(curve(name,x,y,plot_style='step_post'))
    elif identifier=='3-6':
        require(len(points)==1,'Per-user means must reuse one complete original CDF bank')
        for name in names:
            rates=np.asarray([hu_rates(eval_scheme(s,name),6) for s in points[0]['samples']],float)
            require(rates.shape==(1000,6) and np.all(np.isfinite(rates)),'All1000 six-HU rates required')
            out.append(curve(name,list(range(1,7)),np.mean(rates,axis=0)))
    elif identifier=='3-2':
        require(len(points)==1,'One complete original convergence population required')
        for name in names:
            histories=[s['history'][name] for s in points[0]['samples']]
            mean=terminal_hold_mean(histories)
            out.append(curve(name,list(range(len(mean))),mean))
    elif identifier=='3-3':
        mapping={'TwoStage_phase':'TwoStage_phase','TwoStage_total':'TwoStage','AO_phase':'AO_phase','AO_total':'AO'}
        for name in names:
            out.append(curve(name,[p['value'] for p in points],
                [float(np.mean([s['cpu_seconds'][mapping[name]] for s in p['samples']])) for p in points]))
    else:
        for name in names:
            out.append(curve(name,[p['value'] for p in points],
                [float(np.mean([eval_scheme(s,name)['hu_sum_rate'] for s in p['samples']])) for p in points]))
    return dict(source_id=identifier,curves=out,x=item['x'],y=item.get('y',{}),
                source_label_correction=correction,reference_line=item.get('reference_line'),
                aggregation='all1000 realizations; no failed sample discarded; terminal state held only for convergence traces',
                cpu_timing_is_local_not_original_hardware=identifier=='3-3')

def statistical_panel(documents):
    docs=[d for d in documents if d.get('algorithm')=='corrected_QT_erratum_NOT_original_printed_invalid_SOC']
    cases=[c for d in docs for c in d.get('cases',[])]
    require(len(cases)==18,'All18 original U1:6 x beta0/10/20 cases required')
    require(all(d.get('source_unchanged_during_run') is True for d in docs),'Immutable statistical runtime sources required')
    require(all(d.get('configuration',{}).get('tuned_not_reported',{}).get('monte_carlo_realizations')==1000 for d in docs),
            'Full1000 independent evaluations required')
    out=[]
    for beta in (0,10,20):
        selected=[]
        for u in range(1,7):
            matches=[c for c in cases if c.get('U')==u and c.get('kappa_satellite_db')==beta]
            require(len(matches)==1,'Missing/duplicate statistical source case')
            c=matches[0]
            require(c.get('status')=='executed' and all(c.get('checks',{}).get(k) is True for k in GATES),
                    'Every statistical case must pass physical/stop/primal/QT gates')
            for name in ('AO','TwoStage','NoRIS'):
                e=c['schemes'][name];mc=e.get('independent_MC',{})
                require(mc.get('count')==1000 and len(mc.get('hu_rate_samples',[]))==1000,
                        'Actual independent1000-draw evidence required for each scheme')
                numbers(mc['hu_rate_samples'])
            selected.append(c)
        for name in ('AO','TwoStage','NoRIS'):
            # Source objective is log(1+ratio of expected powers), not E[log].
            out.append(curve(f'{name}_kS{beta}',list(range(1,7)),
                [c['schemes'][name]['evaluation']['hu_sum_rate'] for c in selected]))
    return dict(source_id='3-10',curves=out,x={'quantity':'HU count','unit':'index'},
        y={'quantity':'source ratio-of-expected-powers HU sum rate','unit':'bps/Hz'},
        algorithm='explicit_corrected_vector_QT_erratum_not_printed_invalid_SOC',
        exact_ergodic_E_log_MC_stored_separately=True)

def cooperative_panels(item,coverage,documents):
    grid=item['x'].get('values')
    if grid is None:
        maximum=5 if item['source_id']=='4-2' else 6
        grid=(2**np.arange(0,maximum+.01,.5)).tolist()
    names=item.get('curves',[]);out=[]
    if isinstance(names,str):names=coverage[names]
    selections=[]
    if item['source_id']=='4-11':
        for beta in (20,0):
            for name in ('AP-AO','MR-TTS-TS'):
                selections.append((f'M_{"AP" if name=="AP-AO" else "MR_TTS_TS"}_kL{beta}',f'multi_vs_single_multi_kL{beta}',name))
            for offset in (1.25,2.5):
                for name in ('AP-AO','MR-TTS-TS'):
                    selections.append((f'S_{"AP" if name=="AP-AO" else "MR_TTS_TS"}_kL{beta}_offset{offset}',
                        f'multi_vs_single_single_{offset}_kL{beta}',name))
    else:selections=[(name,item['sweep_id'],name) for name in names]
    for label,sweep,name in selections:
        points=point_results(documents,sweep,grid)
        for p in points:
            require(p.get('valid_figure_point') is True and all(p.get(k) is True for k in COOP_GATES),
                    'Every complete eight-scheme scenario must pass all original gates')
            require(p.get('monte_carlo',{}).get('count')==1000,'All1000 independent finite-Rician moment draws required')
            require(set(coverage['curves']).issubset(p.get('schemes',{})),'All eight source schemes required')
        out.append(curve(label,grid,[float(np.min(p['schemes'][name]['evaluation']['sinr'])) for p in points]))
    require({c['label'] for c in out}==set(names),'Every source comparison legend must be included')
    return dict(source_id=item['source_id'],curves=out,x=item['x'],y=coverage['y'],reference_line=item.get('reference_line'),
        aggregation='original analytical statistical/two-timescale SINR; all1000 channel-moment validations retained',
        interference_axis_source_unit_conflict=coverage.get('source_unit_conflict'))

def aggregate(paper,figure,documents):
    require(paper in ('cooperative-satcom','hotspot-satcom'),'Only source-mapped satellite packages supported')
    require(documents and all(d.get('paper_id')==paper for d in documents),'All input documents must be from the same paper')
    require(all('component' not in d.get('scope','') and 'NOT_MC' not in d.get('scope','') for d in documents),
            'Component/single-case receipts cannot be relabelled a full figure')
    coverage=json.loads((HERE/paper/'figure_coverage.json').read_text(encoding='utf-8-sig'))
    chapter=4 if paper=='cooperative-satcom' else 3;prefix=f'{chapter}-{figure}'
    items=[i for i in coverage['figures'] if i['source_id']==prefix or i['source_id'] in (prefix+'a',prefix+'b')]
    require(items and all(i.get('simulation_required',True) for i in items),'This figure is not a numerical experiment')
    if paper=='hotspot-satcom' and figure==10:panels=[statistical_panel(documents)]
    elif paper=='hotspot-satcom':
        require(all(d.get('source_unchanged_during_run') is True for d in documents),'Immutable instantaneous runtime sources required')
        panels=[hotspot_panel(i,coverage,documents) for i in items]
    else:
        require(all(d.get('source_unchanged_during_run') is True for d in documents),
                'Immutable cooperative runtime sources required; old unbound receipts are historical')
        panels=[cooperative_panels(i,coverage,documents) for i in items]
    pair_distance_declared=(all(d.get('configuration',{}).get('tuned_not_reported',{}).get('hu_cluster_radius_m')==10
                   and d.get('geometry_contract') is not None for d in documents) if paper=='hotspot-satcom' else None)
    return dict(paper_id=paper,figure=figure,data_kind='independent_simulation_curves',panels=panels,
        full_execution_verified=True,all_source_panels_present=True,failed_samples_discarded=False,
        hotspot_HU_pair_distance_contract_declared=pair_distance_declared,
        scenario_source_constraints_verified=False,source_conforming_full_execution_verified=False,
        source_conformance_note='A declared HU-distance contract and numerical gates do not establish every source assumption, historical feed/LoS geometry, covariance convention or author initialization.',
        published_figure_reproduction_certified=False,original_curve_closeness_verified=False,
        source_version=coverage['source_version'],final_published_figure_numbering_verified=False)

def render(data,directory):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    directory.mkdir(parents=True,exist_ok=True)
    n=len(data['panels']);fig,axes=plt.subplots(1,n,figsize=(7*n,5),squeeze=False)
    for ax,panel in zip(axes.flat,data['panels']):
        for c in panel['curves']:
            if c.get('plot_style')=='step_post':ax.step(c['x'],c['y'],where='post',label=c['label'])
            else:ax.plot(c['x'],c['y'],label=c['label'],linewidth=1.6)
        def label(spec):return spec.get('quantity','')+(' ('+spec['unit']+')' if spec.get('unit') else '')
        ax.set_xlabel(label(panel['x']));ax.set_ylabel(label(panel['y']));ax.grid(True,alpha=.25);ax.legend(fontsize=7)
        ax.set_title(panel['source_id']+' | independently computed; original agreement unverified',fontsize=10)
    fig.tight_layout();stem=directory/f'{data["paper_id"]}-figure-{data["figure"]}'
    fig.savefig(stem.with_suffix('.png'),dpi=200);fig.savefig(stem.with_suffix('.svg'));plt.close(fig)
    stem.with_suffix('.json').write_text(json.dumps(data,indent=2,allow_nan=False)+'\n',encoding='utf-8')


def main():
    """Render already executed receipts only; never launch another solver."""
    import argparse
    import hashlib
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--paper',choices=('hotspot-satcom','cooperative-satcom'),required=True)
    parser.add_argument('--figure',type=int,required=True)
    parser.add_argument('--input','--inputs',dest='input',type=Path,nargs='+',required=True)
    parser.add_argument('--output-dir',type=Path,required=True)
    args=parser.parse_args()
    raw=[path.read_bytes() for path in args.input]
    source=Path(__file__);before=hashlib.sha256(source.read_bytes()).hexdigest()
    data=aggregate(args.paper,args.figure,[json.loads(item.decode('utf-8-sig')) for item in raw])
    data['input_file_sha256']={f'{index}:{path.name}':hashlib.sha256(item).hexdigest()
                              for index,(path,item) in enumerate(zip(args.input,raw))}
    data['renderer_source_sha256']=before
    render(data,args.output_dir)
    require(before==hashlib.sha256(source.read_bytes()).hexdigest(),'Renderer changed during actual plotting')
    require(all(path.read_bytes()==item for path,item in zip(args.input,raw)),
            'Input receipts changed during actual plotting')
    data['input_and_renderer_unchanged_during_render']=True
    output=args.output_dir/f'{args.paper}-figure-{args.figure}-data.json'
    output.write_text(json.dumps(data,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    print(json.dumps(dict(full_execution_verified=data['full_execution_verified'],
        panels=len(data['panels']),published_figure_reproduction_certified=False,output=str(output))))


if __name__=='__main__':main()
