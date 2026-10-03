"""Plot only complete, independently executed and source-bound MATLAB banks.

MATLAB JSON key/array normalization is serialization only. No Python solver,
Python metric or successful-survivor average can stand in for MATLAB results.
All convergence and identity gates are checked again from the actual records.
"""
from __future__ import annotations
import argparse
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import sys
import numpy as np

HERE=Path(__file__).resolve().parent
ISAC_NAMES=['Rot-BS & Rot-RIS','Rot-BS & Fix-RIS','Fix-BS & Rot-RIS',
            'Fix-BS & Fix-RIS','Rot-BS & No-RIS','Fix-BS & No-RIS']
MA_NAMES={'MA_MRT':'MA-MRT','MA_ZF':'MA-ZF','FPA_MRT':'FPA-MRT','FPA_ZF':'FPA-ZF','FPA_OPT':'FPA-OPT'}


def require(value,message):
    if not value:raise ValueError(message)


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def load(path):return json.loads(path.read_text(encoding='utf-8-sig'))
def as_list(value):return value if isinstance(value,list) else [value]
def finite(value):return isinstance(value,(float,int)) and not isinstance(value,bool) and math.isfinite(value)


def inner_complete(item,kind):
    if item.get('converged') is not True or item.get('capped_unconverged') is not False:return False
    reason=item.get('termination_reason')
    if kind=='RIS' and item.get('applicable') is False:
        return reason=='not_applicable_no_RIS' and item.get('iterations')==0
    if not 0<item.get('iterations',0)<=item.get('iteration_budget',0):return False
    def measured(key,tol,strict=False):
        a,b=item.get(key),item.get(tol)
        return finite(a) and finite(b) and b>=0 and (a<b if strict else a<=b)
    if kind=='W':
        return (reason=='relative_objective_tolerance' and measured('relative_objective_improvement','relative_tolerance',True)
                or reason=='relative_step_tolerance' and measured('relative_step','relative_tolerance',True))
    if kind=='RIS':return reason=='gradient_tolerance' and measured('last_checked_normalized_gradient_norm','gradient_tolerance')
    if kind=='rotation':
        return (reason=='projected_gradient_tolerance' and measured('last_checked_projected_gradient_norm','gradient_tolerance')
                or reason=='relative_step_tolerance' and measured('relative_step','relative_tolerance'))
    return False


def normalize_isac(raw):
    require(raw.get('mode')=='full_scenario' and raw.get('status')!='failed','Actual full MATLAB ISAC scenario required')
    require(raw.get('scheme_names')==ISAC_NAMES,'All six uniquely ordered source schemes required')
    result=dict(raw)
    for key in ('metrics','checks','history'):
        items=as_list(raw[key]);require(len(items)==6,'All six MATLAB scheme records required')
        result[key]=dict(zip(ISAC_NAMES,items))
    for name in ISAC_NAMES:
        check=result['checks'][name];history=result['history'][name];metric=result['metrics'][name]
        require(check.get('status')=='executed' and all(check.get(k) is True for k in
            ('converged','inner_all_converged','full_converged','power_feasible','rotation_feasible')),
            'All original inner/outer and physical ISAC gates required')
        require(finite(check.get('unit_modulus_error')) and check['unit_modulus_error']<=1e-10,'RIS unit-modulus gate failed')
        require(all(history.get(k) is True for k in ('inner_all_converged','full_converged')),'Full MATLAB AO history gates required')
        blocks=as_list(history.get('blocks',[]));require(blocks,'Actual MATLAB block histories required')
        require(all(inner_complete(b.get(k,{}),k) for b in blocks for k in ('W','RIS','rotation')),
                'A capped or unmeasured original block cannot be relabelled convergence')
        require(all(finite(metric.get(k)) for k in ('utility','rate','nmse')),'Finite MATLAB metrics required')
    return result


