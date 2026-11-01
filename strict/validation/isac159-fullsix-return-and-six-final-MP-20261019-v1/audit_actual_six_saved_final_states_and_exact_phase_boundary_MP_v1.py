"""Prepared, not executed: existing MP physical/derivative oracles on six saved states.

This is a schema/ownership adapter, not an optimizer or a new mathematical oracle.
The original natural exit2 and original convergence failures are never gates for
admitting a saved physical state, and never upgraded by a fixed-state result.
"""
from pathlib import Path
import argparse,copy,hashlib,importlib.util,json,sys,time

NAMES=('Rot-BS & Rot-RIS','Rot-BS & Fix-RIS','Fix-BS & Rot-RIS','Fix-BS & Fix-RIS','Rot-BS & No-RIS','Fix-BS & No-RIS')

def sha(raw):return hashlib.sha256(raw).hexdigest()

def load(path):
    raw=path.read_bytes();return json.loads(raw),sha(raw)

def save(path,value):
    path.write_text(json.dumps(value,indent=2,allow_nan=False)+'\n',encoding='utf-8')

def execute(args):
    if not args.execute:raise ValueError('This future MP action requires explicit --execute')
    if args.output_dir.exists():raise FileExistsError('Preserve prior partial or complete outcome')
    plan,plan_sha=load(args.plan)
    watched={Path(p):h for p,h in plan['source_and_input_pins'].items()}
    before={str(p):sha(p.read_bytes()) for p in watched}
    if before!={str(p):h for p,h in watched.items()}:raise ValueError('Prepared source/input identity changed')
    fixture,_=load(Path(plan['fixture']));scene,_=load(Path(plan['scenario']));config,_=load(Path(plan['config']))
    assert tuple(fixture['metrics'])==NAMES and tuple(fixture['checks'])==NAMES
    assert fixture['actual_entry_exit_code']==2 and fixture['original_full_converged']==4
    assert fixture['original_not_full_converged']==list(NAMES[:2])
    assert fixture['actual_entry_source_and_input_interval']['source_and_input_interval_unchanged'] is True
    for key in ('W_solver','RCG_solver','PGA_solver','AO_solver'):
        assert fixture['original_result_nonhistory_metadata']['original_controls'][key]==scene[key]==config[key]
    # Load the actual frozen producer's evaluator provider, not the repo's newer core.
    runtime_root=Path(plan['runtime_root']);tools=Path(plan['tools_root'])
    sys.path.insert(0,str(runtime_root))
    spec=importlib.util.spec_from_file_location('actual_case159_fixed_state_runtime',runtime_root/'equivalent_runtime_case159_v1.py')
    runtime=importlib.util.module_from_spec(spec);spec.loader.exec_module(runtime)
    model=runtime.load_core()  # definitions + arithmetic evaluator only; no solver call.
    sys.path.insert(0,str(tools))
    import mpmath as mp
    import numpy as np
    from audit_cold_control import audit_states
    from audit_stable_derivatives import reference
    from mp_physical_reference import exact,field_parts
    from audit_failure import FixedObjective,mpmatrix
    args.output_dir.mkdir(parents=True)
    start=time.perf_counter()
    report=dict(schema='actual-six-saved-final-states-independent-fixed-state-MP-v1',
        original_closed_entry_exit_code=fixture['actual_entry_exit_code'],
        original_full_converged=fixture['original_full_converged'],
        original_not_full_converged=fixture['original_not_full_converged'],
        original_checks=fixture['checks'],plan_SHA256=plan_sha,source_before=before,
        mathematical_execution_started=True,scope_errors=[],complete=False,
        historical_QT_auxiliaries_QCQP_KKT_or_intermediate_state_certified=False,
        fixed_state_checks_do_not_change_original_algorithm_stops=True,
        new_optimizer_MC_RNG_or_production_QCQP_calls=0)
    dest=args.output_dir/'ACTUAL_SIX_FINAL_PHYSICS_AND_LAST_FIXED_IOTA_DERIVATIVES_MP80_MP100_V1.json'
    save(dest,report)
    try:
        report['all_six_final_physics']=audit_states(fixture['metrics'],scene,fixture['checks'])
        report['all6_final_physical_fields_and_feasibility_pass']=bool(report['all_six_final_physics']['all_five_returned_physical_states_and_feasibility_pass'])
        report['legacy_helper_field_name_scope']='The helper label all_five is historical; its actual loop consumed exactly these six named returned states at both precisions.'
        save(dest,report)
        lanes={};numeric={}
        for digits in (80,100):
            lanes[str(digits)]={};numeric[digits]=[]
            with mp.workdps(digits):
                for name in NAMES:
                    state=fixture['metrics'][name];last=fixture['last_actual_blocks'][name]
                    own=copy.deepcopy(scene)
                    if 'No-RIS' in name:
                        own['br_gain_re']=[0.]*len(own['br_gain_re']);own['br_gain_im']=[0.]*len(own['br_gain_im'])
                    w=np.asarray(state['w_re'])+1j*np.asarray(state['w_im'])
                    theta=np.asarray(state['theta_re'])+1j*np.asarray(state['theta_im'])
                    rotation=np.asarray(state['rotation']);iota=last['last_AO_fixed_iota']
                    refs=reference(w,theta,rotation.tolist(),own,iota)
                    actual_metric,actual_gradient=model.evaluate(w,theta,rotation,own,iota,True)
                    components={}
                    for kind,got,ref in zip(('W','RIS','rotation'),actual_gradient,refs):
                        flat=list(np.asarray(ref,dtype=object).reshape(-1));got=np.asarray(got).reshape(-1)
                        errors=[abs(exact(complex(a))-b) for a,b in zip(got,flat)]
                        assert len(got)==len(flat)
                        components[kind]=dict(components=len(flat),maximum_absolute_error=mp.nstr(max(errors),105),
                            existing_fixed_state_reader_component_bound='1e-5',
                            all_component_comparisons_pass=bool(max(errors)<mp.mpf('1e-5')),
                            reference=[dict(real=mp.nstr(mp.re(v),105),imag=mp.nstr(mp.im(v),105)) for v in flat])
                        numeric[digits].extend(flat)
                    objective=FixedObjective(mpmatrix(w),own,iota,field_parts(rotation.tolist(),own)).evaluate([exact(complex(v)) for v in theta])
                    fixed_utility_error=abs(exact(actual_metric['utility'])-objective['utility'])
                    ris=[v-mp.re(v*mp.conj(exact(complex(t))))*exact(complex(t)) for v,t in zip(refs[1],theta)]
                    ris_norm=mp.sqrt(mp.fsum(abs(v)**2 for v in ris)/len(theta))
                    width=[own.get('rotation_bs_half_width',own.get('rotation_half_width',np.pi/2)) if name.startswith('Rot-BS') else 0.]*3
                    width += [own.get('rotation_ris_half_width',own.get('rotation_half_width',np.pi/2)) if ' & Rot-RIS' in name else 0.]*3
                    projected=[]
                    for v,x,b in zip(refs[2],rotation,width):
                        if b==0:v=mp.mpf(0)
                        else:
                            if x<=-b:v=max(mp.mpf(0),v)
                            if x>=b:v=min(mp.mpf(0),v)
                        projected.append(v)
                    pga_norm=mp.sqrt(mp.fsum(v*v for v in projected))
                    saved_pga=last['last_block']['rotation']['final_projected_gradient_norm']
                    pga_error=abs(pga_norm-exact(saved_pga))
                    # Only a zero-update last rotation block proves this is the
                    # actual historical phase endpoint, rather than a later state.
                    exact_phase=('No-RIS' not in name and last['last_block']['rotation']['updates']==0)
                    saved_phase=last['last_block']['RIS'].get('final_normalized_gradient_norm')
                    row=dict(last_actual_fixed_iota=iota,reported_final_metric_optimal_iota=state['iota'],
                        all_gradient_components=components,
                        fixed_iota_utility_MP=mp.nstr(objective['utility'],105),
                        actual_provider_fixed_iota_utility=actual_metric['utility'],
                        fixed_iota_utility_absolute_error=mp.nstr(fixed_utility_error,105),
                        original_verification_tolerance=own['verification_tolerance'],
                        fixed_iota_utility_pass=bool(fixed_utility_error<=exact(own['verification_tolerance'])),
                        explicit_self_excluded_interference_MP=[mp.nstr(v,105) for v in objective['interference']],
                        signal_MP=[mp.nstr(v,105) for v in objective['signal']],
                        final_RIS_normalized_gradient_MP=mp.nstr(ris_norm,105),
                        final_PGA_projected_gradient_MP=mp.nstr(pga_norm,105),
                        saved_actual_final_PGA_norm=saved_pga,PGA_norm_absolute_error=mp.nstr(pga_error,105),
                        PGA_norm_reader_comparison_pass=bool(pga_error<mp.mpf('1e-5')),
                        original_PGA_stop=last['last_block']['rotation']['converged'],
                        original_PGA_stop_reason=last['last_block']['rotation']['termination_reason'],
                        independent_PGA_gradient_threshold_satisfied=bool(pga_norm<=exact(own['PGA_solver']['gradient_tolerance'])),
                        original_RIS_stop=last['last_block']['RIS']['converged'],
                        original_RIS_gradient_tolerance=own['RCG_solver']['gradient_tolerance'],
                        independent_current_state_RIS_gradient_threshold_satisfied=bool(ris_norm<=exact(own['RCG_solver']['gradient_tolerance'])),
                        exact_actual_historical_phase_endpoint_by_zero_rotation_updates=exact_phase,
                        original_recorded_phase_norm=saved_phase,
                        exact_historical_phase_norm_error=mp.nstr(abs(ris_norm-exact(saved_phase)),105) if exact_phase else None,
                        exact_historical_phase_norm_reader_comparison_pass=bool(abs(ris_norm-exact(saved_phase))<mp.mpf('1e-5')) if exact_phase else None,
                        exact_historical_phase_threshold_classification_matches_original=bool((ris_norm<=exact(own['RCG_solver']['gradient_tolerance']))==last['last_block']['RIS']['converged']) if exact_phase else None,
                        historical_phase_norm_comparison_applicable=exact_phase,
                        last_rotation_updates=last['last_block']['rotation']['updates'],
                        final_W_power_residual=mp.nstr(mp.mpf(report['all_six_final_physics']['lanes'][str(digits)][name]['transmit_power'])-exact(own['power']),105),
                        rotation_half_widths_radians=width,
                        original_RCGlow_and_PGA_stop_flags_preserved=True)
                    lanes[str(digits)][name]=row
                    numeric[digits].extend([objective['utility'],ris_norm,pga_norm])
                    report['last_fixed_iota_derivative_lanes']=lanes
                    save(dest,report)
        with mp.workdps(110):gap=max(abs(a-b) for a,b in zip(numeric[80],numeric[100]))
        report['maximum_derivative_and_fixed_objective_MP80_MP100_difference']=mp.nstr(gap,105)
        report['crossprecision_bound']='1e-35'
        report['all6_last_fixed_iota_gradient_components_and_precision_pass']=bool(gap<mp.mpf('1e-35') and all(
            v['all_component_comparisons_pass'] for lane in lanes.values() for row in lane.values() for v in row['all_gradient_components'].values()))
        report['all6_fixed_iota_objectives_and_final_PGA_norm_reader_comparisons_pass']=all(row['fixed_iota_utility_pass'] and row['PGA_norm_reader_comparison_pass'] for lane in lanes.values() for row in lane.values())
        exact_rows={d:lanes[d]['Rot-BS & Rot-RIS'] for d in ('80','100')}
        assert all(row['exact_actual_historical_phase_endpoint_by_zero_rotation_updates'] is True for row in exact_rows.values())
        assert all(lanes[d]['Rot-BS & Fix-RIS']['last_rotation_updates']==3 and lanes[d]['Rot-BS & Fix-RIS']['historical_phase_norm_comparison_applicable'] is False for d in ('80','100'))
        report['specific_original_failed_phase_boundary_scope']=dict(
            Rot_BS_Rot_RIS='Exact actual last phase endpoint: final rotation made0updates; report both recorded and MP norm, unchanged1e-6 stop. A comparison PASS never upgrades original500-cap failure.',
            Rot_BS_Fix_RIS='Only actual post-rotation final state checked. Last rotation made3updates; its unknown historical pre-rotation r is not reconstructed or substituted.')
        report['Rot_Rot_exact_last_failed_phase_norm_and_original_stop_classification_comparisons_pass']=all(
            row['exact_historical_phase_norm_reader_comparison_pass'] is True and row['exact_historical_phase_threshold_classification_matches_original'] is True for row in exact_rows.values())
        report['complete']=True
    except Exception as error:
        report['scope_errors'].append(dict(type=type(error).__name__,error=str(error)))
    finally:
        after={str(p):sha(p.read_bytes()) for p in watched}
        report['source_after']=after;report['source_input_interval_unchanged']=before==after
        report['original_all_six_algorithm_convergence_pass']=False
        report['historical_QCQP_KKT_dual_language_original_reference_or_paper_PASS']=False
        report['elapsed_seconds']=time.perf_counter()-start
        report['scoped_saved_final_state_and_derivative_comparisons_pass']=bool(report['complete'] and not report['scope_errors'] and before==after and report.get('all6_final_physical_fields_and_feasibility_pass') is True and report.get('all6_last_fixed_iota_gradient_components_and_precision_pass') is True and report.get('all6_fixed_iota_objectives_and_final_PGA_norm_reader_comparisons_pass') is True and report.get('Rot_Rot_exact_last_failed_phase_norm_and_original_stop_classification_comparisons_pass') is True)
        save(dest,report)
    return 0 if report['scoped_saved_final_state_and_derivative_comparisons_pass'] else 1

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--plan',type=Path,required=True);p.add_argument('--output-dir',type=Path,required=True);p.add_argument('--execute',action='store_true')
    return execute(p.parse_args())
if __name__=='__main__':raise SystemExit(main())
