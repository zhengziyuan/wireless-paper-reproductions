"""Versioned correction of an overstrict saved MA N4 pruning-certificate gate.

The frozen v2 reader stays unchanged. Its one positivity assertion is replaced
with an exact nonnegative-integer assertion. Empty feasible subtrees contribute
zero to the original partition, while every original bound/incumbent, coverage,
traversal and winner check remains. Actual saved-data execution needs a new
source-pinned reader plan and an external bounded guard; it is never automatic.
--synthetic-regression uses only seven-vertex compatibility graphs and stdlib.
"""
import sys
sys.dont_write_bytecode=True
import argparse
import ast
import copy
from datetime import datetime,timezone
from fractions import Fraction
from functools import lru_cache
import hashlib
import itertools
import json
import math
from pathlib import Path
import types

CORE_BYTES=20209
CORE_SHA='30d26f1d1198566ef1dc36babc210e822371006a2cd8671b7016e085f0d8a7fe'
OLD="need(amount>0,'Empty feasible cut')"
NEW="need(type(amount) is int and amount>=0,'Invalid feasible cut count')"
REPORT_NAME='ACTUAL_CLOSED_PYTHON_GRID_INDEPENDENT_PRUNE_TRIE_ANALYTIC_COVERAGE_V1.json'


def need(ok,message):
    if not ok:
        raise ValueError(message)


def enc(value):
    return json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def read_core(path):
    with path.open('rb') as f:
        raw=f.read(CORE_BYTES+1)
    need(len(raw)==CORE_BYTES and sha(raw)==CORE_SHA,'One exact unchanged frozen v2 reader')
    return raw,ast.parse(raw,filename=str(path))


def patched_partition(tree):
    original=next(x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name=='certify_partition')
    modified=copy.deepcopy(original)
    old=ast.parse(OLD).body[0];new=ast.parse(NEW).body[0]
    old_dump=ast.dump(old,include_attributes=False);found=[]
    class Replace(ast.NodeTransformer):
        def visit_Expr(self,node):
            if ast.dump(node,include_attributes=False)==old_dump:
                found.append(node);return ast.copy_location(copy.deepcopy(new),node)
            return self.generic_visit(node)
    modified=Replace().visit(modified)
    need(len(found)==1,'Exactly one original empty-cut positivity assertion')
    # An explicit inverse proves that no other original function AST changed.
    class Inverse(ast.NodeTransformer):
        def visit_Expr(self,node):
            if ast.dump(node,include_attributes=False)==ast.dump(new,include_attributes=False):
                return ast.copy_location(copy.deepcopy(old),node)
            return self.generic_visit(node)
    reverted=Inverse().visit(copy.deepcopy(modified))
    need(ast.dump(reverted,include_attributes=False)==ast.dump(original,include_attributes=False),
         'Only the explicitly reviewed assertion may change')
    return ast.fix_missing_locations(modified)


def annotate(row):
    cuts=row['verified_prune_rows']
    need(all(type(x['covered_feasible_sets']) is int and x['covered_feasible_sets']>=0 for x in cuts),
         'Every independently counted cut has an exact nonnegative cardinality')
    row['empty_feasible_completion_prune_count']=sum(x['covered_feasible_sets']==0 for x in cuts)
    row['positive_feasible_completion_prune_count']=sum(x['covered_feasible_sets']>0 for x in cuts)
    # These witnesses already exist in immutable certificate frames. Retain a
    # commitment, not another potentially large copy of every tangent vector.
    tangents=row.pop('actual_saved_tangent_witnesses')
    digest=hashlib.sha256()
    for item in tangents:
        digest.update(enc(item)+b'\n')
    row['saved_tangent_witness_readback']=dict(count=len(tangents),ordered_SHA256=digest.hexdigest(),
        original_witness_values_recomputed_and_checked=True,duplicate_body_retained=False)
    row['original_upper_incumbent_coverage_counter_winner_and_uniqueness_checks_unchanged']=True
    return row


def install(core,path,tree):
    module=types.ModuleType('_frozen_ma_reader_with_empty_cut_assertion_v4')
    module.__file__=str(path);module.__package__=''
    exec(compile(core,str(path),'exec'),module.__dict__)
    function=patched_partition(tree)
    exec(compile(ast.Module(body=[function],type_ignores=[]),str(path)+'::empty-cut-v4','exec'),module.__dict__)
    corrected=module.certify_partition
    def checked(*args,**kwargs):
        return annotate(corrected(*args,**kwargs))
    module.certify_partition=checked
    return module