def normalize_ma(raw,job,config):
    require(raw.get('mode')=='full_scenario' and raw.get('status')!='failed','Actual full MATLAB MA scenario required')
    result=json.loads(json.dumps(raw));checks=result.get('checks',{})
    require(all(checks.get(k) is True for k in ('mrt_converged','zf_converged','mrt_nominal_design_spacing_feasible',
        'zf_nominal_design_spacing_feasible','mrt_nominal_design_box_feasible','zf_nominal_design_box_feasible')),
        'All original MA convergence and physical-design gates required')
    schemes=result['metrics']['schemes'];require(set(MA_NAMES).issubset(schemes),'All five MATLAB schemes required')
    result['metrics']['schemes']={MA_NAMES.get(k,k):v for k,v in schemes.items()}
    def samples(item):
        values=as_list(item.get('sample_sum_rates',[]))
        require(len(values)==1000 and all(finite(v) for v in values) and item.get('nonconverged_samples',0)==0,
                'All1000 original NLoS evaluations required; no failed-sample deletion')
        require(finite(item.get('mean_sum_rate')) and np.isclose(np.mean(values),item['mean_sum_rate'],rtol=1e-12,atol=1e-12),
                'MATLAB mean must equal all actual samples')
    for name in MA_NAMES.values():samples(result['metrics']['schemes'][name])
    if config.get('matlab_convex_solver')=='certified_exact_2d':
        for mode in ('mrt','zf'):
            updates=as_list(result['history'][mode].get('coordinate_updates',[]));require(updates,'All actual coordinate certificates required')
            for update in updates:
                cert=update.get('certificate',{})
                require(update.get('original_subproblem_unchanged') is True and cert.get('certified_without_conic_solver_status') is True,
                        'Only certified original exact2D subproblems accepted')
                for key,tol in (('global_objective_gap_upper_bound','global_objective_gap_tolerance'),
                                ('maximum_normalized_constraint_violation','normalized_constraint_tolerance')):
                    require(finite(cert.get(key)) and finite(cert.get(tol)) and 0<=cert[key]<=cert[tol],
                            'Exact2D mathematical certificate failed')
    extension=result['metrics'].get('correlated_extension',{})
    extension={({'MA_MRT_MC':'MA-MRT_MC','MA_ZF_MC':'MA-ZF_MC'}.get(k,k)):v for k,v in extension.items()}
    result['metrics']['correlated_extension']=extension
    if job.get('correlated',False):
        for name in ('MA-MRT_MC','MA-ZF_MC'):samples(extension.get(name,{}))
    mode='mrt' if job.get('figure') in (3,13,15) else 'zf' if job.get('figure') in (4,14,16) else None
    if mode:
        history=result['history'][mode];n=len(as_list(history.get('objective',[])))
        require(n>=2 and len(as_list(history.get('instantaneous_MC_mean',[])))==n,
                'MC evaluation at every original accepted iterate required')
        names=('MRT_correlated_MC_history','MRT_Eq69_history') if mode=='mrt' else ('ZF_correlated_MC_history',)
        if job.get('correlated',False):
            require(all(len(as_list(extension.get(k,[])))==n for k in names),'Every correlated history point required')
    if 'brute_force_D' in job:
        for mode in ('MRT','ZF'):
            require(result['metrics']['brute_force'][mode]['search'].get('complete') is True,'Incomplete exhaustive search is not a figure')
            samples(result['metrics']['brute_force'][mode]['MC'])
    require(not job.get('correlated',False) or job.get('figure') in (13,15),
            'Correlated-ZF14/16 require explicit corrected-source integral panels, not an undefined printed formula')
    return result


