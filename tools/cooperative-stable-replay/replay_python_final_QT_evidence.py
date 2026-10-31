"""Restore and independently replay all183 selected Python final/QT recordings."""
import argparse
from collections import Counter
from decimal import Decimal,localcontext
import hashlib
from pathlib import Path
import tarfile

from audit_native_case import sha
from audit_native_physics_mp import audit
from build_power_curve_views import read,require,write
from unpack_power_evidence import safe


def unpack(packet,output):
    require(not output.exists(),'Preserve any previous complete or partial replay')
    manifest=read(packet/'archive-manifest.json')
    require(manifest['case_scope']=='selected-Python183-final-states-and-all-QT' and
        manifest['language']=='python' and manifest['original_case_ordinals']==list(range(183)) and
        manifest['actual_original_cases']==183 and manifest['schemes_per_case']==8 and
        manifest['actual_final_states']==1464 and
        manifest['full_actual_numerical_final_states_and_QT_inputs_candidates_included'] is True,
        'Every original source slot, final state and complete QT population is required')
    require(sha(packet/'actual-retained-QT-tolerance-analysis.json')==manifest['retained_tolerance_analysis_SHA256'],
            'The actual full-population tolerance qualification is required')
    spec=manifest['archive'];require(safe(spec['filename']) and spec['parts'],'Safe complete archive required')
    output.mkdir(parents=True);archive_path=output/'verified-source-archive.tar.gz'
    digest=hashlib.sha256();count=0
    with archive_path.open('wb') as stream:
        for i,part in enumerate(spec['parts']):
            require(safe(part['file']) and part['file']==spec['filename']+f'.part{i:03d}',
                    'Safe archive part order required')
            raw=(packet/part['file']).read_bytes()
            require(len(raw)==part['bytes'] and hashlib.sha256(raw).hexdigest()==part['sha256'],
                    'An original archive part differs')
            stream.write(raw);digest.update(raw);count+=len(raw)
    require(count==spec['bytes'] and digest.hexdigest()==spec['sha256'],'Complete original archive differs')
    restored=output/'payloads';restored.mkdir();seen=set()
    with tarfile.open(archive_path,'r:gz') as archive:
        for member in archive:
            name=member.name
            require(safe(name) and member.isfile() and name not in seen and name in manifest['files'],
                    'Unsafe, duplicated or unlisted numerical payload')
            wanted=manifest['files'][name];require(member.size==wanted['bytes'],'Payload size differs')
            raw=archive.extractfile(member).read()
            require(hashlib.sha256(raw).hexdigest()==wanted['sha256'],'A numerical payload differs')
            p=restored/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw);seen.add(name)
    require(seen==set(manifest['files']),'An original numerical payload is missing')
    return restored,manifest


