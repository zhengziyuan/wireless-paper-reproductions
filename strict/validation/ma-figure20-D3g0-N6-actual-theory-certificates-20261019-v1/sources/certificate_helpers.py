"""One saved D4/g0 certificate: no original bound/objective/search/MC call.

All C(16,4) sets are evaluated by the previously verified independent
determinant/cofactor kernel. Every recorded pruning upper is independently
reconstructed, hashed, compared with all covered exact values, and checked
against an independently reconstructed lexicographic incumbent.
"""
from fractions import Fraction as F
import argparse
import gzip
import hashlib
import importlib.util
import itertools
import json
import math
from pathlib import Path
import pickle
import struct
import sys
import traceback


def enc(v):
    return json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False).encode()


def sha(b):
    return hashlib.sha256(b).hexdigest()


def require(v,message):
    if not v:raise ValueError(message)


def rational_hash(v):
    return sha(enc([str(v.numerator),str(v.denominator)]))


def model_identity(groups,mode):
    d=dict(schema='actual-exact-model-typed-operands-v1',mode=mode,N=4,M=3,D=4,
           groups={key:dict(type=type(value).__name__,typed_SHA256=sha(pickle.dumps(value,protocol=5))) for key,value in groups.items()},
           typed_serialization='local trusted Python pickle5 digest; no unpickle input')
    return dict(d,SHA256=sha(enc(d)))


def independent_primitives(job,mode,np,kernel):
    """Deterministic binary64 primitive recipe; no original function is called.

    Complete typed groups must equal the historical actual_frozen_model before
    any independent value or bound check is accepted.
    """
    geom=job['geometry'];theta=np.asarray(geom['elevation']);phi=np.asarray(geom['azimuth'])
    c=dict(beta=(1e-4*np.asarray(geom['distances_m'])**-2.8).tolist(),
           directions=np.c_[np.cos(theta)*np.sin(phi),np.sin(theta)].tolist(),
           rician=[job['kappa']]*3,noise=[1e-11]*3,power=job['power'],minimum_distance=.5,wavelength=1.)
    grid=np.array([[x,y] for x in np.linspace(job['region_lower'][0],job['region_upper'][0],4)
                   for y in np.linspace(job['region_lower'][1],job['region_upper'][1],4)])
    q=kernel.q;points=[tuple(map(q,p)) for p in grid]
    compatible=[[sum((points[i][axis]-points[j][axis])**2 for axis in range(2))>=q(.5)**2
                 for j in range(16)] for i in range(16)]
    terms={};diagonal=None
    groups=dict(grid=grid,compatible=compatible,terms=terms,diagonal=diagonal)
    constants=kernel.rebuild_rational_constants(c,4,3,mode)
    if mode=='MRT':
        directions=np.asarray(c['directions']);wave=2*np.pi/c['wavelength']
        for u in range(3):
            for v in range(3):
                if u!=v:
                    phasors=np.exp(1j*wave*(grid@(directions[u]-directions[v])))
                    terms[u,v]=[(q(z.real),q(z.imag)) for z in phasors]
        groups.update(base=constants['offset'],numerator=constants['desired'],coefficient=constants['coefficient'])
    else:
        h=np.exp(2j*np.pi/c['wavelength']*(grid@np.asarray(c['directions']).T))
        scale=[q(x) for x in np.sqrt(np.asarray(c['rician'])/(np.asarray(c['rician'])+1))]
        weighted=[[(q(z.real)*scale[u],q(z.imag)*scale[u]) for u,z in enumerate(row)] for row in h]
        diagonal=[[kernel.znorm(row[u])/4 for u in range(3)] for row in weighted]
        for u,v in itertools.combinations(range(3),2):
            z=[kernel.zmul(kernel.zconj(row[u]),row[v]) for row in weighted]
            terms[u,v]=[(x[0]/4,x[1]/4) for x in z]
        groups.update(diagonal=diagonal,base=constants['offset'],eta=constants['eta'])
    return dict(constants,grid=grid,spacing=q(.5),terms=terms,diagonal=diagonal,m=3,n=4),groups,compatible