def synthetic(tree):
    """Complete finite seven-vertex regression, never a saved scientific pass."""
    names={'enc','sha','need','CompatibilityCounter','certify_partition'}
    subset=[copy.deepcopy(x) for x in tree.body if isinstance(x,(ast.FunctionDef,ast.ClassDef)) and x.name in names]
    env=dict(F=Fraction,lru_cache=lru_cache,hashlib=hashlib,itertools=itertools,json=json,math=math)
    exec(compile(ast.Module(body=subset,type_ignores=[]),'frozen-v2-synthetic-only','exec'),env)
    original=env['certify_partition'];counter=env['CompatibilityCounter']
    exec(compile(ast.Module(body=[patched_partition(tree)],type_ignores=[]),'patched-v4-synthetic-only','exec'),env)
    corrected=env['certify_partition']
    graph=[[False]*7 for _ in range(7)]
    for i,j in list(itertools.combinations(range(4),2))+[(0,4),(0,5),(0,6),(4,5),(4,6)]:
        graph[i][j]=graph[j][i]=True
    # Independent complete combination enumeration: only (0,1,2,3) is feasible.
    feasible=[c for c in itertools.combinations(range(7),4) if all(graph[i][j] for i,j in itertools.combinations(c,2))]
    need(feasible==[(0,1,2,3)],'Exact synthetic feasible set')
    checkpoint=dict(nodes=17,leaves=1,infeasible=11,prunes=1,sequence=17,best=['1','1'],winner=[0,1,2,3])
    fraction_record=lambda x:[str(x.numerator),str(x.denominator)]
    fraction_hash=lambda x:sha(enc(fraction_record(x)))
    kernel=types.SimpleNamespace(independent_product=lambda o,p,m:Fraction(1) if tuple(p)==(0,1,2,3) else Fraction(1,4),
                                rational_record=fraction_record)
    def fixture(upper=Fraction(1,2),prefix=(0,4),digest=None):
        witness=dict(prefix=list(prefix),supporting_dyadic_counts=None,
                     exact_upper_SHA256=digest or fraction_hash(upper))
        return types.SimpleNamespace(read_certificate=lambda raw,c:([witness],{'synthetic':True}),
            independent_previous_upper=lambda *args:upper,rational_hash=fraction_hash)
    def invoke(fn,checkpoint_=None,b=None):
        return fn({},graph,'MRT',checkpoint_ or checkpoint,b'',kernel,b or fixture())
    outcomes=[]
    def reject(name,fn,message):
        try:
            fn()
        except ValueError as exc:
            need(message in str(exc),'Expected retained gate: '+name);outcomes.append(dict(name=name,pass_=True))
        else:
            raise AssertionError('Expected rejection: '+name)
    reject('frozen_v2_rejects_valid_empty_cut',lambda:invoke(original),'Empty feasible cut')
    row=annotate(invoke(corrected))
    need(row['partition_covered_feasible_sets']==1 and row['independently_counted_feasible_sets']==1
         and row['pruned_feasible_sets']==0 and row['verified_prune_count']==1
         and row['empty_feasible_completion_prune_count']==1
         and row['independent_prefix_counts']==dict(nodes=17,leaves=1,infeasible=11,prunes=1,branches=4)
         and row['earliest_canonical_global_winner_zero_based']==[0,1,2,3],
         'Zero-cut contribution preserves exact exhaustive coverage and original winner/counters')
    outcomes.append(dict(name='v4_empty_cut_covered_zero_and_full_partition_matches_all35_combinations',pass_=True))
    reject('wrong_upper_digest_still_rejected',lambda:invoke(corrected,b=fixture(digest='0'*64)),'Upper rational digest differs')
    reject('upper_above_prior_incumbent_still_rejected',lambda:invoke(corrected,b=fixture(upper=Fraction(2))),
           'Upper exceeds earlier independent leaf incumbent')
    bad=dict(checkpoint,nodes=18)
    reject('wrong_traversal_counter_still_rejected',lambda:invoke(corrected,checkpoint_=bad),'Checkpoint traversal counters differ')
    bad_winner=dict(checkpoint,winner=[0,1,2,4])
    reject('wrong_winner_still_rejected',lambda:invoke(corrected,checkpoint_=bad_winner),'Saved exact winner/product differs')
    reject('unreachable_cut_still_rejected',lambda:invoke(corrected,b=fixture(prefix=(0,2))),
           'Certificate contains an unreachable child')
    for invalid,label in [(-1,'negative'),(0.0,'noninteger')]:
        class InvalidCounter(counter):
            def count(self,mask,r):
                return invalid if mask==((1<<5)|(1<<6)) and r==2 else super().count(mask,r)
        env['CompatibilityCounter']=InvalidCounter
        reject(label+'_cardinality_still_rejected',lambda:invoke(corrected),'Invalid feasible cut count')
    env['CompatibilityCounter']=counter
    return dict(schema='SYNTHETIC_MA_EMPTY_FEASIBLE_CUT_REGRESSION_V4',all_pass=True,tests=outcomes,
        graph_vertices=7,complete_candidate_subsets=35,exact_feasible_subsets=1,
        cut_prefix=[0,4],remaining_vertices=[5,6],remaining_pair_incompatible=True,
        unchanged_function_AST_except_one_assertion=True,
        actual_saved_experiments_read=False,actual149_failures_revalidated=False,
        numerical_optimizer_MC_RNG_calls=0,scientific_or_paper_PASS=False)


