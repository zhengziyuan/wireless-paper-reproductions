"""Independent full200 MATLAB physical/history audit, outside live science.

No production numerical module is imported. Batched fixed-beam QT/waterfill
is checked against an independent per-realization scalar oracle on all1000
draws of the first case before any full-bank gate is reported.
"""
from pathlib import Path
import argparse, hashlib, json, os, time, traceback
import numpy as np

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def rate(h, w, noise):
    gain = np.abs(h.conj().T @ w) ** 2
    signal = np.diag(gain)
    return float(np.log2(1 + signal / (gain.sum(axis=1) - signal + noise)).sum())

def diagonal_kkt(q, b, power, tol):
    def at(lam):
        denom = q + lam
        z = np.zeros_like(b)
        ok = denom > 0
        z[ok] = b[ok] / denom[ok]
        if np.any(np.abs(b[~ok]) > tol):
            return None
        return z
    z = at(0.)
    if z is not None and np.vdot(z, z).real <= power:
        return z
    lo, hi = 0., 1.
    while np.vdot(at(hi), at(hi)).real > power:
        hi *= 2
    while hi - lo > tol * max(1., hi):
        mid = (lo + hi) / 2
        if np.vdot(at(mid), at(mid)).real > power:
            lo = mid
        else:
            hi = mid
    return at(hi)

def fixed(h, power, noise, kind, spec):
    h = h / np.sqrt(noise)[None, :]
    m = h.shape[1]
    if kind == "FPA-ZF":
        v = h @ np.linalg.solve(h.conj().T @ h, np.eye(m))
        v = v / np.linalg.norm(v, axis=0)
        cost = 1 / (np.abs(np.diag(h.conj().T @ v)) ** 2)
        lo, hi = 0., power + max(cost)
        while hi - lo > spec["bisection_tolerance"]:
            mid = (hi + lo) / 2
            if np.maximum(mid - cost, 0).sum() > power:
                hi = mid
            else:
                lo = mid
        w = v * np.sqrt(np.maximum(lo - cost, 0))[None, :]
        return rate(h, w, np.ones(m)), True, float(np.sum(abs(w) ** 2))
    v = h / np.linalg.norm(h, axis=0)
    w = v * np.sqrt(power / m)
    before = rate(h, w, np.ones(m))
    stopped = False
    for _ in range(spec["maximum_iterations"]):
        hw = h.conj().T @ w
        total = np.sum(abs(hw) ** 2, axis=1) + 1
        sig = abs(np.diag(hw)) ** 2
        alpha = sig / (total - sig)
        eta = np.diag(hw) / total
        if kind == "FPA-MRT":
            hv = h.conj().T @ v
            q = (((1 + alpha) * abs(eta) ** 2)[:, None] * abs(hv) ** 2).sum(axis=0) / np.log(2)
            b = (1 + alpha) * np.real(np.conj(eta) * np.diag(hv)) / np.log(2)
            w = v * diagonal_kkt(q, b, power, spec["bisection_tolerance"])[None, :]
        else:
            q = (h * ((1 + alpha) * abs(eta) ** 2)[None, :]) @ h.conj().T / np.log(2)
            b = h * ((1 + alpha) * eta)[None, :] / np.log(2)
            val, vec = np.linalg.eigh(q)
            assert val.min() >= -spec["spectral_zero_tolerance"] * max(float(val.max()), 1.)
            val = np.maximum(val, 0)
            z = vec.conj().T @ b
            norm = np.sqrt((abs(z) ** 2).sum(axis=1))
            amp = diagonal_kkt(val, norm, power, spec["bisection_tolerance"])
            denom = np.divide(norm, amp, out=np.ones_like(norm), where=amp > 0)
            w = vec @ (z / denom[:, None])
        after = rate(h, w, np.ones(m))
        assert after >= before - 1e-9
        if (after - before) / abs(before) < spec["fractional_tolerance"]:
            stopped = True
            break
        before = after
    return after, stopped, float(np.sum(abs(w) ** 2))


