"""Portable gzip-JSON saved first-case reader; no pickle, optimizer or enumeration.

Only unchanged independent geometry_functions/ma_rates are called. In
particular no FPA fixed/fixed_batch/terminal_audit function is invoked.
"""
from pathlib import Path
import argparse
import hashlib
import importlib.util
import json
import math
import gzip
import struct
import sys
import traceback

ORACLE_SHA='9db2b29a4d2235122feb3438c2a47ffe8fdebfce738b6bf3779c4d0a7cc2b81d'
SAMPLE_ATOL=1e-7
MEAN_ATOL=DESIGN_ATOL=1e-9
ROOT=Path(__file__).resolve().parent

def digest(raw):return hashlib.sha256(raw).hexdigest()
def need(value,message):
    if not value:raise ValueError(message)
def signature(value):
    import numpy as np
    if isinstance(value,np.generic):value=value.item()
    if isinstance(value,dict):return ('dict',tuple(sorted((k,signature(v)) for k,v in value.items())))
    if isinstance(value,(tuple,list)):return ('list',tuple(map(signature,value)))
    if isinstance(value,float):return ('binary64',struct.pack('<d',value).hex())
    return (type(value).__name__,value)
def write(path,value):
    path.write_text(json.dumps(value,indent=2,allow_nan=False)+'\n',encoding='utf-8')

