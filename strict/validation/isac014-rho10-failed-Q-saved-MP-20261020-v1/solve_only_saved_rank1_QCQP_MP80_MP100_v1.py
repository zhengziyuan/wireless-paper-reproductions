"""Independent rank-one algebra on the single captured QCQP, never a trajectory run."""
from pathlib import Path
import importlib.util,json,argparse,time
import numpy as np
import mpmath as mp
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('saved_Q_ref',HERE/'diagnose_saved_actual_Q_MP80_MP100_v1.py')
base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)

def precision(a,scene,dps):
    with mp.workdps(dps):
        fc=base.mat(a['fc']);fs=base.mat(a['fs']);w0=base.mat(a['w']);ga=base.mat(a['ga'])
        n,k=np.asarray(a['fc']).shape;den=mp.mpf(float(a['den']));rho=mp.mpf(scene['rho']);lip=mp.fsum(mp.mpf(float(v)) for v in a['lip'])
        alpha=rho*lip/(2*den);iota=mp.mpf(float(a['iota']));pd=base.mat(a['pd'])
        weights=[(1+mp.mpf(float(a['mu'][u])))*abs(base.z(a['eta'][u]))**2/mp.log(2) for u in range(k)]
        active=[u for u,x in enumerate(weights) if x!=0];assert len(active)==1
        u=active[0];h=fc[:,u];hn=(h.H*h)[0];dominant=weights[u]*hn
        pc=mp.matrix(n,w0.cols)
        for user in range(k):
            c=(1+mp.mpf(float(a['mu'][user])))*base.z(a['eta'][user])/mp.log(2)
            for i in range(n):pc[i,user]=fc[i,user]*c
        ps=rho/(2*den)*(lip*w0-ga);p_exact=pc+ps
        cap=mp.mpf(scene['power']);Q=mp.eye(n)*alpha+weights[u]*(h*h.H)
        def physical(w):
            y=fc.H*w;zz=fs.H*w;rate=mp.mpf('0')
            for user in range(k):
                signal=abs(y[user,user])**2
                interf=mp.fsum(abs(y[user,j])**2 for j in range(y.cols) if j!=user)+mp.mpf(float(a['noise'][user]))
                rate+=mp.log1p(signal/interf)/mp.log(2)
            pattern=mp.matrix([mp.fsum(abs(zz[i,j])**2 for j in range(zz.cols)) for i in range(zz.rows)])
            nmse=base.norm(pattern-iota*pd)**2/(iota*iota*(pd.H*pd)[0])
            return dict(rate=base.s(rate),NMSE=base.s(mp.re(nmse)),utility=base.s(rate-rho*mp.re(nmse)))
        def solve(p,label):
            par=h*((h.H*p)/hn);perp=p-par
            def w(nu):return perp/(alpha+nu)+par/(alpha+nu+dominant)
            def power(nu):return base.norm(w(nu))**2
            pzero=power(mp.mpf('0'));steps=0
            if pzero<=cap:nu=mp.mpf('0');lo=hi=nu
            else:
                lo=mp.mpf('0');hi=mp.mpf('1')
                while power(hi)>cap:hi*=2
                # This independent reference locates the same scalar dual
                # root more accurately; it does not alter production controls.
                while hi-lo>mp.power(10,-dps+20)*max(1,hi):
                    mid=(lo+hi)/2
                    if power(mid)>cap:lo=mid
                    else:hi=mid
                    steps+=1
                nu=hi
            ww=w(nu);pw=power(nu);res=(Q+nu*mp.eye(n))*ww-p
            return dict(scope=label,nu=base.s(nu),unconstrained_power=base.s(pzero),power=base.s(pw),power_cap=base.s(cap),
                primal_power_slack=base.s(cap-pw),stationarity_Frobenius=base.s(base.norm(res)),
                relative_stationarity=base.s(base.norm(res)/(base.norm(Q)*base.norm(ww)+base.norm(p))),
                complementarity=base.s(nu*(cap-pw)),dual_nonnegative=nu>=0,feasible=pw<=cap,
                positive_shift_min_eigenvalue=base.s(alpha+nu),root_bisection_steps=steps,
                original_production_bisection_tolerance_changed=False,
                independent_reference_root_accuracy_only=True,
                solution_minus_original_incumbent_Frobenius=base.s(base.norm(ww-w0)),
                same_saved_fixed_channels_physical_objective=physical(ww),
                positive_structure_KKT_PASS=nu>=0 and pw<=cap and base.norm(res)<mp.power(10,-dps+30))
        return dict(decimal_precision=dps,exact_original_expression_Q_and_P_from_saved_coefficients=solve(p_exact,'Unrounded original algebra from actual saved fc/mu/eta/lip/ga/den; alpha and sensing P retained separately'),
            structured_Q_but_original_dense_saved_P=solve(base.mat(a['p']),'Counterfactual diagnostic: repair positive Q representation alone while retaining corrupted dense saved P'),
            exact_original_P_minus_actual_dense_P_Frobenius=base.s(base.norm(p_exact-base.mat(a['p']))),
            original_incumbent_physical_objective=physical(w0),
            scope='Only one captured fixed QCQP and fixed-channel scalar contractions; no original optimizer function is imported or executed.')