class ReportLimit(Exception):
    pass


class OutputJSON:
    def __init__(self,adapter_sha):
        self.adapter_sha=adapter_sha
    def __getattr__(self,name):
        return getattr(json,name)
    def dumps(self,value,*args,**kwargs):
        if kwargs.get('indent')==2 and isinstance(value,dict) and value.get('schema')== \
                'actual-one-closed-Python-grid-independent-prune-trie-and-analytic-coverage-v1':
            value=dict(value,schema='actual-closed-Python-N4-grid-empty-feasible-cut-corrected-v4',
                versioned_reader_adapter_SHA256=self.adapter_sha,frozen_reader_SHA256=CORE_SHA,
                historical_failures_preserved=True,empty_cut_assertion_scope='exact integer count>=0; all original proof gates retained')
            text=json.dumps(value,*args,**kwargs)
            if len((text+'\n').encode('utf-8'))>65536:
                raise ReportLimit('Final corrected-reader report exceeds64KiB; no pass can be retained')
            return text
        return json.dumps(value,*args,**kwargs)


def fresh_json(path,value,limit):
    need(path.parent.is_dir() and not path.exists(),'Fresh small output in existing directory')
    raw=json.dumps(value,indent=2,allow_nan=False).encode()+b'\n';need(len(raw)<=limit,'Bounded small receipt')
    with path.open('xb') as f:
        f.write(raw);f.flush()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--frozen-reader',type=Path,required=True)
    parser.add_argument('--expected-frozen-reader-sha256',required=True)
    group=parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--synthetic-regression',action='store_true')
    group.add_argument('--execute-saved-reader',action='store_true')
    parser.add_argument('--synthetic-output',type=Path)
    args,remaining=parser.parse_known_args()
    need(sys.dont_write_bytecode and not sys.flags.optimize,'No bytecode or optimized assertions')
    need(args.expected_frozen_reader_sha256==CORE_SHA,'Fixed frozen v2 identity')
    source=Path(__file__).read_bytes();adapter_sha=sha(source)
    path=args.frozen_reader.resolve(strict=True);core,tree=read_core(path)
    if args.synthetic_regression:
        need(not remaining and args.synthetic_output is not None,'Synthetic-only exact graph route')
        result=synthetic(tree);result.update(adapter_SHA256=adapter_sha,frozen_reader_SHA256=CORE_SHA,
                                          UTC=datetime.now(timezone.utc).isoformat())
        fresh_json(args.synthetic_output.resolve(),result,8192)
        print(json.dumps(dict(all_pass=result['all_pass'],tests=len(result['tests']),actual_saved_experiments_read=False)))
        return 0
    need(args.synthetic_output is None,'No synthetic output in actual route')
    minimal=argparse.ArgumentParser(add_help=False)
    minimal.add_argument('--plan',type=Path,required=True);minimal.add_argument('--output-dir',type=Path,required=True)
    actual,_=minimal.parse_known_args(remaining)
    need(not actual.output_dir.exists(),'Never overwrite original failed reports or an attempted corrected run')
    with actual.plan.open('rb') as f:
        raw=f.read(65537)
    need(len(raw)<=65536,'Small explicit dependency plan')
    plan=json.loads(raw)
    need(plan['source_pins'].get(str(Path(__file__).resolve()))==adapter_sha
         and plan['source_pins'].get(str(path))==CORE_SHA,'New plan binds corrected adapter and unchanged frozen reader')
    module=install(core,path,tree);module.json=OutputJSON(adapter_sha)
    previous=sys.argv;sys.argv=[str(path)]+remaining
    try:
        try:
            return module.main()
        except ReportLimit as exc:
            fresh_json(actual.output_dir/REPORT_NAME,dict(schema='corrected-MA-reader-output-limit-failure-v4',
                error=str(exc),actual_reader_exit_code=1,all_two_modes_partition_bound_and_global_grid_gate_pass=False,
                historical_failures_preserved=True,adapter_SHA256=adapter_sha),8192)
            return 1
    finally:
        sys.argv=previous


if __name__=='__main__':
    raise SystemExit(main())