def read_bank(paper,bank,results):
    require(paper in ('rotatable-isac','two-timescale-ma'),'Supported independent MATLAB bank required')
    manifest=load(bank/'manifest.json');plan=load(bank/'plan.json');config=load(bank/'run_config.json')
    require(manifest.get('input_bank_complete') is True and manifest.get('realizations_per_case')==100
            and manifest.get('expected_jobs')==manifest['case_count']*100,'Full unchanged100-case population required')
    require(manifest['case_count']==len(plan['cases']) and manifest.get('config_sha256')==sha(bank/'run_config.json'),
            'Complete case list and immutable configuration required')
    if paper=='two-timescale-ma':
        require(manifest.get('nlos_per_geometry')==1000 and config.get('geometry_realizations')==100
                and config.get('nlos_realizations_per_geometry')==1000,'Full100 x1000 MA population required')
    identity=load(results/'execution-identity.json')
    require(identity.get('paper_id')==paper and identity.get('engine')=='matlab'
            and identity.get('source_unchanged_during_run') is True and identity.get('all_result_identities_pass') is True,
            'Actual independent MATLAB execution-time identities required; no post-hoc certificate')
    require(identity.get('expected_jobs')==manifest['expected_jobs'],'Complete MATLAB result count required')
    binding=identity['binding']
    require(identity.get('runtime_dependency_identity_unchanged') is True
            and identity.get('runtime_implementation_fingerprint_after')==binding.get('runtime_implementation_fingerprint')
            ==identity.get('implementation_fingerprint'),
            'Actual fresh BEFORE/AFTER engine/runtime dependency fingerprints required')
    for key,name in (('manifest_sha256','manifest.json'),('configuration_sha256','run_config.json'),('plan_sha256','plan.json')):
        require(binding[key]==sha(bank/name),'Immutable MATLAB input-bank identity changed')
    require(identity['sources_before']==identity['sources_after']==binding['source_identity'],'Actual BEFORE/AFTER sources differ')
    for source in identity['sources_before']:
        path=(HERE/source['relative_path']).resolve()
        require(path.is_relative_to(HERE) and sha(path)==source['sha256'],'MATLAB numerical source identity changed')
    expected={(c,r) for c in range(manifest['case_count']) for r in range(100)}
    require({(e['case_index'],e['realization']) for e in manifest['files']}==expected and len(manifest['files'])==len(expected),
            'Every unique original case/realization required')
    require({p.name for p in (bank/'jobs').glob('case-*-mc-*.json')}=={e['filename'] for e in manifest['files']},
            'Missing or extra immutable input files')
    items=identity['records'];require(len(items)==len(expected),'Every actual MATLAB result identity required')
    require(len({e['input_filename'] for e in items})==len(items),'Duplicate result identities forbidden')
    evidence={e['input_filename']:e for e in items};by_case=[[] for _ in plan['cases']];configuration=(bank/'run_config.json').read_bytes()
    for entry in manifest['files']:
        name=entry['filename'];job_path=bank/'jobs'/name
        fp=hashlib.sha256(b'strict-v1\0'+configuration+b'\0'+job_path.read_bytes()).hexdigest()
        proof=evidence[name];path=results/(Path(name).stem+'-matlab.json')
        require(proof['result_filename']==path.name and proof['result_sha256']==sha(path),
                'MATLAB record changed after execution; no Python replacement')
        require(fp==entry['input_fingerprint']==proof['input_fingerprint'],'Shared input fingerprint changed')
        raw=load(path);require(raw.get('input_fingerprint')==fp and raw.get('implementation_fingerprint')==identity['implementation_fingerprint'],
                                'Independent MATLAB numerical identity mismatch')
        job=load(job_path)
        value=normalize_isac(raw) if paper=='rotatable-isac' else normalize_ma(raw,job,config)
        by_case[entry['case_index']].append(value)
    require(all(len(values)==100 for values in by_case),'All100 actual MATLAB results per point required')
    return plan,by_case,dict(paper_id=paper,engine='matlab',full_execution_verified=True,input_bank_complete=True,
        complete_jobs=len(expected),expected_jobs=len(expected),failed_samples_discarded_for_curve=False,
        original_curve_closeness_verified=False,execution_identity_sha256=sha(results/'execution-identity.json'),
        implementation_fingerprint=identity['implementation_fingerprint'])


def hold(values):
    arrays=[np.asarray(v,float) for v in values]
    require(len(arrays)==100 and all(a.ndim==1 and len(a)>0 and np.all(np.isfinite(a)) for a in arrays),
            'All100 actual finite histories required')
    n=max(map(len,arrays));return np.mean([np.pad(a,(0,n-len(a)),mode='edge') for a in arrays],axis=0).tolist()


def nested(item,path):
    for key in path.split('.'):item=item[key]
    return item


