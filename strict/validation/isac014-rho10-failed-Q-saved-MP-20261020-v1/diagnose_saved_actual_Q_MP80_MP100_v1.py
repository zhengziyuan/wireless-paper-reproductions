"""Saved operands only: no source optimizer, channel generator, or RNG is imported."""
from pathlib import Path
import argparse, hashlib, json, math, time
import numpy as np
import mpmath as mp

CAP=Path(__file__).resolve().parent
HELD=CAP/'actual-held-terminal-and-source-closure.json'
EXPECTED_NPZ='635f106c9c5b5ec02a21117d532325cbd66bbddf6d4caf2016faf0c6c9b901e4'

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(p,v): Path(p).write_text(json.dumps(v,indent=2,ensure_ascii=False,allow_nan=False)+'\n',encoding='utf-8')
def z(x):
    x=complex(x)
    return mp.mpc(mp.mpf(x.real),mp.mpf(x.imag))
def mat(a):
    a=np.asarray(a)
    if a.ndim==1:a=a.reshape(-1,1)
    return mp.matrix([[z(v) for v in row] for row in a])
def norm(a): return mp.sqrt(mp.fsum(abs(v)**2 for v in a))
def s(x): return mp.nstr(x,65)
def cn(x): return {'real':s(mp.re(x)),'imag':s(mp.im(x))}
def eigen(a):return [mp.re(v) for v in mp.eighe(a,eigvals_only=True)]
def lower_hermitian(q):
    n=len(q);h=mp.matrix(n)
    for i in range(n):
        h[i,i]=mp.mpf(float(q[i,i].real))
        for j in range(i):h[i,j]=z(q[i,j]);h[j,i]=mp.conj(h[i,j])
    return h
def colnorm(a):return mp.sqrt(mp.fsum(abs(v)**2 for v in a))

