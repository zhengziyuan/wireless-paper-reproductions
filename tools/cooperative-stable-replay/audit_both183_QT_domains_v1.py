"""Check all12344 original QT before/candidate domains and constraints.

Every actual primal coordinate is read from the published full MAT tapes.
Previously completed full MP100 contractions are reused after exact complete
input, report and current oracle bindings; no fresh MP contraction is claimed.
"""
import argparse
from decimal import Decimal,localcontext
import hashlib
import json
from pathlib import Path
import time

import numpy as np
from scipy.io import loadmat
import audit_native_case as layout
import audit_native_physics_mp as physics_oracle
import mp_phase_reference as physical_reference
import native183_evidence as native_transport
import replay_python_final_QT_evidence as python_transport
import phase183_evidence as helper


def require(condition,message):
    if not condition:raise ValueError(message)
def read(path):return json.loads(path.read_bytes())
def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda:stream.read(1024*1024),b''):h.update(block)
    return h.hexdigest()
def save(path,value):
    path.write_bytes((json.dumps(value,indent=2,allow_nan=False)+'\n').encode())


def domain(values,shape,nonnegative):
    values=np.asarray(values)
    require(values.size==int(np.prod(shape)),'Every original primal coordinate is required')
    finite=bool(np.isfinite(values).all())
    real=bool(not np.iscomplexobj(values) or np.all(values.imag==0))
    result=dict(actual_shape=list(values.shape),full_original_shape=list(shape),finite=finite,
        real_if_required=real if nonnegative else True)
    if nonnegative:
        require(real and finite,'An MR primal coordinate is complex or nonfinite')
        minimum=min(Decimal.from_float(float(x)) for x in np.asarray(values.real,dtype=float).reshape(-1))
        result.update(actual_minimum_exact_binary64=str(minimum),strict_nonnegative=bool(minimum>=0),
            within_original1e_minus5_constraint_tolerance=bool(minimum>=-Decimal.from_float(1e-5)))
    result['passed_strict_domain']=finite and (not nonnegative or real and result['strict_nonnegative'])
    return result


def feasibility(fields,power,limits):
    with localcontext() as context:
        context.prec=140
        p=np.asarray(power).reshape(-1);g=np.asarray(limits).reshape(-1)
        require(np.isfinite(p).all() and np.isfinite(g).all(),'Nonfinite original physical bounds')
        powers=list(map(Decimal,fields['satellite_power']['reference']))
        ground=list(map(Decimal,fields['gt_interference']['reference']))
        den=list(map(Decimal,fields['denominator']['reference']))
        require(len(p)==len(powers) and len(g)==len(ground) and den and
                all(x.is_finite() for x in powers+ground+den),'Missing/nonfinite full MP100 physical field')
        excess_power=max((x-Decimal.from_float(float(y)) for x,y in zip(powers,p)),default=Decimal(0))
        excess_ground=max((x-Decimal.from_float(float(y)) for x,y in zip(ground,g)),default=Decimal(0))
        tolerance=Decimal.from_float(1e-5)
        return dict(positive_denominators=all(x>0 for x in den),
            maximum_actual_power_excess=str(excess_power),maximum_actual_ground_interference_excess=str(excess_ground),
            passed_original1e_minus5_constraints=bool(all(x>0 for x in den) and
                excess_power<=tolerance and excess_ground<=tolerance))


def checked_payloads(packet,restored,language):
    manifest=read(packet/'archive-manifest.json')
    expected='complete-original-native183-phase-final-QT' if language=='native' else 'selected-Python183-final-states-and-all-QT'
    require(manifest['scope' if language=='native' else 'case_scope']==expected and manifest['actual_original_cases']==183,
            'The complete original183-case packet is required')
    for name,spec in manifest['files'].items():
        require(helper.safe(name),'Unsafe numerical payload')
        path=restored/name
        require(path.is_file() and path.stat().st_size==spec['bytes'] and sha(path)==spec['sha256'],
                'A complete published primal input/reference byte differs: '+name)
    if language=='native':
        cases=read(restored/'complete-native183-case-index.json')['cases']
        rows=[dict(ordinal=c['ordinal'],container=c['container'],states=c['states'],
            reference=c['physics_reference'],dimensions=c['dimensions'],QT=c['actual_QT_candidates']) for c in cases]
    else:
        cases=read(restored/'all183-exact-case-mapping.json')
        rows=[]
        for c in cases:
            document=read(restored/c['relative_container']);record=document['state_recording']
            require(helper.safe(record['filename']) and '/' not in record['filename'] and '\\' not in record['filename'],
                    'One safe complete original native-adapted MAT is required')
            rows.append(dict(ordinal=c['ordinal'],container=c['relative_container'],
                states=str(Path(c['relative_container']).parent/record['filename']).replace('\\','/'),
                reference=c['relative_reference'],dimensions=document['configuration']['reported'],QT=c['actual_QT_candidates']))
    require([c['ordinal'] for c in rows]==list(range(183)),'Every original case must be included exactly once')
    for row in rows:
        require(all(helper.safe(row[k]) and row[k] in manifest['files'] for k in ('container','states','reference')),
                'Every full original input/reference must be a manifest member')
    return rows,manifest


