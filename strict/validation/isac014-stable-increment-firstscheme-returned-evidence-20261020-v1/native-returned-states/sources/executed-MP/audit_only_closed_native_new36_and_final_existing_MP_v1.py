"""Only actual new returned W/RCG/PGA states and final ownstate, MP80/100."""
from pathlib import Path
import ast,copy,hashlib,json,sys,time
import mpmath as mp
import numpy as np
from native_saved_state_schema_v1 import load_native,admitted_main,PLAN_PATH
R=Path('E:/ZiyuanZhengProject/paper-reproduction-data/resume-20261017')
A=R.parent/'ISAC014-native-stable-PGA-full-actual-v1'
H=R/'ISAC014-native-stable-PGA-full-first-scheme-prepared-v1'
D=R/'ISAC014-stable-PGA-increment-growth-cap5000-rel1e10-first-scheme-prepared-v1/host-state-finish-guard-v2'
T=Path('E:/ZiyuanZhengProject/academic-homepage/wireless-paper-reproductions/tools/isac-line-search-replay')
OUT=None
NATIVE_PLAN=None
NATIVE_ADMISSION_PATH=None
sys.path.insert(0,str(T))
from audit_cold_control import physical,stopping_rows
from audit_failure import FixedObjective,mpmatrix
from mp_physical_reference import exact,field_parts
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def put(p,v):
    with p.open('x',encoding='utf8',newline='\n')as f:json.dump(v,f,indent=2,allow_nan=False);f.write('\n')
def clean(v):
    if isinstance(v,dict):return{k:clean(x)for k,x in v.items()}
    if isinstance(v,(tuple,list)):return[clean(x)for x in v]
    if isinstance(v,np.ndarray):return v.tolist()
    if isinstance(v,np.generic):return v.item()
    return v
def reprmp(x):return mp.nstr(x,105)
def flat(v):return list(np.asarray(v,dtype=object).reshape(-1))
def W_diagnostics(w,gref,scene):
    W=mpmatrix(w);G=mp.matrix(gref);pw=mp.fsum(abs(v)**2 for v in W);dot=mp.re(mp.fsum(mp.conj(v)*q for v,q in zip(W,G)));lam=max(mp.mpf(0),dot/(2*pw));res=G-2*lam*W
    plus=W+G;pn=mp.sqrt(mp.fsum(abs(v)**2 for v in plus));ball=plus if pn==0 else plus*min(mp.mpf(1),mp.sqrt(exact(scene['power']))/pn);pr=mp.sqrt(mp.fsum(abs(v)**2 for v in ball-W))
    return dict(power_ball_multiplier_ray_estimate=reprmp(lam),raw_KKT_gradient_minus_2lambdaW_Fro_norm=reprmp(mp.sqrt(mp.fsum(abs(v)**2 for v in res))),unit_gradient_step_projected_power_ball_residual=reprmp(pr),complementarity_lambda_power_slack=reprmp(lam*(exact(scene['power'])-pw)),author_W_stationarity_absolute_gate_reported=False,stationarity_PASS_not_assigned=True)
def ref_functions():
    node=next(n for n in ast.parse((T/'audit_stable_derivatives.py').read_text()).body if isinstance(n,ast.FunctionDef)and n.name=='reference')
    ns=dict(mp=mp,np=np,FixedObjective=FixedObjective,mpmatrix=mpmatrix,exact=exact,field_parts=field_parts)
    exec(compile(ast.Module(body=[copy.deepcopy(node)],type_ignores=[]),str(T/'audit_stable_derivatives.py')+':unchanged_reference','exec'),ns)
    full=ns['reference'];partial=copy.deepcopy(node)
    cut=next(i for i,n in enumerate(partial.body)if isinstance(n,ast.Assign)and any(isinstance(t,ast.Name)and t.id=='eps'for t in n.targets))
    partial.body=partial.body[:cut]+[ast.parse("return gw,metric['ambient'],None").body[0]]
    ast.fix_missing_locations(partial);exec(compile(ast.Module(body=[partial],type_ignores=[]),str(T/'audit_stable_derivatives.py')+':skip_unused_rotation_difference_for_W_RCG','exec'),ns)
    return full,ns['reference']