def execute(args):
    need(sys.dont_write_bytecode and not sys.flags.optimize,'Use -X utf8 -B without -O')
    case=ROOT/'fixtures/case-000-mc-000';bank=ROOT/'fixtures/bank';out=args.output_dir.resolve()
    need(not out.exists() and not out.is_relative_to(ROOT),'Fresh output outside this public capsule')
    closedpath=case/'closed-result.json'
    need(closedpath.is_file(),'Actual joint closed case required; never read an inflight tape or wait/retry')
    files={}
    def read(path):
        path=Path(path).resolve()
        if not path.is_file() and path.suffix=='.json':path=path.with_suffix('.json.gz')
        need(path.is_relative_to(ROOT),'Only this public source/selected fixture may be read')
        raw=path.read_bytes();files[str(path)]=dict(SHA256=digest(raw),bytes=len(raw))
        return gzip.decompress(raw) if path.suffix=='.gz' else raw
    pins=json.loads(read(ROOT/'SOURCE_INPUT_PINS.json'))
    for rel,expected in pins['files'].items():
        read(ROOT/rel);need(files[str((ROOT/rel).resolve())]==expected,'Exact public source/input: '+rel)
    read(Path(__file__))
    closed=json.loads(read(closedpath));binding=closed['case_binding']
    need(case.name=='case-000-mc-000','Only first case0/realization0; not a bank follower')
    cfgraw=read(bank/'run_config.json');cfg=json.loads(cfgraw)
    bankplanraw=read(bank/'plan.json');bankplan=json.loads(bankplanraw)
    manifestraw=read(bank/'manifest.json');manifest=json.loads(manifestraw)
    figure=bankplan['figure'];need(figure in (19,20),'Only full-axis Fig19 or20')
    n,m=(4,3) if figure==19 else (6,5)
    axis=list(range(3,19 if figure==19 else 13))
    need(cfg['sweeps']['brute_force_points_per_axis']==axis and cfg['geometry_realizations']==100 and cfg['nlos_realizations_per_geometry']==1000,'Full original D axis and configured100x1000 retained')
    need(cfg['brute_force_objective']=='instantaneous_MC' and cfg['maximum_AO_iterations']==10000,'Current complete fixed-MC objective/AO control')
    need(manifest['input_bank_complete'] is True and manifest['expected_jobs']==len(axis)*100,'Exact full-axis bank declaration')
    selected=[row for row in manifest['files'] if row['filename']==case.name+'.json']
    need(len(selected)==1 and selected[0]['case_index']==selected[0]['realization']==0,'Unique original first input slot')
    jobraw=read(bank/'jobs'/selected[0]['filename']);job=json.loads(jobraw)
    fp=digest(b'strict-v1\0'+cfgraw+b'\0'+jobraw)
    need(selected[0]['input_fingerprint']==binding['input_fingerprint']==fp and binding['actual_job_SHA256']==digest(jobraw),'Exact case input fingerprint and job bytes')
    need(binding['configuration_SHA256']==digest(cfgraw) and binding['manifest_SHA256']==digest(manifestraw) and binding['original_bank_plan_SHA256']==digest(bankplanraw),'Original source-bound bank metadata')
    need((job['figure'],job['point'],job['brute_force_D'],job['N'],job['M'],job['kappa'],job['realization'])==(figure,3,3,n,m,100,0),'Full actual first D3 scene')
    need(not any(key in job for key in ('estimated_geometry','antenna_position_error','initial_positions')),'No unreviewed perturbation/initialization variant')
    out.mkdir(parents=True,exist_ok=False)
    report=dict(schema='actual-one-closed-first-full-axis-MA19-MA20-saved-state-readback-v1',figure=figure,
        actual_closed_status=closed['status'],actual_original_implemented_checks=closed.get('original_implemented_checks'),
        complete=False,errors=[],input_fingerprint=fp,
        new_position_optimizations_exhaustive_candidate_calls_FPA_optimizations_MC_draws_RNG_calls=0,
        independent_precision='Existing independent binary64 channel and batched QR-MRT/ZF physical reference; not MP or interval arithmetic.',
        historical_author_search_objective_recovered=False,producer_whole_campaign_source_interval_not_claimed=True,
        all_past_candidate_objectives_or_earliest_optimum_independently_reverified=False,
        each_coordinate_gradient_or_QT_KKT_or_historical_FPA_beam_transcripts_reverified=False,
        original_reference_dual_or_fullpaper_PASS=False)
    dest=out/'ACTUAL_ONE_CLOSED_FIRST_MA_FULL_AXIS_SAVED_GEOMETRY_MC_STOP_AND_COUNT_SCOPE_V1.json'
    if closed.get('actual_result') is None:
        report.update(actual_retained_original_failure=closed,all_scoped_saved_state_checks_pass=False,
            missing_returned_state_not_invented=True,source_and_input_identities=files)
        write(dest,report);return 2
    try:
        actualraw=read(case/'case-000-mc-000-python.json')
        need(digest(actualraw)==closed['actual_result_SHA256'],'Original decompressed actual JSON bytes')
        raw=json.loads(actualraw)
        need(raw['input_fingerprint']==fp and raw['implementation_fingerprint']==binding['original_runtime_implementation_fingerprint'],'Original actual result metadata')
        prior=json.loads(read(ROOT/'evidence/original-independent-readback.json.gz'))
        need(prior['all_scoped_saved_state_checks_pass'] is True and prior['input_fingerprint']==fp,'Sealed original one-case independent report')
        report['public_pickle_loaded']=False
        report['typed_return_identity_reused_only_from_prior_local_report']=True
        oraclepath=ROOT/'sources/independent_saved_physics.py'
        need(digest(read(oraclepath))==ORACLE_SHA,'Exact independent physical definition excerpts')
        spec=importlib.util.spec_from_file_location('_only_saved_first_MA_full_axis_physics',oraclepath)
        oracle=importlib.util.module_from_spec(spec);sys.modules[spec.name]=oracle;spec.loader.exec_module(oracle)
        import numpy as np
        initial,_default_lower,_default_upper,draws,noise,channel,design=oracle.geometry_functions(job,cfg)
        # Original run_job overrides scenario bounds from these exact job fields.
        # No physical formula is changed; the generic helper default A-bounds
        # are intentionally not used for these two explicitly bounded figures.
        lower=np.asarray(job['region_lower'],float);upper=np.asarray(job['region_upper'],float)
        need(draws.shape==(1000,n,m) and np.all(np.isfinite(draws)),'All actual1000 fixed draws of this one original case')
        need(np.array_equal(lower,[-1.6,-1.6]) and np.array_equal(upper,[1.6,1.6 if figure==19 else 2.4]),'Actual source figure box')
        def feasible(t):
            distance=np.linalg.norm(t[:,None,:]-t[None,:,:],axis=2)+np.eye(n)*1e9
            return dict(shape_and_finite=bool(t.shape==(n,2) and np.all(np.isfinite(t))),
                minimum_pair_spacing=float(distance.min()),
                spacing_pass=bool(distance.min()>=.5-cfg['verification_tolerance']),
                source_box_pass=bool(np.all(t>=lower-cfg['verification_tolerance']) and np.all(t<=upper+cfg['verification_tolerance'])))
        physics={};stops={};counts={};fpa={}
        for mode in ('MRT','ZF'):
            key=mode.lower();history=raw['history'][key]
            positions=np.asarray(history['positions'],float);values=np.asarray(history['objective'],float)
            need(len(values)>=2 and positions.shape==(len(values),n,2) and np.all(np.isfinite(positions)) and np.all(np.isfinite(values)),'Actual complete finite AO sweep schema')
            need(np.array_equal(positions[0],initial) and np.array_equal(positions[-1],raw['metrics'][key+'_positions']) and np.array_equal(positions[-1],raw['metrics'][key+'_realized_positions']),'Source initial/final/realized position identities')
            updates=history['coordinate_updates'];sweeps=len(values)-1
            need(len(updates)==n*sweeps and all((row['sweep'],row['antenna'])==divmod(i,n) for i,row in enumerate(updates)),'Original ordered complete coordinate sweep counts')
            need(np.all(np.abs(values[:-1])>0),'Saved source fractional stop must have nonzero denominators; do not invent a zero rule')
            fractions=np.diff(values)/np.abs(values[:-1]);below=fractions<cfg['fractional_increase_threshold']
            converged=history['converged'];need(type(converged) is bool,'Explicit original source stop boolean')
            stop_consistent=(sweeps<=cfg['maximum_AO_iterations'] and not bool(np.any(below[:-1])) and
                (bool(below[-1]) and history['termination']=='fractional_increase' if converged else
                 sweeps==cfg['maximum_AO_iterations'] and not bool(below[-1]) and history['termination']=='configured_iteration_cap'))
            lasttwo=np.asarray([design(t,key) for t in positions[-2:]])
            need(np.all(np.isfinite(lasttwo)),'Finite independent final two design objectives')
            design_error=float(np.max(abs(lasttwo-values[-2:])))
            stops[mode]=dict(actual_converged=converged,actual_termination=history['termination'],
                accepted_sweeps=sweeps,actual_cap=cfg['maximum_AO_iterations'],source_fractional_threshold=cfg['fractional_increase_threshold'],
                final_saved_fractional_increase=float(fractions[-1]),original_source_first_stop_arithmetic_consistent=bool(stop_consistent),
                independent_last_two_design_objectives=lasttwo.tolist(),maximum_last_two_design_error=design_error,
                last_two_design_comparison_pass=design_error<=DESIGN_ATOL,
                earlier_saved_objectives_not_independently_recomputed=True)
            for kind,t,stored in (('AO-final',positions[-1],raw['metrics']['schemes']['MA-'+mode]),
                ('brute-winner',np.asarray(raw['metrics']['brute_force'][mode]['positions'],float),raw['metrics']['brute_force'][mode]['MC'])):
                need(t.shape==(n,2) and np.all(np.isfinite(t)),'Full finite saved geometry shape')
                rates,powers=oracle.ma_rates(channel(t),job['power'],noise,key)
                savedrates=np.asarray(stored['sample_sum_rates'],float);savedpowers=np.asarray(stored['powers'],float)
                need(rates.shape==powers.shape==savedrates.shape==savedpowers.shape==(1000,),'All1000 actual/independent rates and powers')
                need(all(np.all(np.isfinite(v)) for v in (rates,powers,savedrates,savedpowers)) and math.isfinite(stored['mean_sum_rate']),'Nonfinite actual or independent values retained as a failed readback, never made zero')
                geom=feasible(t);sample_error=float(np.max(abs(rates-savedrates)))
                mean=float(np.mean(rates));mean_error=abs(mean-stored['mean_sum_rate'])
                power_error=float(np.max(abs(powers-savedpowers)))
                passed=bool(all(geom[k] for k in ('shape_and_finite','spacing_pass','source_box_pass')) and
                    np.all(np.isfinite(rates)) and np.all(np.isfinite(powers)) and np.all(np.isfinite(savedrates)) and np.all(np.isfinite(savedpowers)) and
                    sample_error<=SAMPLE_ATOL and mean_error<=MEAN_ATOL and power_error<=MEAN_ATOL and np.max(powers)<=job['power']+MEAN_ATOL)
                physics[mode+'-'+kind]=dict(geometry=geom,maximum_1000_sample_rate_error=sample_error,
                    independent_mean_sum_rate=mean,saved_mean_sum_rate=stored['mean_sum_rate'],mean_absolute_error=mean_error,
                    maximum_1000_power_error=power_error,maximum_independent_power=float(np.max(powers)),
                    independent_all1000_sample_sum_rates=rates.tolist(),independent_all1000_total_powers=powers.tolist(),
                    existing_sample_tolerance=SAMPLE_ATOL,existing_mean_power_tolerance=MEAN_ATOL,passed=passed)
            search=raw['metrics']['brute_force'][mode]['search']
            checkpointpath=case/('grid-'+mode)/'checkpoint.json'
            checkpoint=json.loads(read(checkpointpath))
            grid=np.array([[x,y] for x in np.linspace(lower[0],upper[0],3) for y in np.linspace(lower[1],upper[1],3)])
            minimum_grid_step=min((upper-lower)/2)
            need(minimum_grid_step>=.5,'D3 closed-form no-spacing-edge count is applicable')
            expected_count=math.perm(9,n);expected_pruned=sum(math.perm(9,k)*k for k in range(1,n))
            objective=struct.unpack('>d',bytes.fromhex(checkpoint['best_bits']))[0]
            winner=np.asarray(raw['metrics']['brute_force'][mode]['positions'],float)
            countpass=(search['D']==3 and search['N']==n and search['mode']==mode and search['complete'] is True and
                search['permutation_symmetry_reduction'] is False and search['objective_protocol']=='instantaneous_MC' and
                search['evaluated_feasible_geometries']==checkpoint['tested']==expected_count and
                search['pruned_partial_branches']==checkpoint['pruned']==expected_pruned and
                checkpoint['complete'] is True and not checkpoint['stack'] and checkpoint['closed_failure'] is None and
                np.array_equal(grid[checkpoint['winner_indices']],winner) and signature(objective)==signature(search['objective']) and
                abs(search['objective']-physics[mode+'-brute-winner']['independent_mean_sum_rate'])<=MEAN_ATOL)
            counts[mode]=dict(D=3,grid_points=9,full_N=n,expected_ordered_distinct_candidates=expected_count,
                independent_count_formula='P(9,N); all distinct D3 points satisfy source spacing',expected_partial_duplicate_prunes=expected_pruned,
                actual_search=search,committed_checkpoint=checkpoint,count_axis_winner_and_fullMC_objective_checks_pass=bool(countpass),
                no_candidate_enumeration_or_historical_successful_value_replay=True,
                independent_global_maximum_and_earliest_tie_not_rechecked=True)
        for name in ('FPA-MRT','FPA-ZF','FPA-OPT'):
            item=raw['metrics']['schemes'][name];rates=np.asarray(item['sample_sum_rates'],float)
            finite=bool(len(rates)==1000 and np.all(np.isfinite(rates)) and math.isfinite(item['mean_sum_rate']))
            fpa[name]=dict(saved_count=len(rates),saved_finite=bool(len(rates)==1000 and np.all(np.isfinite(rates))),
                saved_nonconverged_samples=item.get('nonconverged_samples'),
                saved_mean_matches_saved_samples=finite and abs(float(np.mean(rates))-item['mean_sum_rate'])<=MEAN_ATOL,
                independent_FPA_optimization_beam_power_QT_or_KKT_checks_performed=False)
        report.update(complete=True,physics=physics,original_stops=stops,brute_axis_and_counts=counts,
            original_FPA_reported_fields_only=fpa,
            all_five_saved_scheme_arrays_finite_and_means_consistent=all(row['saved_finite'] and row['saved_mean_matches_saved_samples'] for row in fpa.values()),
            original_FPA_reported_zero_nonconverged_samples=all(row['saved_nonconverged_samples']==0 for row in fpa.values()),
            all_five_schemes_independent_FPA_optimizer_KKT_correctness_PASS=False,
            all_four_terminal_geometries_powers_and_full1000_MC_fields_pass=all(row['passed'] for row in physics.values()),
            all_original_AO_stop_fields_consistent=all(row['original_source_first_stop_arithmetic_consistent'] and row['last_two_design_comparison_pass'] for row in stops.values()),
            both_original_AO_converged=all(row['actual_converged'] for row in stops.values()),
            both_D3_ordered_scope_counts_pass=all(row['count_axis_winner_and_fullMC_objective_checks_pass'] for row in counts.values()),
            actual_independent_functions_called=['geometry_functions','ma_rates','returned channel closure','returned design closure on only final two AO states'],
            forbidden_functions_not_called=['fixed','fixed_batch','terminal_audit','optimize','exhaustive'],
            explicit_job_region_overrides_generic_helper_A_bounds=True)
    except BaseException as error:
        report['errors'].append(dict(type=type(error).__name__,message=str(error),traceback=traceback.format_exc()))
    finally:
        after={}
        for path in files:
            try:
                value=Path(path).read_bytes();after[path]=dict(SHA256=digest(value),bytes=len(value))
            except BaseException as error:
                after[path]=None;report['errors'].append(dict(stage='post_readback_source_or_input_read',path=path,type=type(error).__name__,message=str(error)))
        report['source_and_input_before']=files;report['source_and_input_after']=after
        report['source_and_input_interval_pass']=files==after
        report['all_scoped_saved_state_checks_pass']=bool(report['complete'] and not report['errors'] and files==after and all(report.get(k) is True for k in (
            'all_four_terminal_geometries_powers_and_full1000_MC_fields_pass','all_original_AO_stop_fields_consistent','both_original_AO_converged','both_D3_ordered_scope_counts_pass','all_five_saved_scheme_arrays_finite_and_means_consistent')))
        write(dest,report)
    print(json.dumps(dict(output=str(dest),passed=report['all_scoped_saved_state_checks_pass'],errors=report['errors'])))
    return 0 if report['all_scoped_saved_state_checks_pass'] else 2

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output-dir',type=Path,required=True)
    p.add_argument('--execute',action='store_true',required=True)
    raise SystemExit(execute(p.parse_args()))