def read_certificate(raw,checkpoint):
    pos=0;chain='0'*64;witnesses=[];chunks=[]
    while pos<len(raw):
        require(pos+40<=len(raw),'Partial frame header')
        length=struct.unpack('>Q',raw[pos:pos+8])[0]
        require(length<=4*1024*1024 and pos+40+length<=len(raw),'Partial/oversized frame')
        frame=raw[pos:pos+40+length];body=frame[40:]
        require(hashlib.sha256(body).digest()==frame[8:40],'Frame payload digest mismatch')
        decoded=gzip.decompress(body);require(len(decoded)<=8*1024*1024,'Oversized witness chunk')
        chunk=json.loads(decoded)
        require(chunk['schema']=='exact-prune-prefix-witness-chunk-v1' and chunk['previous_chain']==chain,'Witness chain mismatch')
        seq=chunk['batch_sequence'];require(isinstance(seq,int) and (not chunks or seq>chunks[-1]),'Nonincreasing batch sequence')
        require(seq<checkpoint['batch_sequence'],'Uncommitted witness batch')
        chain=sha(bytes.fromhex(chain)+frame);chunks.append(seq);witnesses.extend(chunk['witnesses']);pos+=len(frame)
    require(pos==checkpoint['certificate_bytes']==len(raw),'Certificate byte count mismatch')
    require(len(chunks)==checkpoint['certificate_chunks'] and chain==checkpoint['certificate_chain'],'Final chain mismatch')
    require(len(witnesses)==checkpoint['prunes'],'Not every recorded prune has a witness')
    return witnesses,dict(frame_count=len(chunks),frame_batch_sequences=chunks,frame_payload_digests_and_chain_pass=True,
                           certificate_bytes=len(raw),final_chain=chain)


DIRECTIONS=((1,0),(1,1),(0,1),(-1,1),(-1,0),(-1,-1),(0,-1),(1,-1))


