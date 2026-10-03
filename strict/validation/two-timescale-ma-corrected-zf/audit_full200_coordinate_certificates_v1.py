"""Independent original-SCA concavity certificates for all actual200 cases.

Reconstructs each coordinate state; derives the same published minorants
without importing production core/solver. A concave tangent plane maximized
over every spacing/box polygon vertex certifies the global objective gap.
Vertices outside the ZF logarithm domain are never evaluated in the objective.
Only the finite accepted point's gradient is needed for the linear bound.
"""
from pathlib import Path
import argparse, json, time, traceback
import numpy as np
from audit_full200_matlab_v1 import sha, atomic, geometry_functions


def largest_real_symmetric_2x2(matrix):
    return float((matrix[0,0]+matrix[1,1]+np.hypot(matrix[0,0]-matrix[1,1],2*matrix[0,1]))/2)


def mrt_expansion(t, antenna, directions, beta, noise, power, kap):
    n,m=t.shape[0],len(beta);wave=2*np.pi
    numerator=beta**2*(n*n+n*(2*kap+1)/(kap+1)**2)
    denominators=noise*n*np.sum(beta)/power
    gradients=np.zeros((m,2));curvatures=np.zeros(m)
    for u in range(m):
        bound=np.zeros((2,2))
        for v in range(m):
            if v==u:continue
            direction=directions[u]-directions[v]
            phases=np.exp(1j*wave*(t@direction));sumphase=np.sum(phases)
            scale=beta[u]*beta[v]*kap*kap/(kap+1)**2
            denominators[u]+=scale*abs(sumphase)**2+beta[u]*beta[v]*n*(2*kap+1)/(kap+1)**2
            gradients[u]+=2*scale*np.real(sumphase.conjugate()*1j*wave*phases[antenna])*direction
            bound+=scale*abs(np.sum(np.delete(phases,antenna)))*abs(np.outer(direction,direction))
        curvatures[u]=2*wave*wave*largest_real_symmetric_2x2(bound)
    weights=numerator/(np.log(2)*denominators*(denominators+numerator))
    return -weights@gradients,float(weights@curvatures)


def zf_expansion(t, antenna, directions, beta, noise, power, kap):
    n,m=t.shape[0],len(beta);h=np.exp(2j*np.pi*(t@directions.T));scale=np.sqrt(kap/(kap+1))
    # Sum only the other rows, rather than subtracting the coordinate outer
    # product from the full Gram matrix. Same mathematical Theta2.
    others=np.delete(h,antenna,axis=0)
    theta2=np.eye(m)/(kap+1)+(kap/(kap+1))*(others.conj().T@others)/n
    inv=np.linalg.inv(theta2);y=n/m*np.eye(m)+(kap/(kap+1))*inv
    g=h[antenna].conj();quadratic=float(np.real(g.conj()@y@g))
    eta=power*beta*(n-m)/(m*noise);base=[];gradients=[];curvatures=[]
    for u in range(m):
        ell=(inv*scale)[u].conj();x=inv[u,u].real*y-np.outer(ell,ell.conj())
        den=float(np.real(g.conj()@x@g));assert den>0
        largest=float(np.linalg.eigvalsh(x)[-1])
        q=2/den*(g.conj()@(y-quadratic/den*(x-largest*np.eye(m))))
        # Derive cos/sin from complex products, without source phase/angle
        # extraction, avoiding an independent trigonometric cancellation.
        gradients.append(-2*np.pi*np.imag(q.conj()*h[antenna])@directions)
        bound=sum(abs(q[v])*abs(np.outer(directions[v],directions[v]))for v in range(m))
        curvatures.append(4*np.pi*np.pi*largest_real_symmetric_2x2(bound))
        base.append(quadratic/den+1/eta[u])
    return np.array(base),np.array(gradients),np.array(curvatures)


def polygon_vertices(t,antenna,lower,upper):
    A=[[-1.,0.],[0.,-1.],[1.,0.],[0.,1.]]
    b=[*(t[antenna]-lower),*(upper-t[antenna])]
    for j in range(len(t)):
        if j!=antenna:
            d=t[antenna]-t[j];A.append(-2*d);b.append(float(d@d-.25))
    A,b=np.array(A),np.array(b);norm=np.linalg.norm(A,axis=1)
    assert np.all(norm>0)
    A=A/norm[:,None];b=b/norm
    tolerance=2e-12*max(1.,float(np.max(abs(b))))
    vertices=[]
    for i in range(len(A)):
        for j in range(i):
            det=A[i,0]*A[j,1]-A[i,1]*A[j,0]
            if abs(det)<=1e-13:continue
            point=np.array([(b[i]*A[j,1]-A[i,1]*b[j])/det,
                (A[i,0]*b[j]-b[i]*A[j,0])/det])
            if np.max(A@point-b)<=tolerance:
                vertices.append(point)
    assert len(vertices)>0
    return A,b,np.array(vertices),tolerance