def one_precision(a,scene,dps):
    with mp.workdps(dps):
        fc=mat(a['fc']);q=mat(a['q']);p=mat(a['p']);qc=mat(a['q_communication']);pc=mat(a['p_communication']);ps=mat(a['p_sensing'])
        n,k=np.asarray(a['fc']).shape
        alpha=mp.mpf(float(a['q_sensing'][0,0]));den=mp.mpf(float(a['den']));rho=mp.mpf(scene['rho'])
        alpha_formula=rho*mp.fsum(mp.mpf(float(v)) for v in a['lip'])/(2*den)
        weights=[(1+mp.mpf(float(a['mu'][u])))*abs(z(a['eta'][u]))**2/mp.log(2) for u in range(k)]
        q_exact=mp.eye(n)*alpha_formula
        for u in range(k):
            for i in range(n):
                for j in range(n):q_exact[i,j]+=weights[u]*fc[i,u]*mp.conj(fc[j,u])
        # A separately declared structured model freezing the positive binary64
        # weights and alpha. It isolates dense Gram assembly from weight error.
        wa=(1+a['mu'])*abs(a['eta'])**2
        q_weight_frozen=mp.eye(n)*alpha
        for u in range(k):
            w=mp.mpf(float(wa[u]))/mp.mpf(float(np.log(2)))
            for i in range(n):
                for j in range(n):q_weight_frozen[i,j]+=w*fc[i,u]*mp.conj(fc[j,u])
        hl=lower_hermitian(a['q']);hh=(q+q.H)/2
        evl=eigen(hl);evh=eigen(hh);eve=eigen(q_exact);evf=eigen(q_weight_frozen)
        evsaved=mat(a['val']);v=mat(a['vec']);lam=mp.diag([evsaved[i] for i in range(n)])
        eigres_lower=norm(hl*v-v*lam);eigres_full=norm(q*v-v*lam)
        scale=norm(hl)
        # Rank-one active column is established by actual saved zero/nonzero
        # weights; no numerical rank tolerance is used.
        active=[u for u in range(k) if weights[u]!=0]
        assert len(active)==1
        u=active[0];h=fc[:,u];hn=(h.H*h)[0]
        def nullpart(x):return x-h*((h.H*x)/hn)
        npc=nullpart(pc);nps=nullpart(ps);npfull=nullpart(p)
        y=mat(a['y']);interference=[]
        for user in range(k):
            sig=abs(y[user,user])**2
            inc=mp.fsum(abs(y[user,j])**2 for j in range(y.cols) if j!=user)+mp.mpf(float(a['noise'][user]))
            old=mp.mpf(float(a['total'][user]))-mp.mpf(float(a['signal'][user]))
            mu_exact=sig/inc
            interference.append(dict(user_zero_based=user,saved_subtraction=s(old),same_saved_y_self_excluded_MP=s(inc),
                subtraction_minus_self_excluded=s(old-inc),relative_subtraction_error=s((old-inc)/inc),
                saved_mu=s(mp.mpf(float(a['mu'][user]))),same_saved_y_direct_mu=s(mu_exact),
                mu_relative_error=s((mp.mpf(float(a['mu'][user]))-mu_exact)/mu_exact) if mu_exact else None))
        dense_error=norm(q-q_exact);lower_error=norm(hl-q_exact)
        return dict(decimal_precision=dps,all_values_from_actual_saved_binary64_operands=True,
            alpha_saved=s(alpha),alpha_original_expression_from_saved_lip_den_MP=s(alpha_formula),
            original_real_arithmetic_structured_eigenvalues=[s(x) for x in eve],
            positive_weight_frozen_structured_eigenvalues=[s(x) for x in evf],
            actual_lower_triangle_Hermitian_eigenvalues=[s(x) for x in evl],
            actual_fullQ_Hermitian_part_eigenvalues=[s(x) for x in evh],
            non_Hermitian_fullQ_Frobenius=s(norm(q-q.H)),
            dense_fullQ_minus_original_structured_Frobenius=s(dense_error),
            effective_lowerQ_minus_original_structured_Frobenius=s(lower_error),
            exact_structured_condition_number=s(max(eve)/min(eve)),
            actual_eigh_lower_eigenpair_residual_Frobenius=s(eigres_lower),
            actual_eigh_fullQ_eigenpair_residual_Frobenius=s(eigres_full),
            relative_lower_eigenpair_residual=s(eigres_lower/scale),
            active_communication_columns_zero_based=active,
            P_communication_nullspace_Frobenius=s(norm(npc)),P_sensing_nullspace_Frobenius=s(norm(nps)),
            actual_fullP_nullspace_Frobenius=s(norm(npfull)),
            communication_null_roundoff_over_sensing_null=s(norm(npc)/norm(nps)) if norm(nps) else None,
            fullP_null_over_alpha_unconstrained_component_norm=s(norm(npfull)/alpha),
            exact_formula_communication_P_in_range_Fc=True,
            actual_interference_and_QT_mu_comparison=interference,
            verdict=dict(original_factored_positive_Q_is_PD=min(eve)>0,
                frozen_positive_weights_factored_Q_is_PD=min(evf)>0,
                actual_eigh_lower_matrix_is_indefinite=min(evl)<0,
                actual_fullQ_Hermitian_part_is_indefinite=min(evh)<0,
                eigh_error_does_not_create_all_negative_curvature=min(evl)<0,
                communication_subtraction_finite_positive=all(mp.mpf(x['saved_subtraction'])>0 for x in interference)))