def run():
    started=time.perf_counter();out=OUT/'ACTUAL_NATIVE_NEW36_AND_FINAL_EXISTING_MP80_MP100_PHYSICS_AND_GRADIENTS_V1.json';assert not out.exists()
    native=load_native(NATIVE_PLAN,OUT);j=native['j'];sm=native['sm'];result=native['result'];scene=native['scene'];arrays=native['arrays']
    blocks=result['history']['Rot-BS & Rot-RIS']['blocks']
    files=[Path(p)for p in NATIVE_PLAN['source_and_input_pins']]+[PLAN_PATH,NATIVE_ADMISSION_PATH]
    before={str(p):sha(p)for p in files}
    assert all(before[p]==digest for p,digest in NATIVE_PLAN['source_and_input_pins'].items())
    sys.path.insert(0,str(D));from equivalent_runtime_case014_v1 import load_core
    model=load_core(None);fullref,partialref=ref_functions();scalar_rows,populations=stopping_rows(result,scene)
    assert all(v.dtype.kind in 'fc'and np.all(np.isfinite(v))for v in arrays.values())
    prepared=[]
    for row in sm['rows']:
        w,theta,r=[arrays[row['arrays'][k]]for k in ('W','theta','r')];iota=row['fixed_iota'];metric,der=model.evaluate(w,theta,r,scene,iota,True)
        state=clean(dict(metric,w_re=w.real,w_im=w.imag,theta_re=theta.real,theta_im=theta.imag,rotation=r))
        prepared.append(dict(method=row['method'],call=row['call'],state=state,w=w,theta=theta,r=r,gradient=der[{'update_w':0,'update_theta':1,'update_rotation':2}[row['method']]],flags=row['actual_returned_flags']))
    final=result['metrics']['Rot-BS & Rot-RIS'];fw=native['final_arrays']['W'];ft=native['final_arrays']['theta'];fr=native['final_arrays']['r'];_,fg=model.evaluate(fw,ft,fr,scene,float(final['iota']),True)
    prepared.append(dict(method='final_ownstate',call=1,state=final,w=fw,theta=ft,r=fr,all_gradients=fg,flags=result['checks']['Rot-BS & Rot-RIS']))
    put(OUT/'actual-new-block-fixed-input-evaluations-and-final-ownstate.json',{'states':[{'method':x['method'],'call':x['call'],'state':x['state'],'actual_returned_flags':x['flags']}for x in prepared],'intermediate_iota_is_fixed_actual_block_input_not_reoptimized':True,'no_optimizer_or_RNG':True})
    lanes={};nums={};width=np.r_[np.ones(3)*scene.get('rotation_bs_half_width',scene.get('rotation_half_width',np.pi/2)),np.ones(3)*scene.get('rotation_ris_half_width',scene.get('rotation_half_width',np.pi/2))]
    for digits in (80,100):
        rows=[];numeric=[]
        with mp.workdps(digits):
            for x in prepared:
                st=x['state'];ref=physical(st,scene);fieldrows={}
                for key in ('utility','rate','nmse','sinr','pattern'):
                    got=st[key]if isinstance(st[key],list)else[st[key]];expected=ref[key]if isinstance(ref[key],list)else[ref[key]];assert len(got)==len(expected)
                    errors=[abs(exact(v)-q)for v,q in zip(got,expected)];bounds=[exact(scene['verification_tolerance'])+(mp.mpf('1e-10')*abs(q)if key=='sinr'else 0)for q in expected]
                    fieldrows[key]={'count':len(expected),'maximum_absolute_error':reprmp(max(errors)),'original_bound_pass':all(e<=b for e,b in zip(errors,bounds))};numeric+=expected
                if x['method']=='final_ownstate':
                    ie=abs(exact(st['iota'])-ref['iota']);ipass=ie<=exact(scene['verification_tolerance'])+mp.mpf('1e-10')*abs(ref['iota'])
                    fieldrows['iota']={'optimal_iota_error':reprmp(ie),'original_bound_pass':ipass}
                else:fieldrows['iota']={'scope':'Actual fixed inner iota; no optimality comparison appropriate for these endpoints.','exact_saved_input_identity_pass':float(st['iota'])==blocks[x['call']-1]['iota'],'optimal_iota_informative_only':reprmp(ref['iota']),'original_bound_pass':True}
                feasible={'power':ref['transmit_power']<=exact(scene['power'])+exact(scene['verification_tolerance']),'unit_modulus':ref['unit_modulus_error']<=mp.mpf('1e-12'),'rotation':all(abs(exact(float(r)))<=exact(float(b))+mp.mpf('1e-12')for r,b in zip(st['rotation'],width))}
                grow=None
                if x['method']!='final_ownstate':
                    refs=(fullref if x['method']=='update_rotation'else partialref)(x['w'],x['theta'],x['r'].tolist(),scene,float(st['iota']))
                    idx={'update_w':0,'update_theta':1,'update_rotation':2}[x['method']];gref=flat(refs[idx]);gactual=flat(x['gradient']);err=max(abs(exact(complex(v))-q)for v,q in zip(gactual,gref));numeric+=gref
                    grow={'component_count':len(gref),'maximum_component_error':reprmp(err),'existing_derivative_absolute_1e_minus5_pass':err<exact(1e-5),'reference_gradient':[{'real':reprmp(mp.re(v)),'imag':reprmp(mp.im(v))}for v in gref]}
                    if x['method']=='update_rotation':
                        projected=[]
                        for q,v,b in zip(gref,x['r'],width):
                            if v<=-b:q=max(mp.mpf(0),q)
                            if v>=b:q=min(mp.mpf(0),q)
                            projected.append(q)
                        norm=mp.sqrt(mp.fsum(q*q for q in projected));recorded=blocks[x['call']-1]['rotation']['final_projected_gradient_norm'];grow.update(projected_gradient_norm=reprmp(norm),actual_recorded_final_projected_gradient_norm=recorded,MP_norm_minus_actual_recorded_norm=reprmp(norm-exact(recorded)),strict_gradient_threshold=scene['PGA_solver']['gradient_tolerance'],strict_gradient_pass=norm<=exact(scene['PGA_solver']['gradient_tolerance']),reference='Unchanged independent MP rotation central difference h=1e-20')
                    elif x['method']=='update_theta':
                        tangent=[g-mp.re(g*mp.conj(exact(complex(t))))*exact(complex(t))for g,t in zip(gref,x['theta'])];norm=mp.sqrt(mp.fsum(abs(v)**2 for v in tangent))/mp.sqrt(len(tangent));recorded=blocks[x['call']-1]['RIS']['final_normalized_gradient_norm'];grow.update(normalized_unit_circle_tangent_norm=reprmp(norm),actual_recorded_final_normalized_gradient_norm=recorded,MP_norm_minus_actual_recorded_norm=reprmp(norm-exact(recorded)),strict_gradient_threshold=scene['RCG_solver']['gradient_tolerance'],strict_gradient_pass=norm<=exact(scene['RCG_solver']['gradient_tolerance']))
                    else:
                        # Unit gradient-step projected-ascent residual is an explicit
                        # diagnostic scale; the paper supplies no absolute W-KKT cutoff.
                        grow.update(W_diagnostics(x['w'],refs[0],scene))
                else:
                    refs=fullref(x['w'],x['theta'],x['r'].tolist(),scene,float(st['iota']));parts={};errors=[]
                    for kind,got,expected in zip(('W','RCG','PGA'),x['all_gradients'],refs):
                        wanted=flat(expected);actual=flat(got);error=max(abs(exact(complex(v))-q)for v,q in zip(actual,wanted));numeric+=wanted;errors.append(error)
                        part=dict(component_count=len(wanted),maximum_component_error=reprmp(error),existing_derivative_absolute_1e_minus5_pass=error<exact(1e-5))
                        if kind=='W':part.update(W_diagnostics(x['w'],expected,scene))
                        elif kind=='RCG':
                            tangent=[g-mp.re(g*mp.conj(exact(complex(t))))*exact(complex(t))for g,t in zip(wanted,x['theta'])];norm=mp.sqrt(mp.fsum(abs(v)**2 for v in tangent))/mp.sqrt(len(tangent));part.update(normalized_unit_circle_tangent_norm=reprmp(norm),strict_gradient_threshold=scene['RCG_solver']['gradient_tolerance'],strict_gradient_pass=norm<=exact(scene['RCG_solver']['gradient_tolerance']))
                        else:
                            projected=[]
                            for q,v,b in zip(wanted,x['r'],width):
                                if v<=-b:q=max(mp.mpf(0),q)
                                if v>=b:q=min(mp.mpf(0),q)
                                projected.append(q)
                            norm=mp.sqrt(mp.fsum(q*q for q in projected));part.update(projected_gradient_norm=reprmp(norm),strict_gradient_threshold=scene['PGA_solver']['gradient_tolerance'],strict_gradient_pass=norm<=exact(scene['PGA_solver']['gradient_tolerance']),reference='Unchanged independent MP rotation central difference h=1e-20')
                        parts[kind]=part
                    grow=dict(scope='Joint final W/theta/r with final optimal iota, distinct from earlier block-return stops; same-provider fixed evaluation is new saved-only diagnostic, not an algorithm stopping record.',parts=parts,existing_derivative_absolute_1e_minus5_pass=all(e<exact(1e-5)for e in errors),joint_full_stationarity_PASS_not_assigned=True)
                ok=all(v['original_bound_pass']for v in fieldrows.values())and all(feasible.values());gradok=grow is None or grow['existing_derivative_absolute_1e_minus5_pass']
                rows.append(dict(method=x['method'],call=x['call'],fields=fieldrows,feasibility=feasible,physical_pass=ok,block_gradient=grow,gradient_formula_check_pass=gradok,actual_returned_flags=x['flags']))
                print(json.dumps({'digits':digits,'method':x['method'],'call':x['call'],'physical_pass':ok,'gradient_formula_check_pass':gradok,'strict_block_gradient_pass':None if grow is None else grow.get('strict_gradient_pass')}),flush=True)
        nums[digits]=numeric;lanes[str(digits)]=rows
    with mp.workdps(110):gap=max(abs(x-y)for x,y in zip(nums[80],nums[100]));cross=gap<mp.mpf('1e-35')
    after={str(p):sha(p)for p in files};assert before==after
    science=all(r['physical_pass']and r['gradient_formula_check_pass']for lane in lanes.values()for r in lane)and cross
    strictpga=[r['call']for r in lanes['100']if r['method']=='update_rotation'and not r['block_gradient']['strict_gradient_pass']];strictrcg=[r['call']for r in lanes['100']if r['method']=='update_theta'and not r['block_gradient']['strict_gradient_pass']]
    report={'schema':'actual-only-new-stable-increment-firstscheme-returned-blocks-MP80-MP100-v1','source_input_before':before,'source_input_after':after,'source_input_interval_closed':True,'held_scientific_exit_code':j['actual_child_terminal_exit_code'],'returned_inner_blocks':len(sm['rows']),'returned_per_method':sm['counts'],'actual_outer_blocks':len(blocks),'final_ownstate_also_checked':True,'final_joint_state_gradient_residuals':lanes['100'][-1]['block_gradient'],'precision_lanes':lanes,'MP80_MP100_maximum_absolute_difference':reprmp(gap),'MP80_MP100_bound':'1e-35','crossprecision_pass':cross,'all_new_states_physics_feasibility_and_corresponding_gradient_formula_checks_pass':science,'strict_PGA_failed_block_calls':strictpga,'strict_RCG_failed_block_calls':strictrcg,'all_strict_RCGe_PGA_block_return_stationarity_pass':not strictpga and not strictrcg,'block_return_pass_does_not_establish_final_joint_KKT':True,'W_KKT_no_author_absolute_gate_assigned':True,'original_algorithm_populations':populations,'original_scalar_block_rows':scalar_rows,'fixed_block_iota_does_not_assert_optimal_iota':True,'saved_only_no_optimization_MC_RNG_or_new_trials':True,'full_six_schemes_native_original_reference_or_paper_PASS':False,'elapsed_seconds':time.perf_counter()-started}
    report.update(schema='actual-only-native-new36-and-final-common-formula-MP80-MP100-v1',
        actual_native_MAT_input_schema_receipt='ACTUAL_NATIVE_MAT_TYPED_STATE_SCHEMA_AND_INPUT_BINDING_V1.json',
        actual_native_MAT_SHA256=NATIVE_PLAN['source_and_input_pins'][NATIVE_PLAN['actual_inputs']['MAT']],
        actual_native_result_SHA256=NATIVE_PLAN['source_and_input_pins'][NATIVE_PLAN['actual_inputs']['result']],
        independent_native_state_values_not_inherited_from_Python_PASS=True,
        binary64_formula_comparator_scope='Frozen common Python arithmetic provider on each actual native state; native per-coordinate analytic vectors were not captured. Stored native RCG/PGA norms are separately reported alongside newly computed MP norms.',
        native_returned_block_input_not_final_joint_stationarity=True,
        actual_final_complex_components_from_raw_MAT_not_recombined_JSON=True)
    put(out,report);print(json.dumps({'report':str(out),'SHA256':sha(out),'scientific_field_and_gradient_formula_pass':science,'strict_PGA_failed_block_calls':strictpga,'strict_RCG_failed_block_calls':strictrcg,'elapsed_seconds':report['elapsed_seconds']}),flush=True)
    if not science:raise SystemExit(1)
if __name__=='__main__':admitted_main(globals(),run)