def rates_batch(h, w, noise):
    gain = abs(h.conj().transpose(0,2,1) @ w)**2
    signal = np.diagonal(gain, axis1=1, axis2=2)
    return np.log2(1+signal/(gain.sum(axis=2)-signal+noise)).sum(axis=1)


def amplitudes_batch(q, b, power, tol):
    def at(lam):
        den=q+lam[:,None]
        return np.divide(b, den, out=np.zeros_like(b), where=den>0)
    zero=np.zeros(len(q)); z=at(zero)
    free=(np.sum(abs(z)**2,axis=1)<=power)&np.all((q>0)|(abs(b)<=tol),axis=1)
    lo=np.zeros(len(q)); hi=np.ones(len(q))
    mask=~free
    while np.any(mask & (np.sum(abs(at(hi))**2,axis=1)>power)):
        grow=mask & (np.sum(abs(at(hi))**2,axis=1)>power); hi[grow]*=2
        assert np.all(np.isfinite(hi)), 'No finite diagonal multiplier bracket'
    while True:
        active=mask & ((hi-lo)>tol*np.maximum(1,hi))
        if not np.any(active): break
        mid=(lo+hi)/2; exceed=np.sum(abs(at(mid))**2,axis=1)>power
        lo=np.where(active&exceed,mid,lo); hi=np.where(active&~exceed,mid,hi)
    result=at(hi); result[free]=z[free]
    return result


def fixed_batch(h, power, noise, kind, spec):
    h=h/np.sqrt(noise)[None,None,:]; count,n,m=h.shape
    if kind=='FPA-ZF':
        q,r=np.linalg.qr(h,mode='reduced')
        v=q@np.linalg.solve(r.conj().transpose(0,2,1),np.broadcast_to(np.eye(m),(count,m,m)))
        v=v/np.linalg.norm(v,axis=1)[:,None,:]
        cost=1/abs(np.diagonal(h.conj().transpose(0,2,1)@v,axis1=1,axis2=2))**2
        lo=np.zeros(count); hi=power+np.max(cost,axis=1)
        while True:
            active=(hi-lo)>spec['bisection_tolerance']
            if not np.any(active):break
            mid=(hi+lo)/2; exceed=np.maximum(mid[:,None]-cost,0).sum(axis=1)>power
            lo=np.where(active&~exceed,mid,lo);hi=np.where(active&exceed,mid,hi)
        w=v*np.sqrt(np.maximum(lo[:,None]-cost,0))[:,None,:]
        return rates_batch(h,w,1),np.ones(count,bool),np.sum(abs(w)**2,axis=(1,2))
    v=h/np.linalg.norm(h,axis=1)[:,None,:]
    w=v*np.sqrt(power/m); before=rates_batch(h,w,1); stopped=np.zeros(count,bool)
    result=before.copy(); powers=np.sum(abs(w)**2,axis=(1,2))
    for iteration in range(spec['maximum_iterations']):
        rows=np.where(~stopped)[0]
        if not len(rows):break
        hh,ww,vv=h[rows],w[rows],v[rows]
        hw=hh.conj().transpose(0,2,1)@ww
        total=np.sum(abs(hw)**2,axis=2)+1; signal=abs(np.diagonal(hw,axis1=1,axis2=2))**2
        alpha=signal/(total-signal);eta=np.diagonal(hw,axis1=1,axis2=2)/total
        if kind=='FPA-MRT':
            hv=hh.conj().transpose(0,2,1)@vv
            q=(((1+alpha)*abs(eta)**2)[:,:,None]*abs(hv)**2).sum(axis=1)/np.log(2)
            b=(1+alpha)*np.real(eta.conj()*np.diagonal(hv,axis1=1,axis2=2))/np.log(2)
            new=vv*amplitudes_batch(q,b,power,spec['bisection_tolerance'])[:,None,:]
        elif kind=='FPA-OPT':
            q=(hh*((1+alpha)*abs(eta)**2)[:,None,:])@hh.conj().transpose(0,2,1)/np.log(2)
            b=hh*((1+alpha)*eta)[:,None,:]/np.log(2)
            val,vec=np.linalg.eigh(q)
            assert np.all(val[:,0]>=-spec['spectral_zero_tolerance']*np.maximum(val[:,-1],1))
            val=np.maximum(val,0); z=vec.conj().transpose(0,2,1)@b
            norms=np.sqrt((abs(z)**2).sum(axis=2)); amp=amplitudes_batch(val,norms,power,spec['bisection_tolerance'])
            den=np.divide(norms,amp,out=np.ones_like(norms),where=amp>0)
            new=vec@(z/den[:,:,None])
        else:raise ValueError(kind)
        after=rates_batch(hh,new,1); assert np.all(after>=before[rows]-1e-9)
        stopped[rows]=(after-before[rows])/abs(before[rows])<spec['fractional_tolerance']
        w[rows]=new; before[rows]=after;result[rows]=after;powers[rows]=np.sum(abs(new)**2,axis=(1,2))
    return result,stopped,powers