def run(output):
    output=Path(output);output.mkdir(parents=True,exist_ok=False);started=time.perf_counter()
    paths=[Path(__file__),Path(base.__file__),base.CAP/'actual-failed-Q-operands.npz',base.CAP/'original-scenario.json',base.CAP/'actual-failed-Q-capture-or-nonreproduction.json',base.HELD]
    before={str(p):base.sha(p) for p in paths};assert before[str(paths[2])]==base.EXPECTED_NPZ
    held=json.loads(paths[-1].read_text());cap=json.loads(paths[-2].read_text());assert held['all_watched_source_and_job_bytes_unchanged'] and held['exact_original_handle_birth_and_exit_match'] and held['actual_child_terminal_exit_code']==0 and cap['target_failure_captured'] and cap['source_unchanged']
    with np.load(paths[2],allow_pickle=False) as src:a={k:src[k].copy() for k in src.files}
    scene=json.loads(paths[3].read_text());lanes=[precision(a,scene,d) for d in (80,100)]
    after={str(p):base.sha(p) for p in paths}
    report=dict(schema='ACTUAL_ISAC014_SINGLE_CAPTURED_ORIGINAL_QCQP_MP80_MP100_PRIMAL_DUAL_AND_P_ROUNDOFF_V1',
        source_before=before,source_after=after,source_interval_closed=before==after,MP_lanes=lanes,
        actual_failed_Q_guard_retained=True,actual_current_nu_was_unassigned=True,
        saved_fixed_QCQP_reference_not_original_full_optimization=True,production_sources_changed=False,
        new_trajectory_optimizer_or_MC_or_RNG_calls=0,full_algorithm_or_reference_PASS=False,elapsed_seconds=time.perf_counter()-started)
    base.put(output/'ACTUAL_ISAC014_SINGLE_CAPTURED_ORIGINAL_QCQP_MP80_MP100_PRIMAL_DUAL_AND_P_ROUNDOFF_V1.json',report)
    print(json.dumps(dict(source_interval_closed=before==after,lanes=[dict(dps=x['decimal_precision'],exact=x['exact_original_expression_Q_and_P_from_saved_coefficients'],denseP=x['structured_Q_but_original_dense_saved_P']) for x in lanes])))
    return 0 if before==after and all(x['exact_original_expression_Q_and_P_from_saved_coefficients']['positive_structure_KKT_PASS'] for x in lanes) else 1
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output-dir',type=Path,required=True);a=p.parse_args();raise SystemExit(run(a.output_dir))