def audit_language(packet,restored,output,language):
    rows,manifest=checked_payloads(packet,restored,language)
    counts={'AP':0,'MR':0};events=[];cases=[];bindings=[]
    for case in rows:
        container=restored/case['container'];matrix=restored/case['states'];prior=restored/case['reference']
        bound={str(p):sha(p) for p in (container,matrix,prior)}
        physical=read(prior);identity=physical['source_input_sha256']
        require(identity['result']==sha(container) and identity['states']==sha(matrix) and
                identity['auditor']==sha(Path(physics_oracle.__file__)) and
                identity['reference']==sha(Path(physical_reference.__file__)) and
                physical['all_physical_QT_and_precision_checks_pass'] and physical['source_and_inputs_unchanged'],
                'A complete MP100 oracle, physical report or primal source binding differs')
        tape=loadmat(matrix,simplify_cells=True)['recording']
        J,U,N=(int(case['dimensions'][key]) for key in ('J','U','N'))
        candidates=layout.sequence(tape['QT_candidates']);references=physical['lanes']['100']['QT_candidates']
        require(len(candidates)==len(references)==case['QT'],'All original QT updates are required')
        found=[]
        for i,(state,reference) in enumerate(zip(candidates,references)):
            args=layout.sequence(state['input']);kind=state['kind']
            require(reference['index']==i and reference['kind']==kind and kind in ('mr_qt_update','ap_qt_update'),
                    'An actual original QT identity differs')
            nonnegative=kind=='mr_qt_update';shape=(J,U) if nonnegative else (J,N,U)
            old=domain(args[0],shape,nonnegative);new=domain(state['candidate'],shape,nonnegative)
            first=feasibility(reference['before_fields'],args[-2],args[-1])
            last=feasibility(reference['after_fields'],args[-2],args[-1])
            row=dict(index=i,kind=kind,before_domain=old,candidate_domain=new,
                independent_MP100_before_feasibility=first,independent_MP100_candidate_feasibility=last)
            found.append(row);counts['MR' if nonnegative else 'AP']+=1
            if not(old['passed_strict_domain'] and new['passed_strict_domain'] and
                    first['passed_original1e_minus5_constraints'] and last['passed_original1e_minus5_constraints']):
                events.append(dict(ordinal=case['ordinal'],**row))
        require(bound=={p:sha(Path(p)) for p in bound},'A complete source/input changed during domain verification')
        cases.append(dict(ordinal=case['ordinal'],actual_QT_candidates=len(found),all_original_candidates=found))
        bindings.append(dict(ordinal=case['ordinal'],container_sha256=sha(container),states_sha256=sha(matrix),
            complete_MP100_report_sha256=sha(prior)))
        if len(cases)%30==0:print(json.dumps(dict(language=language,actual_original_cases=len(cases),actual_QT_updates=sum(counts.values()))),flush=True)
    require(counts==({'AP':1696,'MR':4485} if language=='native' else {'AP':1696,'MR':4467}),
            'The complete original QT population differs')
    result=dict(language=language,actual_original_cases=183,actual_QT_candidates=sum(counts.values()),
        actual_AP_QT_candidates=counts['AP'],actual_MR_QT_candidates=counts['MR'],
        all_exact_primal_domains_and_both_before_candidate_original_tolerance_constraints_pass=not events,
        actual_domain_or_before_candidate_constraint_events=events,cases=cases,exact_input_and_reference_bindings=bindings,
        full_original_packet_archive_sha256=manifest['archive']['sha256'],
        actual_fresh_MP100_physical_contractions=0,complete_existing_MP100_contractions_reused=True,
        exact_binary64_primal_domains_freshly_checked=True,original_optimizer_RNG_or_gradient_calls=0,
        every_inner_state_dual_KKT_original_reference_or_full_paper_pass=False)
    save(output,result);return result


def run(args):
    require(not args.output_dir.exists(),'Preserve earlier complete/failed domain replay epochs')
    args.output_dir.mkdir(parents=True);start=time.perf_counter()
    watched=[Path(__file__),Path(layout.__file__),Path(physics_oracle.__file__),Path(physical_reference.__file__),Path(helper.__file__)]
    before={str(p):sha(p) for p in watched}
    native=args.native_restored
    if native is None:_,_,native=native_transport.unpack(args.native_packet,args.output_dir/'native-transport')
    python=args.python_restored
    if python is None:python,_=python_transport.unpack(args.python_packet,args.output_dir/'python-transport')
    summaries=[]
    for language,packet,root in [('native',args.native_packet,native),('python',args.python_packet,python)]:
        result=audit_language(packet,root,args.output_dir/(language+'-all183-QT-domains.json'),language)
        summaries.append({k:v for k,v in result.items() if k not in ('cases','exact_input_and_reference_bindings')})
    after={str(p):sha(p) for p in watched};require(before==after,'An original physical/domain oracle changed')
    summary=dict(actual_language_populations=2,actual_original_cases_per_language=183,
        actual_original_QT_updates=12344,all_original_QT_before_candidate_domains_and_constraints_pass=all(
            r['all_exact_primal_domains_and_both_before_candidate_original_tolerance_constraints_pass'] for r in summaries),
        complete_original_MP100_physical_contractions_reused=True,actual_fresh_MP100_contractions=0,
        exact_full_primal_binary64_domain_checks_freshly_computed=True,source_before=before,source_after=after,
        elapsed_seconds=time.perf_counter()-start,populations=summaries,original_optimizer_RNG_or_gradient_calls=0,
        every_inner_state_dual_KKT_original_reference_or_full_paper_pass=False)
    save(args.output_dir/'summary.json',summary)
    print(json.dumps({k:v for k,v in summary.items() if k not in ('source_before','source_after','populations')}),flush=True)
    return summary


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('native-packet','python-packet','output-dir'):p.add_argument('--'+name,type=Path,required=True)
    for name in ('native-restored','python-restored'):p.add_argument('--'+name,type=Path)
    if not run(p.parse_args())['all_original_QT_before_candidate_domains_and_constraints_pass']:raise SystemExit(1)