def geometry_functions(job,cfg):
    n,m=job['N'],job['M']; power,kap=job['power'],job['kappa'];geom=job['geometry']
    el,az=np.array(geom['elevation']),np.array(geom['azimuth'])
    directions=np.c_[np.cos(el)*np.sin(az),np.sin(el)]
    beta=1e-4*np.array(geom['distances_m'])**-2.8;noise=np.full(m,1e-11)
    nr,nc=cfg['antenna_factorization'][str(n)]
    initial=np.array([[x,y]for x in(np.arange(nr)-(nr-1)/2)/2 for y in(np.arange(nc)-(nc-1)/2)/2])
    lower,upper=-np.array([nr,nc])*job['A']/2,np.array([nr,nc])*job['A']/2
    draws=np.array(job['nlos_re'])+1j*np.array(job['nlos_im'])
    def channel(t):
        return np.exp(2j*np.pi*(t@directions.T))[None,:,:]*np.sqrt(beta*kap/(kap+1))[None,None,:]+draws*np.sqrt(beta/(kap+1))[None,None,:]
    def design(t,mode):
        H=np.exp(2j*np.pi*(t@directions.T))
        if mode=='zf':
            sigma=np.eye(m)/(kap+1)+kap/(kap+1)*(H.conj().T@H)/n
            eta=power*beta*(n-m)/(m*noise)
            return float(np.log2(1+eta/np.real(np.diag(np.linalg.solve(sigma,np.eye(m))))).sum())
        numerator=beta**2*(n*n+n*(2*kap+1)/(kap+1)**2)
        denominator=noise*n*beta.sum()/power
        for u in range(m):
            for v in range(m):
                if u!=v:
                    inner=np.sum(np.exp(2j*np.pi*(t@(directions[u]-directions[v]))))
                    denominator[u]+=beta[u]*beta[v]*(kap*kap*abs(inner)**2+n*(2*kap+1))/(kap+1)**2
        return float(np.log2(1+numerator/denominator).sum())
    return initial,lower,upper,draws,noise,channel,design


def ma_rates(h,power,noise,mode):
    if mode=='mrt':
        w=h*np.sqrt(power/np.sum(abs(h)**2,axis=(1,2)))[:,None,None]
    else:
        count,n,m=h.shape;q,r=np.linalg.qr(h,mode='reduced')
        v=q@np.linalg.solve(r.conj().transpose(0,2,1),np.broadcast_to(np.eye(m),(count,m,m)))
        w=v/np.linalg.norm(v,axis=1)[:,None,:]*np.sqrt(power/m)
    return rates_batch(h,w,noise),np.sum(abs(w)**2,axis=(1,2))