def run(output):
    output=Path(output);output.mkdir(parents=True,exist_ok=False)
    started=time.perf_counter();paths=[Path(__file__),CAP/'actual-failed-Q-operands.npz',CAP/'actual-failed-Q-capture-or-nonreproduction.json',CAP/'original-scenario.json',HELD]
    before={str(p):sha(p) for p in paths}
    assert before[str(CAP/'actual-failed-Q-operands.npz')]==EXPECTED_NPZ
    cap=json.loads(paths[2].read_text(encoding='utf-8'));scene=json.loads(paths[3].read_text(encoding='utf-8'));held=json.loads(HELD.read_text(encoding='utf-8'))
    assert held['natural_wait_completed'] and held['exact_original_handle_birth_and_exit_match'] and held['all_watched_source_and_job_bytes_unchanged']
    assert held['actual_child_terminal_exit_code']==0 and held['host_errors']==[]
    assert cap['source_unchanged'] and cap['observer_errors']==[] and cap['target_failure_captured'] and cap['effective_capture_exit_code']==0
    tc=cap['target_capture'];assert tc['q_addends_reconstruct_actual_Q_bitwise'] and tc['p_addends_reconstruct_actual_P_bitwise']
    assert scene['rho']==10 and not tc['current_QCQP_nu_assigned_before_failure']
    with np.load(paths[1],allow_pickle=False) as source:a={k:source[k].copy() for k in source.files}
    assert all(np.isfinite(x).all() for x in a.values())
    q=a['q'];qc=a['q_communication'];alpha=float(a['q_sensing'][0,0])
    diag=[dict(index_zero_based=i,Q_diagonal_real=float(q[i,i].real),diagonal_spacing=float(abs(np.spacing(q[i,i].real))),
        alpha_over_diagonal_spacing=alpha/abs(float(np.spacing(q[i,i].real))),
        actual_Q_equals_communication_at_diagonal=bool(q[i,i]==qc[i,i])) for i in range(len(q))]
    lanes=[one_precision(a,scene,dps) for dps in (80,100)]
    after={str(p):sha(p) for p in paths}
    stable_agreement=all(lanes[0]['verdict'][k]==lanes[1]['verdict'][k] for k in lanes[0]['verdict'])
    report=dict(schema='ACTUAL_ISAC014_RHO10_FAILED_Q_SAVED_OPERAND_MP80_MP100_DIAGNOSIS_V1',
        source_before=before,source_after=after,source_interval_closed=before==after,
        actual_held_terminal=dict(owner=held['owner'],child=held['child'],exit_code=held['actual_child_terminal_exit_code'],
            exact_original_handle_birth_and_exit_match=True,all_watched_source_and_job_bytes_unchanged=True),
        actual_failure=dict(rho=scene['rho'],AO_iteration_zero_based=tc['AO_iteration_zero_based'],W_block_call=tc['W_block_call'],
            W_iteration_zero_based=tc['W_iteration_zero_based'],minimum_numpy_eigh_eigenvalue=tc['minimum_actual_eigenvalue'],
            original_failure_retained=True,current_nu_was_not_assigned=True,full_six_or_case_success=False),
        array_transport=dict(NPZ_SHA256=EXPECTED_NPZ,all_finite=True,q_p_addends_bitwise_reconstruct=True,
            sensing_shift_lost_in_every_diagonal=all(x['actual_Q_equals_communication_at_diagonal'] for x in diag),
            actual_full_Q_bytes_equal_communication_Q_bytes=q.tobytes()==qc.tobytes(),diagonal_ULP_rows=diag),
        MP_lanes=lanes,MP80_MP100_classifications_agree=stable_agreement,
        supported_cause='A positive rho10 sensing shift is smaller than every dense Gram diagonal ULP and is lost. Rank-one positive communication Gram rounding creates a non-Hermitian full array and a genuinely indefinite effective lower-triangle Hermitian matrix. The original eigh guard rejects that stored matrix before any current QCQP multiplier is assigned. It is not a rho0 theoretical singularity.',
        communication_cancellation_scope='The saved total-minus-signal has a separately quantified positive relative error; weights remain nonnegative. It does not explain negative curvature of the exact positive structured Q. No SINR or convergence gate is upgraded.',
        mathematically_equivalent_remedy=dict(Q='Retain Q = alpha I + Fc diag((1+mu)|eta|^2/ln2) Fc^H as a positive structured representation; retain alpha separately rather than add it to huge dense diagonal entries.',
            P='Retain communication P as Fc times its original coefficient matrix plus the original sensing P separately; avoid cancellation-induced nullspace components from a separately rounded dense dominant P.',
            solve='Use a factored/low-rank or guarded higher-precision solution of the unchanged (Q+nu I)W=P and original power-dual equation, with original tolerance/budget. Diagnose at fixed saved inputs before any whole-trajectory claim.',
            not_supported='No eigenvalue clipping, diagonal jitter, pseudo-inverse fallback, replacement objective, changed tolerance, or claim that symmetrizing alone recovers lost alpha.',
            implementation_or_full_trajectory_executed=False),
        scope=dict(saved_mathematics_only=True,optimizer_calls=0,RNG_calls=0,MC_calls=0,new_channels=0,
            full_KKT_solve_or_multiplier_recovery=False,original_algorithm_convergence_PASS=False,reference_PASS=False,full_paper_PASS=False),
        elapsed_seconds=time.perf_counter()-started)
    put(output/'ACTUAL_ISAC014_RHO10_POSITIVE_STRUCTURED_Q_DENSE_ROUNDOFF_AND_LOWER_EIGH_MP80_MP100_CAUSE_V1.json',report)
    print(json.dumps(dict(source_interval_closed=report['source_interval_closed'],classifications_agree=stable_agreement,
        diagonal_shift_lost=report['array_transport']['sensing_shift_lost_in_every_diagonal'],lanes=[dict(dps=x['decimal_precision'],alpha=x['alpha_saved'],lower_min=x['actual_lower_triangle_Hermitian_eigenvalues'][0],structured_min=x['original_real_arithmetic_structured_eigenvalues'][0],Pcomm_null=x['P_communication_nullspace_Frobenius']) for x in lanes])))
    return 0 if before==after and stable_agreement else 1

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--output-dir',type=Path,required=True);a=ap.parse_args();raise SystemExit(run(a.output_dir))
