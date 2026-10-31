"""N6/M5-only independent branch. N4/M3 still uses whole original V2 module.
Generic n/m values, bounds, tangent and graph count were checked against actual
complete original-bank N6/M5 D3/g0 all84 scientific enumeration, not a controller
test. No original model/bound/search/MC/optimizer/RNG function is called.
"""
from fractions import Fraction as F
import hashlib,itertools,json,math,pickle
generic_math=None
def enc(v):return json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
def sha(b):return hashlib.sha256(b).hexdigest()
def need(v,message):
    if not v:raise ValueError(message)

def typed_identity(groups,mode,D):
    v=dict(schema='actual-exact-model-typed-operands-v1',mode=mode,N=6,M=5,D=D,
           groups={key:dict(type=type(value).__name__,typed_SHA256=sha(pickle.dumps(value,protocol=5))) for key,value in groups.items()},
           typed_serialization='local trusted Python pickle5 digest; no unpickle input')
    return dict(v,SHA256=sha(enc(v)))


def reconstruct_own_operands(job,mode,np,k):
    need(job['N']==6 and job['M']==5,'This generic dimensional branch requires exact N6/M5');n=job['N'];m=job['M']
    D=job['brute_force_D'];need(type(D) is int and 2<=D<=64,'Invalid D')
    g=job['geometry'];theta=np.asarray(g['elevation']);phi=np.asarray(g['azimuth'])
    c=dict(beta=(1e-4*np.asarray(g['distances_m'])**-2.8).tolist(),
           directions=np.c_[np.cos(theta)*np.sin(phi),np.sin(theta)].tolist(),
           rician=[job['kappa']]*m,noise=[1e-11]*m,power=job['power'],minimum_distance=.5,wavelength=1.)
    grid=np.array([[x,y] for x in np.linspace(job['region_lower'][0],job['region_upper'][0],D)
                   for y in np.linspace(job['region_lower'][1],job['region_upper'][1],D)])
    points=[tuple(map(k.q,row)) for row in grid];P=len(points)
    compatible=[[sum((points[i][d]-points[j][d])**2 for d in range(2))>=k.q(.5)**2
                 for j in range(P)] for i in range(P)]
    groups=dict(grid=grid,compatible=compatible,terms={},diagonal=None)
    terms=groups['terms'];diagonal=None;constants=generic_math.constants(c,n,m,mode,k)
    if mode=='MRT':
        wave=2*np.pi/c['wavelength'];directions=np.asarray(c['directions'])
        for u in range(m):
            for v in range(m):
                if u!=v:
                    phasor=np.exp(1j*wave*(grid@(directions[u]-directions[v])))
                    terms[u,v]=[(k.q(z.real),k.q(z.imag)) for z in phasor]
        groups.update(base=constants['offset'],numerator=constants['desired'],coefficient=constants['coefficient'])
    else:
        h=np.exp(2j*np.pi/c['wavelength']*(grid@np.asarray(c['directions']).T))
        scale=[k.q(x) for x in np.sqrt(np.asarray(c['rician'])/(np.asarray(c['rician'])+1))]
        weighted=[[(k.q(z.real)*scale[u],k.q(z.imag)*scale[u]) for u,z in enumerate(row)] for row in h]
        diagonal=[[k.znorm(row[u])/n for u in range(m)] for row in weighted]
        for u,v in itertools.combinations(range(m),2):
            z=[k.zmul(k.zconj(row[u]),row[v]) for row in weighted]
            terms[u,v]=[(x[0]/n,x[1]/n) for x in z]
        groups.update(diagonal=diagonal,base=constants['offset'],eta=constants['eta'])
    return dict(constants,grid=grid,spacing=k.q(.5),terms=terms,diagonal=diagonal,m=m,n=n),groups,compatible


def certify_partition(o,compatible,mode,checkpoint,certificate,k,b):
    witnesses,framing=b.read_certificate(certificate,checkpoint)
    counter=generic_math.CliqueCounter(compatible);P=counter.P;n=o['n']
    cuts={}
    trie={}
    for w in witnesses:
        p=tuple(w['prefix']);need(0<len(p)<n and p==tuple(sorted(set(p))) and 0<=p[0]<=p[-1]<P,'Invalid cut prefix')
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
        counts['nodes']+=1;r=n-len(prefix)
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
            upper=generic_math.base_upper(o,prefix,remaining,mode,k,b)
            tangent_counts=w['supporting_dyadic_counts']
            if tangent_counts is not None:
                need(mode=='ZF' and r>=2,'Unexpected tangent witness')
                tangent=generic_math.supporting_tangent_upper(o,prefix,remaining,tangent_counts,k,b)
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
    graph_count=counter.count(counter.all,n)
    need(covered==graph_count and seen==set(cuts),'Coverage count or consumed cut list differs')
    need(all(counts[key]==checkpoint[key] for key in ['nodes','leaves','infeasible','prunes']),'Checkpoint traversal counters differ')
    need(counts['nodes']==checkpoint['sequence'],'Decision count differs')
    stored=F(int(checkpoint['best'][0]),int(checkpoint['best'][1]))
    need(incumbent==stored and list(winner)==checkpoint['winner'],'Saved exact winner/product differs')
    # If every cut is strictly below final best, no hidden tied optimum exists.
    strict_cuts=all(value<incumbent for value in cut_uppers)
    return dict(mode=mode,grid_points=P,complete_unordered_sets=math.comb(P,n),
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