def ceil_sqrt_dyadic(value):
    """Exact smallest 2^-64 multiple no smaller than sqrt(value)."""
    require(value>=0,'Negative squared norm')
    numerator=value.numerator*(1<<128);denominator=value.denominator
    root=math.isqrt(numerator//denominator)
    if root*root*denominator<numerator:root+=1
    result=F(root,1<<64);require(result*result>=value,'Square-root ceiling failed')
    return result


def projection_lower(terms,prefix,remaining,r):
    s=(sum(terms[i][0] for i in prefix),sum(terms[i][1] for i in prefix))
    values=[]
    for x,y in DIRECTIONS:
        lower=x*s[0]+y*s[1]+sum(sorted(x*terms[i][0]+y*terms[i][1] for i in remaining)[:r])
        values.append(max(F(0),lower)**2/(x*x+y*y))
    return max(values)


def independent_norm_upper(terms,prefix,remaining,r,kernel):
    fixed=kernel.zsum(terms[i] for i in prefix)
    rectangle=F(0)
    for axis in range(2):
        values=sorted(terms[i][axis] for i in remaining)
        low=fixed[axis]+sum(values[:r]);high=fixed[axis]+sum(values[-r:])
        rectangle+=max(low*low,high*high)
    rectangle=ceil_sqrt_dyadic(rectangle)
    triangle=ceil_sqrt_dyadic(kernel.znorm(fixed))+sum(sorted((ceil_sqrt_dyadic(kernel.znorm(terms[i])) for i in remaining),reverse=True)[:r])
    return min(rectangle,triangle)


def independent_previous_upper(o,prefix,remaining,mode,kernel):
    r=4-len(prefix)
    lower={pair:projection_lower(terms,prefix,remaining,r) for pair,terms in o['terms'].items()}
    result=F(1)
    if mode=='MRT':
        for u in range(3):
            denominator=o['offset'][u]+sum(o['coefficient'][u,v]*lower[u,v] for v in range(3) if v!=u)
            result*=1+o['desired'][u]/denominator
    else:
        diag=[o['offset'][u]+sum(o['diagonal'][i][u] for i in prefix)+
              sum(sorted((o['diagonal'][i][u] for i in remaining),reverse=True)[:r]) for u in range(3)]
        norms={pair:independent_norm_upper(terms,prefix,remaining,r,kernel) for pair,terms in o['terms'].items()}
        for u in range(3):
            v,w=[x for x in range(3) if x!=u]
            eigen_upper=min(diag[v]+diag[w],max(diag[v],diag[w])+norms[min(v,w),max(v,w)])
            schur=max(F(0),diag[u]-(lower[min(u,v),max(u,v)]+lower[min(u,w),max(u,w)])/eigen_upper)
            result*=1+o['eta'][u]*schur
    return result


def upward_128(value):
    scale=1<<128
    return F(-((-value.numerator*scale)//value.denominator),scale)


def independent_exp_ceiling(value):
    """Separate power/factorial expansion of the declared degree-40 ceiling.

    At t<=1/2, tail terms after 41 have ratio at most t/42. Upward argument,
    Taylor remainder and repeated-squaring roundings preserve an upper bound.
    No original exp routine, floating exp, or MP estimate is used.
    """
    require(value>=0,'Negative tangent increment')
    if value==0:return F(1)
    count=0
    while value>F(1,2):value/=2;count+=1
    t=upward_128(value);require(t<=F(1,2),'Invalid scaled exponential interval')
    polynomial=sum((t**j/F(math.factorial(j)) for j in range(41)),F(0))
    tail=t**41/F(math.factorial(41))/(1-t/42)
    upper=upward_128(polynomial+tail)
    for _ in range(count):upper=upward_128(upper**2)
    return upper


def matrix_for_weights(o,prefix,remaining,weights,kernel):
    matrix=[[kernel.Z0 for _ in range(3)] for _ in range(3)]
    for u in range(3):
        matrix[u][u]=(o['offset'][u]+sum(o['diagonal'][i][u] for i in prefix)+
                       sum(w*o['diagonal'][i][u] for w,i in zip(weights,remaining)),F(0))
    for u,v in itertools.combinations(range(3),2):
        values=[o['terms'][u,v][i] for i in prefix]
        values.extend((w*o['terms'][u,v][i][0],w*o['terms'][u,v][i][1]) for w,i in zip(weights,remaining))
        matrix[u][v]=kernel.zsum(values);matrix[v][u]=kernel.zconj(matrix[u][v])
    return matrix


def independent_tangent_upper(o,prefix,remaining,counts,kernel):
    r=4-len(prefix);Q=1<<32
    require(len(counts)==len(remaining) and all(type(x) is int and 0<=x<=Q for x in counts)
            and sum(counts)==r*Q,'Invalid saved dyadic hypersimplex point')
    weights=[F(x,Q) for x in counts]
    matrix=matrix_for_weights(o,prefix,remaining,weights,kernel)
    det=kernel.real_positive_det(matrix)
    # All inverse entries use independent determinant cofactors, not the
    # original integer adjugate/elimination or any numerical inverse.
    inverse=[]
    for i in range(3):
        row=[]
        for j in range(3):
            cross=[[matrix[a][b] for b in range(3) if b!=i] for a in range(3) if a!=j]
            z=kernel.determinant(cross);sign=(-1)**(i+j)
            row.append((sign*z[0]/det,sign*z[1]/det))
        inverse.append(row)
    schur=[];point_product=F(1)
    for u in range(3):
        require(inverse[u][u][1]==0 and inverse[u][u][0]>0,'Nonpositive inverse diagonal')
        schur.append(1/inverse[u][u][0]);point_product*=1+o['eta'][u]*schur[-1]
    coefficient=[o['eta'][u]*schur[u]**2/(1+o['eta'][u]*schur[u]) for u in range(3)]
    gradient=[]
    for u in range(3):
        row=[]
        for v in range(3):
            values=[kernel.zmul(inverse[u][j],inverse[j][v]) for j in range(3)]
            row.append((sum(coefficient[j]*values[j][0] for j in range(3)),
                        sum(coefficient[j]*values[j][1] for j in range(3))))
        gradient.append(row)
    scores=[]
    for i in remaining:
        score=sum(gradient[u][u][0]*o['diagonal'][i][u] for u in range(3))
        for u,v in itertools.combinations(range(3),2):
            score+=2*kernel.zmul(gradient[u][v],kernel.zconj(o['terms'][u,v][i]))[0]
        scores.append(score)
    increment=sum(sorted(scores,reverse=True)[:r])-sum(w*s for w,s in zip(weights,scores))
    require(increment>=0,'Negative exact linear relaxation increment')
    return point_product*independent_exp_ceiling(increment)


def audit_mode(o,compatible,mode,binding,checkpoint,raw_certificate,kernel):
    witnesses,framing=read_certificate(raw_certificate,checkpoint)
    cuts={}
    for w in witnesses:
        p=tuple(w['prefix'])
        require(0<len(p)<4 and tuple(sorted(set(p)))==p and 0<=p[0]<=p[-1]<16,'Invalid prune prefix')
        require(p not in cuts,'Duplicate pruning prefix')
        require(all(compatible[i][j] for i,j in itertools.combinations(p,2)),'Infeasible recorded prune prefix')
        cuts[p]=w
    require(all(not any(p[:k] in cuts for k in range(1,len(p))) for p in cuts),'Nested pruning witnesses overlap')
    objective={};owners={};winner=None;best=None;ties=[];all_chain=hashlib.sha256()
    for whole in itertools.combinations(range(16),4):
        feasible=all(compatible[i][j] for i,j in itertools.combinations(whole,2))
        row=dict(indices=whole,feasible=feasible)
        if feasible:
            value=kernel.independent_product(o,whole,mode);objective[whole]=value
            matches=[whole[:k] for k in range(1,4) if whole[:k] in cuts]
            require(len(matches)<=1,'A feasible set is covered by multiple prune prefixes')
            owners[whole]=matches[0] if matches else None
            row['product']=kernel.rational_record(value)
            if best is None or value>best:best,winner,ties=value,whole,[whole]
            elif value==best:ties.append(whole)
        all_chain.update(enc(row)+b'\n')
    require(len(objective)>0,'No feasible set')
    uncut=[whole for whole in objective if owners[whole] is None]
    require(len(uncut)==checkpoint['leaves'],'Unpruned feasible complement differs from stored leaf count')
    remaining_for=lambda p:tuple(i for i in range(p[-1]+1 if p else 0,16) if all(compatible[j][i] for j in p))
    uppers={};prune_checks=[]
    for p,w in cuts.items():
        remaining=remaining_for(p);r=4-len(p)
        require(len(remaining)>=r,'Recorded prune is an impossible prefix')
        upper=independent_previous_upper(o,p,remaining,mode,kernel)
        if w['supporting_dyadic_counts'] is not None:
            require(mode=='ZF' and r>=2,'Unexpected tangent witness')
            tangent=independent_tangent_upper(o,p,remaining,w['supporting_dyadic_counts'],kernel)
            upper=min(upper,tangent)
        require(rational_hash(upper)==w['exact_upper_SHA256'],'Independent bound rational digest mismatch at '+str(p))
        covered=[value for whole,value in objective.items() if owners[whole]==p]
        require(covered,'Prune has no feasible completion')
        maximum=max(covered);require(maximum<=upper,'Unsafe prune upper at '+str(p))
        uppers[p]=upper
        prune_checks.append(dict(prefix=list(p),covered_feasible_sets=len(covered),exact_upper_SHA256=rational_hash(upper),
                                 exact_maximum_covered_product_SHA256=rational_hash(maximum),
                                 exact_upper_covers_all_completions=True,has_saved_tangent_point=w['supporting_dyadic_counts'] is not None))
    # Independent prefix-set construction, not original DFS. A prefix is visited
    # iff all its proper prefixes are feasible, completion-possible, and uncut.
    events=[]
    for length in range(5):
        for p in itertools.combinations(range(16),length):
            if not all(compatible[i][j] for i,j in itertools.combinations(p,2)):continue
            blocked=False
            for k in range(len(p)):
                ancestor=p[:k]
                if ancestor in cuts or len(remaining_for(ancestor))<4-k:blocked=True;break
            if not blocked:events.append(p)
    events.sort()
    counts=dict(nodes=0,leaves=0,infeasible=0,prunes=0,branches=0);incumbent=None;chosen=None
    for p in events:
        counts['nodes']+=1;r=4-len(p);remaining=remaining_for(p)
        if len(remaining)<r:counts['infeasible']+=1
        elif r==0:
            counts['leaves']+=1;value=objective[p]
            if incumbent is None or value>incumbent:incumbent,chosen=value,p
        elif p in cuts:
            counts['prunes']+=1
            require(incumbent is not None and uppers[p]<=incumbent,'Pruning bound exceeds independently reconstructed incumbent')
        else:counts['branches']+=1
    require(all(counts[k]==checkpoint[k] for k in ['nodes','leaves','infeasible','prunes']),'Independent prefix partition counters differ')
    require(counts['nodes']==checkpoint['sequence'],'Decision count differs')
    stored=F(int(checkpoint['best'][0]),int(checkpoint['best'][1]))
    require(best==stored==incumbent and list(winner)==checkpoint['winner']==list(chosen),'Saved winner/product is not independent global maximum')
    return dict(mode=mode,all_combinations=math.comb(16,4),feasible_combinations=len(objective),
                pruned_feasible_combinations=len(objective)-len(uncut),independently_evaluated_unpruned_leaves=len(uncut),
                independent_prefix_counts=counts,certificate_framing=framing,
                all_prune_prefixes=list(prune_checks),prune_count=len(cuts),
                saved_tangent_witnesses=sum(w['supporting_dyadic_counts'] is not None for w in witnesses),
                exact_bound_hash_matches=len(cuts),all_prunes_cover_all_exact_descendants=True,
                all_prunes_below_reconstructed_lexicographic_incumbent=True,
                all_feasible_sets_covered_once_by_cut_or_exact_leaf=True,
                unique_lexicographic_global_winner_zero_based=list(winner),number_of_global_ties=len(ties),
                exact_global_product=kernel.rational_record(best),all_exact_values_SHA256=all_chain.hexdigest(),
                typed_model_identity=binding['actual_frozen_model'],scoped_independent_pruning_and_global_grid_pass=True)


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--plan',type=Path,required=True);parser.add_argument('--output-dir',type=Path,required=True);args=parser.parse_args()
    require(not args.output_dir.exists(),'Fresh output required');args.output_dir.mkdir(parents=True)
    report=dict(schema='actual-one-Python-D4g0-independent-exact-pruning-and-global-grid-v1',rows=[],errors=[],
                original_bound_objective_search_optimizer_MC_calls=0,native_certificate_gate=False,
                full2600_gate=False,original_reference_gate=False,historical_author_target_recovered=False)
    expected={};before={};code=1
    try:
        plan_raw=args.plan.read_bytes();plan=json.loads(plan_raw);expected=dict(plan['source_and_input_pins']);expected[str(args.plan)]=sha(plan_raw)
        for path,ident in expected.items():before[path]=sha(Path(path).read_bytes());require(before[path]==ident,'Pin mismatch '+path)
        spec=importlib.util.spec_from_file_location('independent_complete_grid_kernel',plan['independent_kernel']);kernel=importlib.util.module_from_spec(spec);spec.loader.exec_module(kernel)
        sys.path.insert(0,plan['site_packages']);import numpy as np
        job=json.loads(Path(plan['job']).read_bytes())
        require((job['N'],job['M'],job['brute_force_D'],job['realization'])==(4,3,4,0),'Wrong case')
        closed=json.loads(Path(plan['closed_result']).read_bytes())
        require(closed['failure'] is None and closed['checks']['all_two_statistical_grids_closed'] is True and closed['checks']['sources_unchanged'] is True,'Original case closure absent')
        for mode in ['MRT','ZF']:
            paths=plan['modes'][mode];binding=json.loads(Path(paths['binding']).read_bytes());checkpoint=json.loads(Path(paths['checkpoint']).read_bytes())
            require(checkpoint['complete'] is True and checkpoint['stack']==[],'Incomplete original grid')
            require(binding['original_job_SHA256']==before[plan['job']] and binding['execution_configuration_SHA256']==before[plan['configuration']],'Original job/configuration binding mismatch')
            operands,groups,compatible=independent_primitives(job,mode,np,kernel)
            require(model_identity(groups,mode)==binding['actual_frozen_model'],'Actual typed model mismatch')
            report['rows'].append(audit_mode(operands,compatible,mode,binding,checkpoint,Path(paths['certificate']).read_bytes(),kernel))
        report['all_two_modes_independent_pruning_and_complete1820_grid_checks_pass']=len(report['rows'])==2
        code=0
    except Exception as exc:
        report['errors'].append(dict(type=type(exc).__name__,message=str(exc),traceback=traceback.format_exc()));report['all_two_modes_independent_pruning_and_complete1820_grid_checks_pass']=False;code=1
    finally:
        after={}
        for path in expected:
            try:after[path]=sha(Path(path).read_bytes())
            except OSError as exc:report['errors'].append(dict(type=type(exc).__name__,message=str(exc),path=path))
        report['source_input_before']=before;report['source_input_after']=after;report['source_input_interval_closed']=bool(expected) and before==after==expected
        if not report['source_input_interval_closed']:code=1
        report['actual_reader_exit_code']=code
        report['limitations']=[
            'Only Python Figure19 N4/M3/D4/g0; own frozen binary64 primitive model, not original symbolic trigonometric values.',
            'Source-bound framing/chain and prune witnesses verified; original branch upper values/tangent points and full leaf/event transcript are not saved, so the original complete decision_digest is not recomputed.',
            'Incumbent reconstructed from the independent lexicographic leaf complement, not recovered from a stored per-prune incumbent.',
            'No native per-prune witness data was imported: native rolling hashes alone cannot inherit this pruning gate.',
            'Not a proof for all2600, the historical author search target, trajectory/MC protocol, original-reference agreement or full-paper reproduction.']
        (args.output_dir/'ACTUAL_PYTHON_D4G0_ALL1820_AND_ALL425_PRUNES_INDEPENDENT_EXACT_CLOSURE_V1.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    print(json.dumps(dict(actual_exit_code=code,completed_modes=len(report['rows']),all_pass=report.get('all_two_modes_independent_pruning_and_complete1820_grid_checks_pass',False),source_input_closed=report['source_input_interval_closed'])))
    return code


if __name__=='__main__':raise SystemExit(main())