def audit_case(mat,job,cfg,scalar_oracle=False):
    n,m=job['N'],job['M'];power=job['power']; initial,lower,upper,draws,noise,channel,design=geometry_functions(job,cfg)
    assert n==6 and m==5 and len(draws)==1000 and cfg['geometry_realizations']==100
    assert mat['matlab_source_version']=='MATLAB-full-v2-history-storage'
    assert mat['runtime_source_identity']['fresh_before_after_not_persistent_cache']
    histories={};allchecks=[]
    for mode in ['mrt','zf']:
        history=mat['history'][mode]; obj=np.array(history['objective']);positions=np.array(history['positions'])
        assert positions.shape==(len(obj),n,2) and np.array_equal(positions[0],initial)
        direct=np.array([design(t,mode)for t in positions]);error=float(np.max(abs(direct-obj)))
        stop=float((obj[-1]-obj[-2])/abs(obj[-2]))
        assert error<1e-9 and np.all(np.diff(obj)>=-cfg['verification_tolerance'])
        assert history['converged'] and history['termination']=='fractional_increase' and stop<cfg['fractional_increase_threshold']
        distances=np.linalg.norm(positions[:,:,None]-positions[:,None,:],axis=3)+np.eye(n)[None]*1e9
        assert distances.min()>=.5-cfg['verification_tolerance']
        assert np.all(positions>=lower-cfg['verification_tolerance']) and np.all(positions<=upper+cfg['verification_tolerance'])
        updates=history['coordinate_updates'];assert len(updates)==(len(obj)-1)*n
        max_coordinate_rate_error=0.; max_gap_ratio=max_constraint_ratio=0.
        for i,update in enumerate(updates):
            sweep,antenna=i//n,i%n;cert=update['certificate']
            assert update['sweep']==sweep and update['antenna']==antenna
            # Each coordinate state is reconstructed from the two sweep
            # endpoints and the documented antenna order, not a guessed path.
            pre=positions[sweep].copy();pre[:antenna]=positions[sweep+1,:antenna]
            post=pre.copy();post[antenna]=positions[sweep+1,antenna]
            errs=[abs(design(pre,mode)-update['before']),abs(design(post,mode)-update['after'])]
            max_coordinate_rate_error=max(max_coordinate_rate_error,*errs)
            assert max(errs)<1e-9
            displacement=post[antenna]-pre[antenna]
            for v in range(n):
                if v!=antenna:
                    d=pre[antenna]-pre[v]
                    assert 2*d@displacement+d@d>=.25-cfg['verification_tolerance']
            assert update['original_subproblem_unchanged'] and cert['original_subproblem_unchanged'] and cert['certified_without_conic_solver_status']
            values=[cert[k] for k in ['global_objective_gap_upper_bound','global_objective_gap_tolerance','maximum_normalized_constraint_violation','normalized_constraint_tolerance']]
            assert np.all(np.isfinite(values)) and min(values)>=0
            assert values[0]<=values[1] and values[2]<=values[3]
            max_gap_ratio=max(max_gap_ratio,values[0]/values[1]);max_constraint_ratio=max(max_constraint_ratio,values[2]/values[3])
            assert abs(update['surrogate']-update['before']-cert['minorant_increment'])<1e-9
            assert abs(update['after']-update['surrogate']-update['lower_bound_gap'])<1e-9
            assert update['after']>=update['before']-1e-9 and update['lower_bound_gap']>=-1e-9
        means=[]
        for t in positions:
            vals,powers=ma_rates(channel(t),power,noise,mode);means.append(float(np.mean(vals)))
            assert len(vals)==1000 and np.all(np.isfinite(vals)) and np.max(powers)-power<1e-9
        if mode=='mrt':
            mc_error=float(np.max(abs(np.array(means)-np.array(history['instantaneous_MC_mean']))))
            assert mc_error<1e-9
        else:mc_error=None
        histories[mode]={'accepted_position_count':len(obj),'all_position_and_linearized_spacing_constraints':True,
            'all_design_objectives_freshly_recomputed':True,'max_design_abs_error':error,
            'all_ordered_coordinate_states_reconstructed_and_rate_identities_verified':True,
            'coordinate_count':len(updates),'max_coordinate_objective_abs_error':max_coordinate_rate_error,
            'all_finite_certificate_bounds_and_minorant_identities_verified':True,
            'certificate_gap_max_ratio':max_gap_ratio,'certificate_constraint_max_ratio':max_constraint_ratio,
            'final_fractional_increase':stop,'original_threshold':cfg['fractional_increase_threshold'],
            'original_stop_verified':True,'every_accepted_position_all1000_MC_freshly_evaluated':True,
            'MC_means':means,'saved_mrt_MC_history_max_abs_error':mc_error}
    schemes={}
    oracle=[]
    for kind in ['MA-MRT','MA-ZF','FPA-MRT','FPA-ZF','FPA-OPT']:
        pos=np.array(mat['metrics']['mrt_realized_positions' if kind=='MA-MRT' else 'zf_realized_positions']) if kind.startswith('MA') else initial
        H=channel(pos)
        if kind.startswith('MA'):
            values,powers=ma_rates(H,power,noise,'mrt' if kind=='MA-MRT' else 'zf');stops=np.ones(1000,bool)
        else:
            values,stops,powers=fixed_batch(H,power,noise,kind,cfg['benchmark_solver'])
            if scalar_oracle:
                independent=[fixed(h,power,noise,kind,cfg['benchmark_solver'])for h in H]
                oldvalues=np.array([v[0]for v in independent]);oldstop=np.array([v[1]for v in independent])
                err=float(np.max(abs(values-oldvalues)))
                assert err<1e-7 and np.all(stops==oldstop)
                oracle.append({'scheme':kind,'all1000_scalar_QT_or_waterfill_reference_checked':True,'max_batch_scalar_rate_error':err,
                    'all_per_realization_stop_gates_agree':True,'rate_atol':1e-7})
        raw=mat['metrics']['schemes'][kind.replace('-','_')]; saved=np.array(raw['sample_sum_rates'])
        assert len(saved)==1000 and np.all(np.isfinite(saved))
        error=float(np.max(abs(saved-values)));meanerror=float(abs(raw['mean_sum_rate']-np.mean(saved)))
        assert error<1e-7 and meanerror<1e-9 and np.all(stops) and np.max(powers)-power<1e-9
        assert raw.get('nonconverged_samples',0)==0
        schemes[kind]={'sample_count':1000,'all_samples_freshly_recomputed':True,'sample_rate_atol':1e-7,
            'max_sample_rate_abs_error':error,'saved_mean_identity_abs_error':meanerror,'all1000_stops':True,
            'maximum_power_excess':float(np.max(powers)-power),'all_power_constraints':True}
    return {'all_independent_numeric_gates':True,'histories':histories,'schemes':schemes,
        'scalar_oracle_full1000_checks':oracle,'certificate_scope':'saved finite global bounds plus independent physical/minorant/constraint identities; not independent full re-solution of every subproblem'}