def check_case(raw,job,cfg):
    initial,lower,upper,draws,noise,channel,design=geometry_functions(job,cfg)
    geom=job['geometry'];elev,az=np.array(geom['elevation']),np.array(geom['azimuth'])
    directions=np.c_[np.cos(elev)*np.sin(az),np.sin(elev)];beta=1e-4*np.array(geom['distances_m'])**-2.8
    result={}
    for mode in ['mrt','zf']:
        hist=raw['history'][mode];positions=np.array(hist['positions']);updates=hist['coordinate_updates']
        max_gap_ratio=max_primal_ratio=max_increment_error=0.;negative_domain_vertices=0
        for i,record in enumerate(updates):
            sweep,antenna=i//job['N'],i%job['N']
            assert record['sweep']==sweep and record['antenna']==antenna
            pre=positions[sweep].copy();pre[:antenna]=positions[sweep+1,:antenna]
            delta=positions[sweep+1,antenna]-pre[antenna]
            A,b,vertices,primal_tolerance=polygon_vertices(pre,antenna,lower,upper)
            if mode=='mrt':
                gradient,curvature=mrt_expansion(pre,antenna,directions,beta,noise,job['power'],job['kappa'])
                increment=float(gradient@delta-curvature/2*(delta@delta));at_delta=gradient-curvature*delta
            else:
                base,gradient,curvature=zf_expansion(pre,antenna,directions,beta,noise,job['power'],job['kappa'])
                change=gradient@delta-curvature/2*(delta@delta);domain=base+change
                assert np.all(domain>0) and np.all(np.isfinite(domain))
                increment=float(np.sum(np.log1p(change/base))/np.log(2))
                at_delta=np.sum((gradient-curvature[:,None]*delta)/domain[:,None],axis=0)/np.log(2)
                vertex_domains=base[None,:]+vertices@gradient.T-np.sum(vertices*vertices,axis=1)[:,None]*curvature[None,:]/2
                negative_domain_vertices+=int(np.sum(np.any(vertex_domains<=0,axis=1)))
            assert np.all(np.isfinite(at_delta))
            gap=max(0.,float(np.max((vertices-delta)@at_delta)))
            primal=max(0.,float(np.max(A@delta-b)))
            certificate=record['certificate'];original_gap_tolerance=certificate['global_objective_gap_tolerance']
            error=abs(increment-certificate['minorant_increment'])
            max_gap_ratio=max(max_gap_ratio,gap/original_gap_tolerance)
            max_primal_ratio=max(max_primal_ratio,primal/primal_tolerance)
            max_increment_error=max(max_increment_error,error)
            assert gap<=original_gap_tolerance, (mode,i,gap,original_gap_tolerance)
            assert primal<=primal_tolerance and error<1e-9
        result[mode]={'coordinate_count':len(updates),'all_global_concave_tangent_gap_bounds_independently_recomputed':True,
            'all_spacing_box_polygon_vertices_enumerated':True,'maximum_gap_to_original_tolerance_ratio':max_gap_ratio,
            'maximum_primal_to_original_tolerance_ratio':max_primal_ratio,'maximum_minorant_increment_abs_error':max_increment_error,
            'original_minorant_atol':1e-9,'domain_invalid_vertices_not_evaluated_in_log_objective':negative_domain_vertices}
    return result


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--bank',required=True);parser.add_argument('--inputs-bank',required=True)
    parser.add_argument('--out',required=True);parser.add_argument('--public',required=True)
    args=parser.parse_args();bank=Path(args.bank).resolve();inputs=Path(args.inputs_bank).resolve()
    out,public=Path(args.out).resolve(),Path(args.public).resolve();assert not out.exists()
    cfgpath=inputs/'run_config.json';cfg=json.loads(cfgpath.read_bytes());jobs=sorted((inputs/'jobs').glob('case-*-mc-*.json'))
    assert len(jobs)==200
    files=[Path(__file__),Path(__file__).with_name('audit_full200_matlab_v1.py'),cfgpath]+jobs+[bank/(p.stem+'-matlab.json')for p in jobs]
    def key(p):
        if p.is_relative_to(bank):return 'raw/'+str(p.relative_to(bank))
        if p.is_relative_to(inputs):return 'inputs/'+str(p.relative_to(inputs))
        return p.name
    frozen={key(p):sha(p)for p in files}
    atomic(out.with_name(out.stem+'-freeze.json'),{'scope':'before_full200_actual_independent_coordinate_certificates',
        'sources_inputs_raw_sha256':frozen,'no_numerical_production_imports':True,'all200_pass_not_yet_claimed':True})
    records=[];failures=[];started=time.perf_counter()
    for index,path in enumerate(jobs):
        try:
            rawpath=bank/(path.stem+'-matlab.json');raw,job=json.loads(rawpath.read_bytes()),json.loads(path.read_bytes())
            expected=__import__('hashlib').sha256(b'strict-v1\0'+cfgpath.read_bytes()+b'\0'+path.read_bytes()).hexdigest()
            assert raw['input_fingerprint']==expected and raw['implementation_fingerprint']=='e78708e52bbfe9733a9fe24faaa736188015469a9d87ea90b41c5a1d0966bf37'
            checks=check_case(raw,job,cfg);records.append({'case':path.stem,'all_independent_coordinate_certificates_passed':True,'checks':checks})
        except Exception as exc:
            failures.append({'case':path.stem,'type':type(exc).__name__,'message':str(exc),'stack':traceback.format_exc()})
        report={'scope':'independent_all200_original_concave_coordinate_global_gap_certificates_not_new_optimizer',
            'expected_cases':200,'attempted':index+1,'passed':len(records),'failed':len(failures),
            'all200_independent_coordinate_certificates_passed':index+1==200 and not failures,
            'original_thresholds_and_all_N6_M5_positions_retained':True,'no_live_source_edits_or_subproblem_solver_imports':True,
            'no_Python_full200_or300_or_historical_graph_recovery_claim':True,'records':records,'failures':failures,
            'elapsed_seconds':time.perf_counter()-started,'freeze_sha256':sha(out.with_name(out.stem+'-freeze.json'))}
        atomic(out,report);print(json.dumps({k:report[k]for k in ['attempted','passed','failed','elapsed_seconds']}),flush=True)
    assert frozen=={key(p):sha(p)for p in files};report['source_input_raw_unchanged_at_end']=True
    atomic(public,report)
    assert report['all200_independent_coordinate_certificates_passed'], 'Keep every real failure; do not relax tolerance.'


if __name__=='__main__':main()
