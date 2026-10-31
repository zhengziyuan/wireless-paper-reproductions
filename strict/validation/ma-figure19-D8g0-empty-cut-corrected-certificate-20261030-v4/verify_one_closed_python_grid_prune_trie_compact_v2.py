"""Independent closed-point pruning/coverage proof without cut-objective replay.

N4/M3 only, with the point's actual D and typed operand binding.  Objective
values are evaluated only at the unpruned leaf complement.  Cut cardinalities
use exact compatibility-graph edge/triangle counts, not complete-set evaluation.
No original model, bound, objective, DFS, chooser, optimizer, MC or RNG call.
"""
from fractions import Fraction as F
import argparse
from functools import lru_cache
import hashlib
import importlib.util
import itertools
import json
import math
from pathlib import Path
import pickle
import sys
import traceback


def enc(v):return json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
def sha(b):return hashlib.sha256(b).hexdigest()
def need(v,message):
    if not v:raise ValueError(message)


def load_module(path,name):
    spec=importlib.util.spec_from_file_location(name,path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module


def typed_identity(groups,mode,D):
    v=dict(schema='actual-exact-model-typed-operands-v1',mode=mode,N=4,M=3,D=D,
           groups={key:dict(type=type(value).__name__,typed_SHA256=sha(pickle.dumps(value,protocol=5))) for key,value in groups.items()},
           typed_serialization='local trusted Python pickle5 digest; no unpickle input')
    return dict(v,SHA256=sha(enc(v)))


def reconstruct_own_operands(job,mode,np,k):
    need(job['N']==4 and job['M']==3,'This audited campaign adapter supports only N4/M3')
    D=job['brute_force_D'];need(type(D) is int and 2<=D<=64,'Invalid D')
    g=job['geometry'];theta=np.asarray(g['elevation']);phi=np.asarray(g['azimuth'])
    c=dict(beta=(1e-4*np.asarray(g['distances_m'])**-2.8).tolist(),
           directions=np.c_[np.cos(theta)*np.sin(phi),np.sin(theta)].tolist(),
           rician=[job['kappa']]*3,noise=[1e-11]*3,power=job['power'],minimum_distance=.5,wavelength=1.)
    grid=np.array([[x,y] for x in np.linspace(job['region_lower'][0],job['region_upper'][0],D)
                   for y in np.linspace(job['region_lower'][1],job['region_upper'][1],D)])
    points=[tuple(map(k.q,row)) for row in grid];P=len(points)
    compatible=[[sum((points[i][d]-points[j][d])**2 for d in range(2))>=k.q(.5)**2
                 for j in range(P)] for i in range(P)]
    groups=dict(grid=grid,compatible=compatible,terms={},diagonal=None)
    terms=groups['terms'];diagonal=None;constants=k.rebuild_rational_constants(c,4,3,mode)
    if mode=='MRT':
        wave=2*np.pi/c['wavelength'];directions=np.asarray(c['directions'])
        for u in range(3):
            for v in range(3):
                if u!=v:
                    phasor=np.exp(1j*wave*(grid@(directions[u]-directions[v])))
                    terms[u,v]=[(k.q(z.real),k.q(z.imag)) for z in phasor]
        groups.update(base=constants['offset'],numerator=constants['desired'],coefficient=constants['coefficient'])
    else:
        h=np.exp(2j*np.pi/c['wavelength']*(grid@np.asarray(c['directions']).T))
        scale=[k.q(x) for x in np.sqrt(np.asarray(c['rician'])/(np.asarray(c['rician'])+1))]
        weighted=[[(k.q(z.real)*scale[u],k.q(z.imag)*scale[u]) for u,z in enumerate(row)] for row in h]
        diagonal=[[k.znorm(row[u])/4 for u in range(3)] for row in weighted]
        for u,v in itertools.combinations(range(3),2):
            z=[k.zmul(k.zconj(row[u]),row[v]) for row in weighted]
            terms[u,v]=[(x[0]/4,x[1]/4) for x in z]
        groups.update(diagonal=diagonal,base=constants['offset'],eta=constants['eta'])
    return dict(constants,grid=grid,spacing=k.q(.5),terms=terms,diagonal=diagonal,m=3,n=4),groups,compatible


class CompatibilityCounter:
    """Exact cardinalities of canonical cliques, with bit-count base cases.

    Four-clique counting sums triangle counts after choosing the smallest
    vertex. Triangle counting sums edge counts after its smallest vertex.
    Edge counting sums compatible higher vertices. No four-set is materialized
    or evaluated by this cardinality computation.
    """
    def __init__(self,compatible):
        self.P=len(compatible);self.adj=[]
        for i,row in enumerate(compatible):
            need(len(row)==self.P and not row[i],'Compatibility diagonal must exclude repeats')
            self.adj.append(sum((1<<j) for j,v in enumerate(row) if v))
        need(all(compatible[i][j]==compatible[j][i] for i in range(self.P) for j in range(self.P)),'Compatibility is not symmetric')
        self.all=(1<<self.P)-1

    @lru_cache(maxsize=8192)
    def edges(self,mask):
        count=0
        while mask:
            bit=mask&-mask;mask^=bit;i=bit.bit_length()-1
            count+=(mask&self.adj[i]).bit_count()
        return count

    @lru_cache(maxsize=8192)
    def triangles(self,mask):
        count=0
        while mask:
            bit=mask&-mask;mask^=bit;i=bit.bit_length()-1
            count+=self.edges(mask&self.adj[i])
        return count

    def count(self,mask,r):
        size=mask.bit_count()
        if size<r:return 0
        if r==0:return 1
        if r==1:return size
        if r==2:return self.edges(mask)
        # An exact complete-graph shortcut needs only the edge count.
        if self.edges(mask)==math.comb(size,2):return math.comb(size,r)
        if r==3:return self.triangles(mask)
        need(r==4,'N4 scope only')
        count=0
        while mask:
            bit=mask&-mask;mask^=bit;i=bit.bit_length()-1
            count+=self.triangles(mask&self.adj[i])
        return count

    @staticmethod
    def indices(mask):
        values=[]
        while mask:
            bit=mask&-mask;mask^=bit;values.append(bit.bit_length()-1)
        return tuple(values)


def certify_partition(o,compatible,mode,checkpoint,certificate,k,b):
    witnesses,framing=b.read_certificate(certificate,checkpoint)
    counter=CompatibilityCounter(compatible);P=counter.P
    cuts={}
    trie={}
    for w in witnesses:
        p=tuple(w['prefix']);need(0<len(p)<4 and p==tuple(sorted(set(p))) and 0<=p[0]<=p[-1]<P,'Invalid cut prefix')
        need(p not in cuts,'Duplicate cut');need(all(compatible[i][j] for i,j in itertools.combinations(p,2)),'Infeasible cut')
        cursor=trie
        for point in p:
            need('_cut' not in cursor,'Nested cut prefix');cursor=cursor.setdefault(point,{})
        need(not cursor,'Cut contains another cut');cursor['_cut']=True;cuts[p]=w
    counts=dict(nodes=0,leaves=0,infeasible=0,prunes=0,branches=0)
    seen=set();cut_rows=[];tangents=[];leaf_chain=hashlib.sha256();cut_chain=hashlib.sha256()
    incumbent=None;winner=None;leaf_ties=0;cut_uppers=[]

    def visit(prefix,remaining_mask,trie_cursor):
        nonlocal incumbent,winner,leaf_ties
        counts['nodes']+=1;r=4-len(prefix)
        if remaining_mask.bit_count()<r:
            counts['infeasible']+=1;need(not trie_cursor,'Certificate contains an unreachable child');return 0
        if r==0:
            need(not trie_cursor,'Cut below a complete leaf');counts['leaves']+=1
            value=k.independent_product(o,prefix,mode)
            leaf_chain.update(enc(dict(prefix=prefix,product=k.rational_record(value)))+b'\n')
            if incumbent is None or value>incumbent:incumbent,winner,leaf_ties=value,prefix,1
            elif value==incumbent:leaf_ties+=1
            return 1
        if '_cut' in trie_cursor:
            need(set(trie_cursor)=={'_cut'} and prefix in cuts,'Malformed terminal trie node')
            w=cuts[prefix];seen.add(prefix);counts['prunes']+=1
            remaining=counter.indices(remaining_mask)
            upper=b.independent_previous_upper(o,prefix,remaining,mode,k)
            tangent_counts=w['supporting_dyadic_counts']
            if tangent_counts is not None:
                need(mode=='ZF' and r>=2,'Unexpected tangent witness')
                tangent=b.independent_tangent_upper(o,prefix,remaining,tangent_counts,k)
                upper=min(upper,tangent)
                tangents.append(dict(prefix=list(prefix),remaining_zero_based=list(remaining),
                                     saved_actual_dyadic_counts=list(tangent_counts),denominator=1<<32,
                                     independently_recomputed_tangent_upper_SHA256=b.rational_hash(tangent),
                                     selected_upper_SHA256=b.rational_hash(upper)))
            need(b.rational_hash(upper)==w['exact_upper_SHA256'],'Upper rational digest differs at '+str(prefix))
            need(incumbent is not None and upper<=incumbent,'Upper exceeds earlier independent leaf incumbent')
            amount=counter.count(remaining_mask,r);need(amount>0,'Empty feasible cut')
            row=dict(prefix=list(prefix),covered_feasible_sets=amount,
                     exact_upper_SHA256=b.rational_hash(upper),
                     incumbent_product_SHA256=b.rational_hash(incumbent),
                     upper_le_incumbent=True,actual_tangent_saved=tangent_counts is not None)
            cut_rows.append(row);cut_chain.update(enc(row)+b'\n');cut_uppers.append(upper)
            return amount
        counts['branches']+=1;total=0;remaining=remaining_mask
        # Choosing the smallest next vertex partitions all canonical completions.
        # The cut trie never makes a new pruning decision: only supplied cuts stop.
        while remaining:
            bit=remaining&-remaining;remaining^=bit;point=bit.bit_length()-1
            child=remaining&counter.adj[point]
            total+=visit(prefix+(point,),child,trie_cursor.get(point,{}))
        need(all(isinstance(key,int) for key in trie_cursor),'Nonterminal cut marker')
        return total

    covered=visit((),counter.all,trie)
    graph_count=counter.count(counter.all,4)
    need(covered==graph_count and seen==set(cuts),'Coverage count or consumed cut list differs')
    need(all(counts[key]==checkpoint[key] for key in ['nodes','leaves','infeasible','prunes']),'Checkpoint traversal counters differ')
    need(counts['nodes']==checkpoint['sequence'],'Decision count differs')
    stored=F(int(checkpoint['best'][0]),int(checkpoint['best'][1]))
    need(incumbent==stored and list(winner)==checkpoint['winner'],'Saved exact winner/product differs')
    # If every cut is strictly below final best, no hidden tied optimum exists.
    strict_cuts=all(value<incumbent for value in cut_uppers)
    return dict(mode=mode,grid_points=P,complete_unordered_sets=math.comb(P,4),
                independently_counted_feasible_sets=graph_count,partition_covered_feasible_sets=covered,
                pruned_feasible_sets=sum(x['covered_feasible_sets'] for x in cut_rows),
                actual_independent_objective_evaluations=counts['leaves'],
                pruned_subtree_objective_evaluations=0,
                independent_prefix_counts=counts,certificate_framing=framing,
                verified_prune_count=len(cuts),verified_exact_upper_hashes=len(cuts),
                all_prune_uppers_le_prior_independent_leaf_incumbent=True,
                all_feasible_sets_partitioned_once=True,all_supplied_cuts_reached_once=True,
                actual_saved_tangent_witness_count=len(tangents),actual_saved_tangent_witnesses=tangents,
                verified_prune_rows=cut_rows,
                unpruned_exact_leaf_stream_SHA256=leaf_chain.hexdigest(),verified_cut_stream_SHA256=cut_chain.hexdigest(),
                exact_global_product=k.rational_record(incumbent),
                earliest_canonical_global_winner_zero_based=list(winner),
                all_cut_uppers_strictly_below_final_best=strict_cuts,
                observed_global_ties_in_unpruned_leaves=leaf_ties,
                unique_global_winner_independently_proven=(strict_cuts and leaf_ties==1),
                scoped_independent_partition_and_bound_gate_pass=True)


def compare_full_proof(rows,proof):
    need(proof['actual_reader_exit_code']==0 and proof['source_input_interval_closed'],'Prior full proof not closed')
    old={r['mode']:r for r in proof['rows']};out=[]
    for row in rows:
        previous=old[row['mode']]
        a={tuple(x['prefix']):x for x in row['verified_prune_rows']}
        z={tuple(x['prefix']):x for x in previous['all_prune_prefixes']}
        checks=dict(same_prune_prefix_set=set(a)==set(z),
                    every_analytic_cut_count_equals_full_enumeration=all(a[p]['covered_feasible_sets']==z[p]['covered_feasible_sets'] for p in a),
                    every_upper_digest_equals_full_proof=all(a[p]['exact_upper_SHA256']==z[p]['exact_upper_SHA256'] for p in a),
                    same_tangent_presence=all(a[p]['actual_tangent_saved']==z[p]['has_saved_tangent_point'] for p in a),
                    same_feasible_population=row['independently_counted_feasible_sets']==previous['feasible_combinations'],
                    same_unpruned_leaf_count=row['actual_independent_objective_evaluations']==previous['independently_evaluated_unpruned_leaves'],
                    same_prefix_counters=row['independent_prefix_counts']==previous['independent_prefix_counts'],
                    same_exact_global_product=row['exact_global_product']==previous['exact_global_product'],
                    same_earliest_winner=row['earliest_canonical_global_winner_zero_based']==previous['unique_lexicographic_global_winner_zero_based'])
        need(all(checks.values()),'Nonexhaustive route differs from closed full proof')
        out.append(dict(mode=row['mode'],checks=checks,comparison_pass=True))
    return out


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ['plan','case-dir','job','configuration','output-dir']:parser.add_argument('--'+name,type=Path,required=True)
    parser.add_argument('--compare-exhaustive-proof',type=Path)
    args=parser.parse_args();need(not args.output_dir.exists(),'Fresh output required');args.output_dir.mkdir(parents=True)
    report=dict(schema='actual-one-closed-Python-grid-independent-prune-trie-and-analytic-coverage-v1',rows=[],errors=[],
                native_gate=False,full2600_gate=False,original_reference_gate=False,
                historical_author_target_recovered=False,original_model_bound_objective_search_chooser_MC_calls=0)
    expected={};before={};code=1;failure_stage='source_input_identity_or_host'
    try:
        raw=args.plan.read_bytes();plan=json.loads(raw);expected=dict(plan['source_pins']);expected[str(args.plan)]=sha(raw)
        dynamic=[args.job,args.configuration,args.case_dir/'closed-result.json',args.case_dir/'binding.json']
        for mode in ['MRT','ZF']:
            dynamic.extend(args.case_dir/f'grid-{mode}'/name for name in ['binding.json','checkpoint.json','pruned-prefix-certificates.frames'])
        if args.compare_exhaustive_proof:dynamic.append(args.compare_exhaustive_proof)
        for p in dynamic:expected[str(p)]=sha(p.read_bytes())
        for path,want in expected.items():before[path]=sha(Path(path).read_bytes());need(before[path]==want,'Source/input pin mismatch')
        b=load_module(plan['independent_bound_source'],'independent_saved_bounds');k=load_module(plan['independent_kernel'],'independent_exact_values')
        sys.path.insert(0,plan['site_packages']);import numpy as np
        job=json.loads(args.job.read_bytes());report['point']={key:job[key] for key in ['figure','point','realization','N','M','brute_force_D']}
        closed=json.loads((args.case_dir/'closed-result.json').read_bytes());casebinding=json.loads((args.case_dir/'binding.json').read_bytes())
        need(closed['failure'] is None and closed['checks']['all_two_statistical_grids_closed'] is True and closed['checks']['sources_unchanged'] is True,'Original point not closed')
        for mode in ['MRT','ZF']:
            folder=args.case_dir/f'grid-{mode}';binding=json.loads((folder/'binding.json').read_bytes());checkpoint=json.loads((folder/'checkpoint.json').read_bytes())
            need(checkpoint['complete'] is True and checkpoint['stack']==[],'Grid not closed')
            need(binding['mode']==mode and binding['original_job_SHA256']==before[str(args.job)] and binding['execution_configuration_SHA256']==before[str(args.configuration)],'Point input binding differs')
            need(all(binding[key]==casebinding[key] for key in ['original_job_SHA256','original_input_fingerprint','execution_configuration_SHA256','original_manifest_SHA256']),'Case and model identities differ')
            o,groups,compatible=reconstruct_own_operands(job,mode,np,k)
            ident=typed_identity(groups,mode,job['brute_force_D']);need(ident==binding['actual_frozen_model'],'Historical typed operands differ')
            certificate_bytes=(folder/'pruned-prefix-certificates.frames').read_bytes()
            failure_stage='independent_saved_certificate_gate'
            row=certify_partition(o,compatible,mode,checkpoint,certificate_bytes,k,b)
            failure_stage='source_input_identity_or_host'
            row['actual_typed_model_identity']=ident;report['rows'].append(row)
        report['all_two_modes_partition_bound_and_global_grid_gate_pass']=len(report['rows'])==2
        report['comparison_with_prior_complete_set_enumeration']=None
        if args.compare_exhaustive_proof:
            report['comparison_with_prior_complete_set_enumeration']=compare_full_proof(report['rows'],json.loads(args.compare_exhaustive_proof.read_bytes()))
            report['prior_exhaustive_proof_SHA256']=before[str(args.compare_exhaustive_proof)]
        # Storage-only projection: the complete checked table is committed by
        # verified_cut_stream_SHA256; actual tangent vectors are retained.
        for row in report['rows']:
            row['verified_prune_rows_count']=len(row.pop('verified_prune_rows'))
        code=0
    except Exception as exc:
        report['errors'].append(dict(type=type(exc).__name__,message=str(exc),traceback=traceback.format_exc(),failure_stage=failure_stage));report['all_two_modes_partition_bound_and_global_grid_gate_pass']=False
        code=2 if failure_stage=='independent_saved_certificate_gate' and isinstance(exc,ValueError) else 1
        report['failure_category']='retained_independent_certificate_gate_failure' if code==2 else 'retained_host_schema_source_or_unknown_failure'
    finally:
        after={}
        for path in expected:
            try:after[path]=sha(Path(path).read_bytes())
            except OSError as exc:report['errors'].append(dict(type=type(exc).__name__,message=str(exc),path=path))
        report['source_input_before']=before;report['source_input_after']=after;report['source_input_interval_closed']=bool(expected) and before==after==expected
        if not report['source_input_interval_closed']:code=1
        report['actual_reader_exit_code']=code
        report['limits']=['No pruned subtree objective was evaluated; safety uses the independently reconstructed upper proof and exact comparison with prior unpruned leaf incumbent.',
            'The historical full branch event/decision digest is unavailable and not reconstructed.',
            'Typed primitive provenance is inherited and matched; symbolic transcendental input exactness is not claimed.',
            'Only the explicitly supplied closed Python point; no batch worker is started. Native needs its own operands and new bound/leaf checks, with recursive refinement when unsafe to close.']
        (args.output_dir/'ACTUAL_CLOSED_PYTHON_GRID_INDEPENDENT_PRUNE_TRIE_ANALYTIC_COVERAGE_V1.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    print(json.dumps(dict(exit_code=code,completed_modes=len(report['rows']),all_pass=report.get('all_two_modes_partition_bound_and_global_grid_gate_pass',False),objective_evaluations=[r['actual_independent_objective_evaluations'] for r in report['rows']],source_input_closed=report['source_input_interval_closed'])))
    return code


if __name__=='__main__':raise SystemExit(main())
