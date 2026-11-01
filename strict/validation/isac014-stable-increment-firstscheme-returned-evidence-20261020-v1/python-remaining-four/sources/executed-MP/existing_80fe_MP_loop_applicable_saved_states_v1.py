"""Original80fe MP numerical loop; input/NoRIS applicability adapters only."""
# Imported only after true admission and real closed-source producer checks.
import mpmath as mp
import numpy as np
import json

def check_saved_states(prepared,scene,width,with_ris,original):
    physical=original.physical;exact=original.exact;flat=original.flat
    reprmp=original.reprmp;W_diagnostics=original.W_diagnostics
    fullref,partialref=original.ref_functions()
    lanes={};nums={}
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
                else:fieldrows['iota']={'scope':'Actual fixed inner iota; no optimality comparison appropriate for these endpoints.','exact_saved_input_identity_pass':float(st['iota']).hex()==float(x['fixed_iota']).hex(),'optimal_iota_informative_only':reprmp(ref['iota']),'original_bound_pass':True}
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
                        norm=mp.sqrt(mp.fsum(q*q for q in projected));recorded=x['flags']['final_projected_gradient_norm'];grow.update(projected_gradient_norm=reprmp(norm),actual_recorded_final_projected_gradient_norm=recorded,MP_norm_minus_actual_recorded_norm=reprmp(norm-exact(recorded)),strict_gradient_threshold=scene['PGA_solver']['gradient_tolerance'],strict_gradient_pass=norm<=exact(scene['PGA_solver']['gradient_tolerance']),reference='Unchanged independent MP rotation central difference h=1e-20')
                    elif x['method']=='update_theta':
                        tangent=[g-mp.re(g*mp.conj(exact(complex(t))))*exact(complex(t))for g,t in zip(gref,x['theta'])];norm=mp.sqrt(mp.fsum(abs(v)**2 for v in tangent))/mp.sqrt(len(tangent));recorded=x['flags']['final_normalized_gradient_norm'];grow.update(normalized_unit_circle_tangent_norm=reprmp(norm),actual_recorded_final_normalized_gradient_norm=recorded,MP_norm_minus_actual_recorded_norm=reprmp(norm-exact(recorded)),strict_gradient_threshold=scene['RCG_solver']['gradient_tolerance'],strict_gradient_pass=norm<=exact(scene['RCG_solver']['gradient_tolerance']))
                    else:
                        # Unit gradient-step projected-ascent residual is an explicit
                        # diagnostic scale; the paper supplies no absolute W-KKT cutoff.
                        grow.update(W_diagnostics(x['w'],refs[0],scene))
                else:
                    refs=fullref(x['w'],x['theta'],x['r'].tolist(),scene,float(st['iota']));parts={};errors=[]
                    for kind,got,expected in zip(('W','RCG','PGA'),x['all_gradients'],refs):
                        if kind=='RCG' and not with_ris:continue
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
    return lanes,reprmp(gap),cross
