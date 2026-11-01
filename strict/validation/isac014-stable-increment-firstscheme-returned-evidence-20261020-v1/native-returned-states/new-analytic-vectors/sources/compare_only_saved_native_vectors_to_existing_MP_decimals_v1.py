"""Only native saved binary64 vectors versus already stored MP decimals."""
from decimal import Decimal,localcontext
import hashlib
import json
from pathlib import Path
import numpy as np
from scipy.io import loadmat

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def need(v,m):
    if not v:raise ValueError(m)
def put(p,v):
    with Path(p).open('x',encoding='utf8',newline='\n')as f:json.dump(v,f,indent=2,allow_nan=False);f.write('\n')
def integer(v):
    a=np.asarray(v).reshape(-1);need(a.size==1,'Actual scalar required');x=float(a[0]);need(np.isfinite(x)and x.is_integer(),'Actual integer required');return int(x)

def run(plan,held_journal):
    out=Path(plan['fresh_output_directory']);mat=out/'actual-new-native36-analytic-vectors.mat';completion=out/'actual-native36-probe-completion.json'
    report=Path(plan['existing_MP_report']);files=[mat,completion,report,Path(held_journal)]
    files += [Path(p)for p in plan['source_and_input_pins']]
    before={str(p):sha(p)for p in files};j=json.loads(Path(held_journal).read_bytes())
    need(j['natural_wait_completed']and j['actual_child_terminal_exit_code']==0 and j['exact_original_handle_birth_and_exit_match'],'Probe did not return naturally0 on held handle')
    need(j['all_watched_source_and_job_bytes_unchanged']and not j['host_errors'],'Probe source interval not closed')
    need(all(sha(p)==h for p,h in plan['source_and_input_pins'].items()),'Frozen source/input changed before decimal comparison')
    existing=json.loads(report.read_bytes());need(existing['source_input_interval_closed']is True,'Existing MP report not sourceclosed')
    need(existing['actual_native_MAT_SHA256']==plan['original_MAT_SHA256'],'Existing MP was bound to another original native MAT')
    done=json.loads(completion.read_bytes());need(done['native_returned_state_count']==36 and done['new_evaluate_calls']==36 and done['optimizer_update_MC_RNG_or_MP_calls']==0,'Probe scope changed')
    loaded=loadmat(mat,simplify_cells=True,mat_dtype=False);vectors=loaded['vectors']
    if isinstance(vectors,dict):vectors=[vectors]
    need(len(vectors)==36,'36 actual native vectors required')
    rows=[];allpass=True;counts={};maxerror=Decimal(0);component_total=0
    with localcontext()as ctx:
        ctx.prec=200;bound=Decimal.from_float(1e-5)
        for index,row in enumerate(vectors):
            need(integer(row['actual_return_index'])==index+1,'Native return ordering mismatch')
            method=str(row['method']);call=integer(row['call']);need(method==('update_w','update_theta','update_rotation')[index%3]and call==index//3+1,'Actual native block mismatch')
            need(str(row['native_gradient_class'])=='double','Original native class not double')
            dims=tuple(int(v)for v in np.asarray(row['native_gradient_size']).reshape(-1))
            wanted={'update_w':(4,6),'update_theta':(36,1),'update_rotation':(6,1)}[method];need(dims==wanted,'Actual native gradient shape mismatch')
            g=np.asarray(row['gradient'])
            need(g.dtype.kind in 'biufc'and np.isfinite(g).all(),'Nonfinite/unsupported native vector')
            # Native class says double; MAT mi compact integer storage can be
            # promoted exactly. Its real+imag component hash must match before use.
            real=np.asarray(g.real,dtype='<f8').reshape(dims,order='F');imag=np.asarray(g.imag,dtype='<f8').reshape(dims,order='F')
            digest=hashlib.sha256(real.tobytes(order='F')+imag.tobytes(order='F')).hexdigest()
            need(digest==str(row['component_real_then_imag_F_binary64_SHA256']),'Native typed real/imag bits did not roundtrip')
            actual=list(zip(real.reshape(-1,order='C'),imag.reshape(-1,order='C')))
            comparisons={};counts[method]=counts.get(method,0)+1
            for digits in ['80','100']:
                old=existing['precision_lanes'][digits][index]
                need(old['method']==method and old['call']==call,'Existing MP source order mismatch')
                ref=old['block_gradient']['reference_gradient'];need(len(ref)==len(actual),'Full existing MP vector required')
                errors=[]
                for (re,im),q in zip(actual,ref):
                    dr=Decimal.from_float(float(re))-Decimal(q['real']);di=Decimal.from_float(float(im))-Decimal(q['imag'])
                    errors.append((dr*dr+di*di).sqrt())
                worst=max(errors);passed=all(e<bound for e in errors);allpass=allpass and passed;maxerror=max(maxerror,worst)
                comparisons[digits]={'components':len(actual),'maximum_absolute_complex_error':str(worst),
                    'original_exact_binary64_absolute_bound':str(bound),'original_strict_less_than_1e_minus5_pass':passed,
                    'per_component_absolute_errors':[str(e)for e in errors]}
            component_total+=len(actual)
            rows.append({'index':index+1,'method':method,'call':call,'native_gradient_shape':list(dims),
                'actual_native_class':str(row['native_gradient_class']),'actual_native_isreal':bool(integer(row['native_isreal'])),
                'actual_loaded_storage_dtype':g.dtype.str,'real_imag_F_binary64_hash_match':True,
                'native_vector_flatten_for_existing_reference':'C order after restoring actual native shape',
                'fixed_iota':float(row['fixed_iota']),'comparisons':comparisons})
    need(counts=={'update_w':12,'update_theta':12,'update_rotation':12},'Actual applicable block count mismatch')
    need(all(existing['precision_lanes'][d][-1]['method']=='final_ownstate' and
        all('reference_gradient'not in part for part in existing['precision_lanes'][d][-1]['block_gradient']['parts'].values())for d in ['80','100']),'Final vector scope differs; do not extend silently')
    after={str(p):sha(p)for p in files};closed=before==after;code=0 if closed and allpass else 2
    result={'schema':'actual-new-native36-analytic-vectors-vs-reused-existing-MP80-MP100-decimals-v1',
        'actual_entry_exit_code':code,'source_input_before':before,'source_input_after':after,'source_input_interval_closed':closed,
        'actual_native_new_sourcebound_vector_calls':36,'component_count_per_precision':component_total,'counts':counts,
        'all_36_native_own_block_analytic_vectors_existing_MP80_MP100_bound_PASS':allpass,'maximum_absolute_error':str(maxerror),'rows':rows,
        'original_binary64_1e_minus5_bound_preserved':True,'existing_MP_reference_regenerated':False,
        'final37_analytic_vector_gate_still_pending_no_saved_reference_vectors':True,'historical_inmemory_native_vectors_recovered':False,
        'new_native_evaluate_at_saved_states_not_Python_binary64_comparator':True,
        'unchanged_original_joint_stationarity_failures_not_promoted':True,'W_author_absolute_stationarity_PASS_not_assigned':True,
        'new_optimizer_update_MC_RNG_MP_or_trial_calls':0,'original_reference_fullsix_or_fullpaper_PASS':False}
    put(out/'ACTUAL_NEW_NATIVE36_ANALYTIC_VECTORS_VS_EXISTING_MP80_MP100_SAVED_DECIMALS_V1.json',result)
    print(json.dumps({'exit':code,'all36_native_vectors_PASS':allpass,'components_per_precision':component_total,'max_absolute_error':str(maxerror),'sourceclosed':closed}),flush=True)
    return code