def run(args):
    T=Path(__file__).resolve().parent
    sources=[Path(__file__),T/'audit_native_physics_mp.py',T/'mp_phase_reference.py',T/'audit_native_case.py']
    watch={str(p):sha(p) for p in sources}
    restored,manifest=unpack(args.packet,args.output_dir)
    index=T.parents[1]/'strict/validation/cooperative-original183-inputs-20261017/original-case-index.json'
    require(sha(index)==manifest['source_case_index_SHA256'],'The original183-case source index differs')
    identities={r['ordinal']:r for r in read(index)['cases']}
    closed_path=restored/'actual-complete183-final-QT-progress.json';closed=read(closed_path)
    require(sha(closed_path)==manifest['actual_complete183_progress_SHA256'] and
        closed['finished_cases']==closed['passed_final_QT_cases']==183 and
        closed['all183_selected_Python_final_QT_fields_constraints_and_precision_pass'],
        'The actual complete183-case reference closure is required')
    diagnostic=read(args.packet/'actual-retained-QT-tolerance-analysis.json')
    require(diagnostic['actual_complete_progress_SHA256']==sha(closed_path) and
        diagnostic['original_retained_nondecrease_tolerance']=='1e-5',
        'The actual original nondecrease tolerance and complete reference association must remain explicit')
    reuse=args.reuse_exact_complete_local_reference_bank is not None
    if reuse:
        require(sha(args.reuse_exact_complete_local_reference_bank)==sha(closed_path),
                'Reuse requires the exact complete183-case local closure')
        local=read(args.reuse_exact_complete_local_reference_bank)
        require(all(Path(p).is_file() and sha(Path(p))==h for p,h in local['source_before'].items()),
                'A completed local reference source changed')
    rows=read(restored/'all183-exact-case-mapping.json')
    require([r['ordinal'] for r in rows]==list(range(183)),'Every original source slot must remain in order')
    originals={r['ordinal']:r for r in closed['records']};reports=[];fresh=0;total_qt=0;coordinates=0
    negative=[];worst=None;kind_counts=Counter()
    for row in rows:
        n=row['ordinal'];old=originals[n]
        require(row['source_identity']==identities[n] and safe(row['relative_container']) and
            row['relative_container'].startswith(f'case-{n:03d}/') and
            row['relative_reference']==f'case-{n:03d}/original-complete-MP80-MP100.json',
            'The exact source identity and safe case association are required')
        container=restored/row['relative_container'];prior_path=restored/row['relative_reference']
        view=read(container);prior=read(prior_path)
        require(sha(container)==row['container_SHA256']==old['container_SHA256'] and
            sha(prior_path)==row['complete_reference_SHA256']==old['report_SHA256'] and
            row['selected_Python_epoch']==old['selected_Python_epoch'] and
            row['source_origin_SHA256']==old['source_origin_SHA256'] and
            view['configuration']['reported']==identities[n]['full_reported_scene'],
            'The actual original configuration, selected epoch, recording or reference differs')
        state=view['state_recording'];require(safe(state['filename']) and '/' not in state['filename'],
                                               'One safe original numerical tape required')
        tape=container.parent/state['filename']
        require(sha(tape)==state['sha256']==prior['source_input_sha256']['states'] and
            sha(container)==prior['source_input_sha256']['result'] and
            sha(T/'audit_native_physics_mp.py')==prior['source_input_sha256']['auditor'] and
            sha(T/'mp_phase_reference.py')==prior['source_input_sha256']['reference'] and
            prior['all_physical_QT_and_precision_checks_pass'] and prior['source_and_inputs_unchanged'] and
            old['actual_final_states']==row['actual_final_states']==prior['final_states']==8 and
            old['actual_QT_candidates']==row['actual_QT_candidates']==prior['QT_candidates'] and
            old['scalar_values_per_precision']==row['scalar_values_per_precision']==prior['scalar_values_per_precision'],
            'Every numerical input, complete population and current independent math source must match')
        if reuse:
            actual_path=Path(old['physical_QT_report'])
            require(actual_path.is_file() and sha(actual_path)==sha(prior_path),
                    'Reuse requires each actual complete local reference report')
            actual=prior
        else:
            actual_path=args.output_dir/'fresh-complete-references'/f'case-{n:03d}-MP80-MP100.json'
            actual_path.parent.mkdir(exist_ok=True);actual=audit(container,actual_path);fresh+=1
        require(actual['all_physical_QT_and_precision_checks_pass'] and actual['source_and_inputs_unchanged'] and
            actual['final_states']==8 and actual['QT_candidates']==prior['QT_candidates'] and
            actual['scalar_values_per_precision']==prior['scalar_values_per_precision'],
            'An actual complete independent final/QT case failed')
        total_qt+=actual['QT_candidates'];coordinates+=actual['scalar_values_per_precision']
        with localcontext() as decimal_context:
            decimal_context.prec=120
            for candidate in actual['lanes']['100']['QT_candidates']:
                before=list(map(Decimal,candidate['before_fields']['sinr']['reference']))
                after=list(map(Decimal,candidate['after_fields']['sinr']['reference']))
                delta=min(after)-min(before);kind_counts[candidate['kind']]+=1
                require(delta>=Decimal('-0.00001'),'An original tolerance-based nondecrease check failed')
                event=dict(original_ordinal=n,QT_index=candidate['index'],kind=candidate['kind'],
                    actual_MP100_minimum_SINR_increment=str(delta),reference_SHA256=row['complete_reference_SHA256'])
                if worst is None or delta<Decimal(worst['actual_MP100_minimum_SINR_increment']):worst=event
                if delta<0:negative.append(event)
        reports.append(dict(ordinal=n,all_physical_QT_and_precision_checks_pass=True,
                            QT_candidates=actual['QT_candidates']))
        if (n+1)%30==0:print(dict(actual_complete_cases=n+1,total=183,fresh_reference_cases=fresh),flush=True)
    require(total_qt==manifest['actual_QT_candidates']==closed['actual_QT_candidates_closed'] and
        coordinates==manifest['scalar_values_per_precision']==closed['actual_scalar_coordinates_per_precision_closed'],
        'Every original QT candidate and independent scalar coordinate must remain included')
    require(watch=={p:sha(Path(p)) for p in watch},'An active independent reader or physical reference changed')
    require(dict(kind_counts)==diagnostic['actual_QT_counts_by_kind'] and
        len(negative)==diagnostic['negative_MP100_minimum_SINR_increments']==len(diagnostic['actual_negative_increments']),
        'Every original QT kind and negative increment must remain included')
    for event,prior in zip(negative,diagnostic['actual_negative_increments']):
        require(all(event[k]==prior[k] for k in ('original_ordinal','QT_index','kind','reference_SHA256')) and
            abs(Decimal(event['actual_MP100_minimum_SINR_increment'])-
                Decimal(prior['actual_MP100_minimum_SINR_increment']))<=Decimal('1e-40'),
            'An actual negative increment or its original numerical reference differs')
    summary=dict(actual_original_cases=183,actual_final_states=1464,actual_QT_candidates=total_qt,
        actual_scalar_coordinates_per_precision=coordinates,actual_payloads_byte_verified=len(manifest['files']),
        all_original_slots_and_numerical_tapes_and_complete_references_present=True,
        actual_cases_freshly_evaluated=fresh,actual_complete_local_reference_bank_reused=reuse,
        all_original_tolerance_based_physical_QT_constraints_and_precision_checks_pass=True,
        original_nondecrease_absolute_tolerance='1e-5',actual_QT_counts_by_kind=dict(kind_counts),
        actual_negative_MP100_minimum_SINR_increments=len(negative),worst_actual_increment=worst,
        literal_exact_nondecrease_for_every_QT_candidate=(not negative),
        new_original_optimizer_or_production_evaluator_or_RNG_calls=0,
        phase_stops_MC_outer_histories_source_curve_or_global_optimum_or_paper_pass=False,
        archive_SHA256=manifest['archive']['sha256'],replayer_SHA256=sha(Path(__file__)))
    write(args.output_dir/'summary.json',summary);write(args.output_dir/'all183-case-results.json',reports)
    print(summary,flush=True);return summary


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--packet',type=Path,required=True)
    p.add_argument('--output-dir',type=Path,required=True)
    p.add_argument('--reuse-exact-complete-local-reference-bank',type=Path)
    run(p.parse_args())