def aggregate(paper,bank,results):
    plan,by_case,receipt=read_bank(paper,bank,results);catalog=load(HERE/paper/'figure_catalog.json');figures=[]
    specs=[s for s in catalog['numerical_figures'] if
           s.get('family')==plan.get('family') and paper=='rotatable-isac' or s['figure']==plan.get('figure') and paper=='two-timescale-ma']
    for spec in specs:
        series=[];figure=spec['figure']
        if paper=='rotatable-isac':
            if spec['series']=='rotation_reference_series':
                for legend in catalog['rotation_reference_series']:
                    pairs=[(case,values) for case,values in zip(plan['cases'],by_case)
                           if case['rotation_legend']['swept_array']==legend['swept_array']
                           and case['rotation_legend']['other_fixed_half_width_deg']==legend['other_fixed_half_width_deg']]
                    pairs.sort(key=lambda pair:pair[0]['point']);require(pairs,'Complete source rotation legend family required')
                    series.append(dict(label=legend['legend'],scheme=legend['scheme'],x=[c['point'] for c,_ in pairs],
                        y=[float(np.mean([v['metrics'][legend['scheme']][spec['y']] for v in values])) for _,values in pairs]))
            else:
                for name in catalog[spec['series']]:
                    series.append(dict(label=name,scheme=name,
                        x=[float(np.mean([v['metrics'][name]['nmse'] for v in values])) if spec.get('parametric') else c['point']
                           for c,values in zip(plan['cases'],by_case)],
                        y=[float(np.mean([v['metrics'][name][spec['y']] for v in values])) for values in by_case]))
        elif figure in (3,4,13,15):
            for case,values in zip(plan['cases'],by_case):
                for path in spec['series']:
                    y=hold([nested(v,path) for v in values])
                    series.append(dict(label=f'{path}; kappa={case["kappa"]:.6g}',source_path=path,x=list(range(len(y))),y=y))
        else:
            groups={}
            for i,case in enumerate(plan['cases']):
                key=(case['N'],case['M'] if figure not in (11,12) else None,case['kappa'] if figure not in (7,8) else None)
                groups.setdefault(key,[]).append(i)
            names=catalog['default_schemes'] if spec['series']=='default_schemes' else spec['series']
            for key,indices in groups.items():
                indices.sort(key=lambda i:plan['cases'][i]['point'])
                for name in names:
                    path=name if name.startswith('metrics.') else f'metrics.schemes.{name}'
                    series.append(dict(label=f'{name}; N={key[0]}; kappa={key[2]}',scheme=name,
                        x=[plan['cases'][i]['point']*(100 if figure==18 else 1) for i in indices],
                        y=[float(np.mean([nested(v,path)['mean_sum_rate'] for v in by_case[i]])) for i in indices]))
        figures.append(dict(**receipt,figure=figure,data_kind='independent_MATLAB_simulation_curves',series=series,
            source_artifact=spec['source_artifact'],x_name=spec['x'],x_unit=spec['x_unit'],y_name=spec['y'],y_unit=spec['y_unit'],
            aggregation='all100 independent MATLAB channels/geometries; all1000 NLoS when applicable; terminal accepted history hold only; no Python metrics',
            reference_x_limits_left_to_right=spec.get('reference_x_limits_left_to_right')))
    require(figures,'Original source figure family is absent')
    return receipt,figures


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--paper',required=True,choices=['rotatable-isac','two-timescale-ma'])
    p.add_argument('--bank',type=Path,required=True);p.add_argument('--results',type=Path,required=True);p.add_argument('--output-dir',type=Path,required=True)
    a=p.parse_args();receipt,figures=aggregate(a.paper,a.bank,a.results)
    sys.path.insert(0,str(HERE/a.paper));spec=importlib.util.spec_from_file_location('matlab_style_only_renderer',HERE/a.paper/'render_figures.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    a.output_dir.mkdir(parents=True,exist_ok=True)
    (a.output_dir/'readiness.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
    for data in figures:
        path=a.output_dir/f'{a.paper}-matlab-figure-{data["figure"]:02d}'
        path.with_suffix('.json').write_text(json.dumps(data,indent=2,allow_nan=False)+'\n',encoding='utf-8');module.render(data,path)
    print(json.dumps(dict(paper_id=a.paper,engine='matlab',full_execution_verified=True,figures_rendered=len(figures),original_curve_closeness_verified=False)))


if __name__=='__main__':main()