def atomic(path,obj):
    path.parent.mkdir(parents=True,exist_ok=True)
    temporary=path.with_name(path.name+'.tmp')
    temporary.write_text(json.dumps(obj,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    for attempt in range(8):
        try:os.replace(temporary,path);return
        except PermissionError:
            if attempt==7:raise
            time.sleep(.1*(attempt+1))


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--bank',required=True);parser.add_argument('--inputs-bank',required=True);parser.add_argument('--out',required=True)
    parser.add_argument('--public',required=True);parser.add_argument('--maximum-cases',type=int,default=200)
    args=parser.parse_args();bank=Path(args.bank).resolve();inputs=Path(args.inputs_bank).resolve();out=Path(args.out).resolve();public=Path(args.public).resolve()
    assert args.maximum_cases==200,'This is the full200 audit; no reduced production selector.'
    cfgpath=inputs/'run_config.json';cfg=json.loads(cfgpath.read_bytes())
    jobs=sorted((inputs/'jobs').glob('case-*-mc-*.json'));assert len(jobs)==200
    fp='e78708e52bbfe9733a9fe24faaa736188015469a9d87ea90b41c5a1d0966bf37'
    files=[cfgpath,Path(__file__)]+jobs+[bank/(p.stem+'-matlab.json')for p in jobs]
    def identity_key(p):
        if p.is_relative_to(bank):return 'raw/'+str(p.relative_to(bank))
        if p.is_relative_to(inputs):return 'inputs/'+str(p.relative_to(inputs))
        return 'independent_audit_script'
    hashes={identity_key(p):sha(p)for p in files}
    freeze={'scope':'source_frozen_before_independent_full200_actual_MATLAB_audit',
        'all200_original_inputs_and_actual_raw_results_sha256':hashes,'source_fingerprint':fp,
        'batch_algorithms_are_same_QT_waterfill_and_QR_ZF_not_surrogate_benchmarks':True,
        'independent_oracle_first_case_all1000_required_before_full_bank':True,
        'no_production_scientific_modules_imported':True,'full200_independent_pass_not_yet_claimed':True}
    assert not out.exists();atomic(out.with_name(out.stem+'-freeze.json'),freeze)
    started=time.perf_counter();records=[];failures=[]
    for index,jobpath in enumerate(jobs):
        rawpath=bank/(jobpath.stem+'-matlab.json')
        try:
            mat,job=json.loads(rawpath.read_bytes()),json.loads(jobpath.read_bytes())
            expected=hashlib.sha256(b'strict-v1\0'+cfgpath.read_bytes()+b'\0'+jobpath.read_bytes()).hexdigest()
            assert mat['implementation_fingerprint']==fp and mat['input_fingerprint']==expected
            record=audit_case(mat,job,cfg,scalar_oracle=index==0)
            record.update(case=jobpath.stem,input_fingerprint=expected,raw_sha256=sha(rawpath))
            records.append(record)
        except Exception as exc:
            failure={'case':jobpath.stem,'type':type(exc).__name__,'message':str(exc),'stack':traceback.format_exc()}
            failures.append(failure);print(json.dumps(failure),flush=True)
        progress={'scope':'independent_full200_actual_MATLAB_full_v2_no_full_Python_claim',
            'expected_cases':200,'attempted_cases':index+1,'passed_cases':len(records),'failed_cases':len(failures),
            'all_attempted':index+1==200,'all200_independent_gates_passed':index+1==200 and not failures,
            'full_original_geometry100_per_case_N6_M5_and_NLoS1000_retained':True,
            'draw_counts_configured_not_disclosed_author_MC_counts':True,
            'records':records,'failures':failures,'elapsed_seconds':time.perf_counter()-started,
            'original_curve_closeness_claimed':False,'Python_full200_or300_execution_claimed':False,
            'freeze_sha256':sha(out.with_name(out.stem+'-freeze.json'))}
        atomic(out,progress)
        print(json.dumps({'attempted':index+1,'passed':len(records),'failed':len(failures),'elapsed':progress['elapsed_seconds']}),flush=True)
        if index==0 and failures:break  # No batch promotion after scalar-oracle/preflight failure.
    assert hashes=={identity_key(p):sha(p)for p in files}
    compact={k:v for k,v in progress.items()if k!='records'}
    compact['records']=[{**row,'histories':{mode:{k:v for k,v in hist.items()if k!='MC_means'}for mode,hist in row['histories'].items()}}for row in records]
    compact['raw_MC_evidence_preserved_in_WORK_output']=True
    compact['all_sources_inputs_raw_outputs_unchanged_at_end']=True
    atomic(public,compact)
    assert progress['all200_independent_gates_passed'],'Retain any failures/partial audit; never relax gates or claim all200.'


if __name__=='__main__':main()
