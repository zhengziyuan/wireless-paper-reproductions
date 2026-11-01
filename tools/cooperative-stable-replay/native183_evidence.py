"""Complete original native183 phase/final/QT transport and MP80/100 replay.

Default replay freshly evaluates every phase and physical/QT tape. Explicit
local reuse requires the exact closed complete inventory and every original
input/reference/current-math hash. Every unit-domain endpoint is always fresh.
"""
import argparse
from decimal import Decimal,localcontext
import gzip
import hashlib
import json
from pathlib import Path
import tarfile
import zipfile

import mpmath as mp
import numpy as np
from scipy.io import loadmat

import phase183_evidence as phase
import inventory_complete_native183_phase_and_QT_v2 as original


SCOPE='complete-original-native183-phase-final-QT'


def bound(item):
    path=Path(item['path'])
    phase.require(path.stat().st_size==item['bytes'] and phase.sha(path)==item['sha256'],
                  'An actual complete native input or reference byte changed')
    return path


def build(args):
    phase.require(not args.packet.exists() and not args.work_dir.exists(),'Preserve previous native transport epochs')
    inventory=phase.read(args.inventory);closed=phase.read(args.terminal_receipt)
    phase.require(inventory['scope']=='complete-original-native183-phase-final-QT-evidence-inventory' and
        inventory['language']=='matlab' and inventory['exact_original_ordinals']==list(range(183)) and
        [c['ordinal'] for c in inventory['cases']]==list(range(183)),'All original native0..182 cases are required')
    phase.require(closed['status']=='actual_scientific_child_returned' and closed['actual_child_terminal_exit_code']==0 and
        closed['all_watched_source_and_job_bytes_unchanged'] and closed['source_before']==closed['source_after'],
        'Actual complete inventory/domain terminal0 and source closure are required')
    for path,digest in closed['source_after'].items():
        phase.require(phase.sha(Path(path))==digest,'A closed inventory control/source byte changed')
    before=original.modules();control=phase.sha(Path(__file__));inventory_control=phase.sha(Path(original.__file__))
    phase.require(before==inventory['current_independent_math_sources_SHA256'] and
        phase.sha(Path(original.__file__))==inventory['actual_source_guarded_inventory_SHA256'],
        'Every current independent math/inventory helper must match the actual closed checks')
    args.work_dir.mkdir(parents=True);payload={};cases=[]
    def add(name,path):
        phase.require(phase.safe(name) and name not in payload,'Unsafe/duplicate actual native payload')
        payload[name]=dict(path=path,bytes=path.stat().st_size,sha256=phase.sha(path))
    add('actual-complete-native183-inventory.json',args.inventory)
    domain_path=args.inventory.parent/'actual-all-native-phase-unit-domains-MP80-MP100.json'
    add('actual-all-original-native-phase-unit-domains.json',domain_path)
    for i,(path,digest) in enumerate(inventory['exact_closed_inputs_and_references_SHA256'].items()):
        source=Path(path);phase.require(phase.sha(source)==digest,'An actual original closed coordinator journal changed')
        add(f'original-closure-provenance/{i:02d}-{source.name}',source)
    terminal=dict(actual_full_native_inventory_and_domains_terminal_exit_code=0,
        all_actual_inventory_source_and_job_bytes_unchanged=True,
        exact_private_actual_owner_terminal_receipt_SHA256=phase.sha(args.terminal_receipt),
        actual_original_cases=183,original_optimizer_RNG_or_fresh_gradient_calls=0,
        raw_moment_vectors_every_inner_iterate_author_inputs_or_full_paper_pass=False)
    terminal_path=args.work_dir/'actual-native-inventory-terminal-closure.json'
    terminal_path.write_bytes(phase.encode(terminal));add(terminal_path.name,terminal_path)
    for case in inventory['cases']:
        n=case['ordinal'];prefix=f'case-{n:03d}';container=bound(case['container']);matrix=bound(case['states'])
        names={key:prefix+'/'+bound(case[key]).name for key in ('container','states')}
        add(names['container'],container);add(names['states'],matrix)
        configuration=bound(case['original_configuration']);names['original_configuration']=prefix+'/original-source-configuration.json'
        add(names['original_configuration'],configuration)
        physics=bound(case['physics_reference']);names['physics_reference']=prefix+'/complete-original-final-QT-MP80-MP100.json'
        add(names['physics_reference'],physics)
        phase.require(original.binding(container,matrix,original.phase_math)==case['phase_binding'] and
            original.binding(container,matrix,original.physics_math)==case['physics_binding'],
            'Every original native input and current independent reader hash must match')
        bundle=args.work_dir/f'case-{n:03d}-all-original-phase-references.zip';members=[]
        phase.require([x['file'] for x in case['phase_reference_members']]==
            ['summary.json']+[f'phase-{i:03d}.json' for i in range(case['actual_phase_endpoints'])],
            'Every original phase JSON reference is required')
        with zipfile.ZipFile(bundle,'x',compression=zipfile.ZIP_STORED) as archive:
            for item in case['phase_reference_members']:
                source=bound(item);raw=source.read_bytes()
                info=zipfile.ZipInfo(item['file'],(1980,1,1,0,0,0));info.external_attr=0o100644<<16
                archive.writestr(info,raw);members.append({k:item[k] for k in ('file','bytes','sha256')})
        names['phase_bundle']=prefix+'/'+bundle.name;add(names['phase_bundle'],bundle)
        public={k:v for k,v in case.items() if k not in
            ('container','states','original_configuration','physics_reference','phase_reference_members')}
        public.update(names,phase_reference_members=members);cases.append(public)
        if len(cases)%12==0:print(json.dumps(dict(actual_complete_native_cases_packed=len(cases),expected=183)),flush=True)
    index={k:v for k,v in inventory.items() if k not in ('cases','exact_closed_inputs_and_references_SHA256')}
    index.update(scope=SCOPE,cases=cases,exact_complete_inventory_SHA256=phase.sha(args.inventory),
        exact_original_unit_domain_report_SHA256=phase.sha(domain_path))
    index_path=args.work_dir/'complete-native183-case-index.json';index_path.write_bytes(phase.encode(index))
    add(index_path.name,index_path)
    archive_path=args.work_dir/'complete-native183-phase-final-QT-inputs-and-references.tar.gz'
    with archive_path.open('xb') as raw:
        with gzip.GzipFile(fileobj=raw,mode='wb',filename='',mtime=0) as compressed:
            with tarfile.open(fileobj=compressed,mode='w|') as archive:
                for name,item in sorted(payload.items()):
                    phase.require(phase.sha(item['path'])==item['sha256'],'An actual sealed native payload changed')
                    member=tarfile.TarInfo(name);member.size=item['bytes'];member.mode=0o644;member.mtime=0
                    with item['path'].open('rb') as source:archive.addfile(member,source)
    phase.require(before==original.modules() and control==phase.sha(Path(__file__)) and
                  inventory_control==phase.sha(Path(original.__file__)),
                  'An active native math or transport source changed')
    args.packet.mkdir(parents=True);parts=[]
    with archive_path.open('rb') as source:
        for n,raw in enumerate(iter(lambda:source.read(512*1024),b'')):
            name=archive_path.name+f'.part{n:03d}';(args.packet/name).write_bytes(raw)
            parts.append(dict(file=name,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest()))
    manifest=dict(scope=SCOPE,language='matlab',actual_original_cases=183,exact_original_ordinals=list(range(183)),
        archive=dict(filename=archive_path.name,bytes=archive_path.stat().st_size,sha256=phase.sha(archive_path),parts=parts),
        files={name:{k:item[k] for k in ('bytes','sha256')} for name,item in payload.items()},packager_SHA256=control)
    (args.packet/'archive-manifest.json').write_bytes(phase.encode(manifest))
    summary={k:v for k,v in index.items() if k not in ('cases',)}
    (args.packet/'complete-native183-scope-summary.json').write_bytes(phase.encode(summary))
    print(json.dumps(dict(actual_original_cases=183,actual_phase_endpoints=index['actual_phase_endpoints'],
        actual_QT_candidates=index['actual_QT_candidates'],archive_bytes=manifest['archive']['bytes'],
        archive_SHA256=manifest['archive']['sha256'],parts=len(parts),actual_payloads=len(payload))),flush=True)


def unpack(packet,output):
    phase.require(not output.exists(),'Use a fresh complete native replay destination')
    manifest=phase.read(packet/'archive-manifest.json')
    phase.require(manifest['scope']==SCOPE and manifest['language']=='matlab' and manifest['actual_original_cases']==183 and
        manifest['exact_original_ordinals']==list(range(183)),'Require the complete original native183 scope')
    spec=manifest['archive'];phase.require(phase.safe(spec['filename']) and spec['parts'],'Safe complete archive required')
    output.mkdir(parents=True);archive_path=output/'verified-complete-native-transport.tar.gz';h=hashlib.sha256();length=0
    with archive_path.open('xb') as stream:
        for n,part in enumerate(spec['parts']):
            phase.require(part['file']==spec['filename']+f'.part{n:03d}' and phase.safe(part['file']),
                          'Unsafe or missing original native archive part')
            raw=(packet/part['file']).read_bytes()
            phase.require(len(raw)==part['bytes'] and hashlib.sha256(raw).hexdigest()==part['sha256'],'Actual original native archive part differs')
            stream.write(raw);h.update(raw);length+=len(raw)
    phase.require(length==spec['bytes'] and h.hexdigest()==spec['sha256'],'Whole original native archive differs')
    restored=output/'restored';restored.mkdir();found=set()
    with tarfile.open(archive_path,'r|gz') as source:
        for member in source:
            name=member.name
            phase.require(phase.safe(name) and member.isfile() and name in manifest['files'] and name not in found,
                          'Unsafe, duplicated or unlisted native numerical payload')
            wanted=manifest['files'][name];phase.require(member.size==wanted['bytes'],'Actual native member size differs')
            target=restored/name;target.parent.mkdir(parents=True,exist_ok=True);digest=hashlib.sha256()
            with target.open('xb') as destination:
                original_stream=source.extractfile(member)
                for block in iter(lambda:original_stream.read(1024*1024),b''):destination.write(block);digest.update(block)
            phase.require(digest.hexdigest()==wanted['sha256'],'Actual original native numerical member differs');found.add(name)
    phase.require(found==set(manifest['files']),'A complete native numerical payload is missing')
    index=phase.read(restored/'complete-native183-case-index.json')
    phase.require(index['scope']==SCOPE and index['language']=='matlab' and index['exact_original_ordinals']==list(range(183)) and
        [c['ordinal'] for c in index['cases']]==list(range(183)) and index['current_independent_math_sources_SHA256']==original.modules() and
        index['actual_source_guarded_inventory_SHA256']==phase.sha(Path(original.__file__)),
        'Every original native case and exact independent math/inventory source is required')
    for case in index['cases']:
        prefix=f"case-{case['ordinal']:03d}/"
        for key in ('container','states','original_configuration','physics_reference','phase_bundle'):
            phase.require(phase.safe(case[key]) and case[key].startswith(prefix) and case[key] in manifest['files'],
                          'Unsafe or missing complete native case operand')
        folder=restored/prefix/'all-original-phase-references';folder.mkdir()
        expected={'summary.json'}|{f'phase-{i:03d}.json' for i in range(case['actual_phase_endpoints'])}
        wanted={x['file']:x for x in case['phase_reference_members']}
        phase.require(set(wanted)==expected and len(wanted)==len(case['phase_reference_members']),
                      'Every complete native phase reference member is required')
        with zipfile.ZipFile(restored/case['phase_bundle']) as source:
            phase.require(set(source.namelist())==expected and len(source.namelist())==len(expected),
                          'Missing or duplicated actual native phase reference')
            for name in source.namelist():
                phase.require(phase.safe(name) and '/' not in name and not source.getinfo(name).is_dir(),
                              'Unsafe native phase reference name')
                raw=source.read(name);item=wanted[name]
                phase.require(len(raw)==item['bytes'] and hashlib.sha256(raw).hexdigest()==item['sha256'],
                              'An actual complete native phase reference byte differs')
                (folder/name).write_bytes(raw)
    return manifest,index,restored


def replay(args):
    before=original.modules();control=phase.sha(Path(__file__));inventory_control=phase.sha(Path(original.__file__))
    manifest,index,restored=unpack(args.packet,args.output_dir)
    local=None
    if args.reuse_exact_complete_local_inventory is not None:
        path=args.reuse_exact_complete_local_inventory
        phase.require(phase.sha(path)==index['exact_complete_inventory_SHA256']==phase.sha(restored/'actual-complete-native183-inventory.json'),
                      'Local reuse requires the exact complete native183 inventory bytes')
        cached=phase.read(path)
        phase.require(cached['current_independent_math_sources_SHA256']==before and
            [c['ordinal'] for c in cached['cases']]==list(range(183)), 'Only complete exact current native references may be reused')
        local={c['ordinal']:c for c in cached['cases']}
    rows=[];unit_cases=[];negative=[];phase_count=coordinates=QT_count=scalars=0
    maxima={80:mp.mpf(0),100:mp.mpf(0)};max_gap=mp.mpf(0)
    for case in index['cases']:
        n=case['ordinal'];container=restored/case['container'];matrix=restored/case['states'];document=phase.read(container)
        phase.require(original.configuration_transport(document['configuration'],phase.read(restored/case['original_configuration']))==
            case['actual_configuration_transport_receipt'] and
            phase.safe(document['state_recording']['filename']) and '/' not in document['state_recording']['filename'] and
            (container.parent/document['state_recording']['filename']).resolve()==matrix.resolve(),
            'Every full original native configuration and actual local MAT is required')
        phase.require(original.binding(container,matrix,original.phase_math)==case['phase_binding'] and
            original.binding(container,matrix,original.physics_math)==case['physics_binding'],
            'An actual complete native input or independent math byte differs')
        reference_dir=restored/f'case-{n:03d}'/'all-original-phase-references'
        prior_phase=phase.read(reference_dir/'summary.json');prior_physics=phase.read(restored/case['physics_reference'])
        if local is not None:
            cached=local[n]
            for key in ('container','states','original_configuration','physics_reference'):bound(cached[key])
            phase.require(original.binding(Path(cached['container']['path']),Path(cached['states']['path']),original.phase_math)==case['phase_binding'] and
                original.binding(Path(cached['container']['path']),Path(cached['states']['path']),original.physics_math)==case['physics_binding'],
                'The exact complete local native input/reference identity differs')
            for member,wanted in zip(cached['phase_reference_members'],case['phase_reference_members']):
                phase.require(member['file']==wanted['file'] and phase.sha(bound(member))==wanted['sha256'],
                              'A complete local original native phase report differs')
            phase.require(len(cached['phase_reference_members'])==len(case['phase_reference_members']) and
                phase.sha(bound(cached['physics_reference']))==phase.sha(restored/case['physics_reference']),
                'A local complete native physical/QT reference differs')
            phase_result=prior_phase;physical=prior_physics;fresh_phase=None
        else:
            fresh_phase=args.output_dir/f'fresh-case-{n:03d}-phase-MP80-MP100'
            phase_result=original.phase_math.audit(container,fresh_phase)
            physical=original.physics_math.audit(container,args.output_dir/f'fresh-case-{n:03d}-final-QT-MP80-MP100.json')
        phase.require(phase_result['source_input_sha256']==case['phase_binding'] and phase_result['source_and_input_unchanged'] and
            phase_result['dimensions']==case['dimensions'] and phase_result['stages']==case['actual_phase_endpoints'] and
            phase_result['complex_coordinates_per_lane']==case['complex_gradient_coordinates_per_precision'] and
            phase_result['all_MP_fields_original_stop_and_precision_checks_pass']==case['original_phase_fields_and_stops_pass'],
            'A complete actual native phase result, dimension, count or original stop differs')
        for i in range(case['actual_phase_endpoints']):
            expected=phase.read(reference_dir/f'phase-{i:03d}.json')
            if fresh_phase is not None:phase.require(phase.equivalent(phase.read(fresh_phase/f'phase-{i:03d}.json'),expected),
                                                  'A fresh complete native phase gradient, criterion or stop differs')
        phase.require(phase.equivalent({k:v for k,v in physical.items() if k!='elapsed_seconds'},
            {k:v for k,v in prior_physics.items() if k!='elapsed_seconds'}),
            'A fresh complete native final/QT field, constraint or precision result differs')
        with localcontext() as context:
            context.prec=130
            for item in physical['lanes']['100']['QT_candidates']:
                delta=min(map(Decimal,item['after_fields']['sinr']['reference']))-min(map(Decimal,item['before_fields']['sinr']['reference']))
                if delta<0:negative.append(dict(ordinal=n,QT_index=item['index'],kind=item['kind'],MP100_minimum_SINR_delta=str(delta),
                    within_original1e_minus5_nondecrease_tolerance=delta>=Decimal('-1e-5')))
        recording=loadmat(matrix,simplify_cells=True)['recording'];endpoints=original.layout.sequence(recording['phase_endpoints'])
        U,M=(case['dimensions'][k] for k in ('U','M'));unit_rows=[]
        phase.require(len(endpoints)==case['actual_phase_endpoints'],'Every actual native phase domain is required')
        for i,state in enumerate(endpoints):
            values=np.asarray(state['final_phi'],complex);phase.require(values.size==U*M,'Every native phase coordinate is required')
            errors={digits:original.domain.unit_error(values,digits) for digits in (80,100)}
            with mp.workdps(110):
                gap=abs(errors[80]-errors[100]);max_gap=max(max_gap,gap)
                passed=all(x<=original.reference.real(1e-10) for x in errors.values()) and gap<=mp.mpf('1e-40')
                for digits,value in errors.items():maxima[digits]=max(maxima[digits],value)
                unit_rows.append(dict(index=i,complex_phase_coordinates=values.size,
                    maximum_unit_modulus_error={str(d):mp.nstr(v,105) for d,v in errors.items()},
                    maximum_crossprecision_difference=mp.nstr(gap,105),passed=bool(passed)))
        unit_cases.append(dict(ordinal=n,actual_phase_endpoints=len(endpoints),
            all_actual_phase_domains_pass=all(x['passed'] for x in unit_rows),phases=unit_rows))
        phase.require(original.binding(container,matrix,original.phase_math)==case['phase_binding'] and
            original.binding(container,matrix,original.physics_math)==case['physics_binding'],
            'An actual restored native input changed during complete evaluation')
        phase_count+=phase_result['stages'];coordinates+=phase_result['complex_coordinates_per_lane']
        QT_count+=physical['QT_candidates'];scalars+=physical['scalar_values_per_precision']
        rows.append(dict(ordinal=n,original_phase_fields_and_stops_pass=phase_result['all_MP_fields_original_stop_and_precision_checks_pass'],
            original_final_QT_physics_pass=physical['all_physical_QT_and_precision_checks_pass'],
            actual_phase_domains_pass=unit_cases[-1]['all_actual_phase_domains_pass']))
        print(json.dumps(dict(actual_complete_native_cases=len(rows),expected=183,actual_phase_endpoints=phase_count,actual_QT_candidates=QT_count)),flush=True)
    with mp.workdps(110):
        domains=dict(language='matlab',actual_original_cases=183,actual_phase_endpoints_checked=phase_count,
            actual_complex_phase_coordinates_per_precision=coordinates,precisions=[80,100],original_unit_modulus_absolute_bound='1e-10',
            crossprecision_absolute_bound='1e-40',maximum_actual_unit_modulus_error={str(d):mp.nstr(v,105) for d,v in maxima.items()},
            maximum_MP80_MP100_difference=mp.nstr(max_gap,105),
            all_actual_original_phase_unit_domains_and_precision_pass=all(c['all_actual_phase_domains_pass'] for c in unit_cases),cases=unit_cases)
    phase.require(phase.equivalent(domains,phase.read(restored/'actual-all-original-native-phase-unit-domains.json')),
                  'A fresh complete native unit-domain calculation differs from the original full-cohort reference')
    phase.require(phase_count==index['actual_phase_endpoints'] and coordinates==index['actual_complex_gradient_coordinates_per_precision'] and
        QT_count==index['actual_QT_candidates'] and scalars==index['actual_physical_QT_scalar_values_per_precision'] and
        phase.equivalent(negative,index['actual_MP100_negative_QT_events']),
        'Every original native phase/QT coordinate and actual negative event must be retained')
    phase.require(before==original.modules() and control==phase.sha(Path(__file__)) and
        inventory_control==phase.sha(Path(original.__file__)), 'An active native math or replay source changed')
    (args.output_dir/'all-native-phase-unit-domains-MP80-MP100.json').write_bytes(phase.encode(domains))
    summary=dict(scope=SCOPE,language='matlab',actual_original_cases=183,actual_phase_endpoints=phase_count,
        actual_complex_gradient_coordinates_per_precision=coordinates,actual_final_states=1464,actual_QT_candidates=QT_count,
        actual_physical_QT_scalar_values_per_precision=scalars,
        actual_cases_with_fresh_phase_gradients=183 if local is None else 0,
        actual_cases_with_fresh_final_QT_physics=183 if local is None else 0,
        actual_fresh_phase_unit_domain_endpoints=phase_count,
        explicit_exact_complete_local_reference_reuse=local is not None,
        all_original_phase_final_QT_and_unit_domain_checks_pass=all(all(c[k] for k in
            ('original_phase_fields_and_stops_pass','original_final_QT_physics_pass','actual_phase_domains_pass')) for c in rows),
        actual_MP100_negative_QT_events=negative,actual_archive_payloads_byte_verified=len(manifest['files']),
        archive_SHA256=manifest['archive']['sha256'],current_independent_math_sources_SHA256=before,
        replayer_SHA256=control,original_optimizer_or_RNG_calls=0,
        every_inner_iterate_MC_author_source_agreement_dual_global_optimum_or_full_paper_pass=False,cases=rows)
    (args.output_dir/'summary.json').write_bytes(phase.encode(summary))
    print(json.dumps({k:v for k,v in summary.items() if k!='cases'}),flush=True)
    return summary


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='mode',required=True)
    b=sub.add_parser('build')
    for name in ('inventory','terminal-receipt','work-dir','packet'):b.add_argument('--'+name,type=Path,required=True)
    r=sub.add_parser('replay')
    for name in ('packet','output-dir'):r.add_argument('--'+name,type=Path,required=True)
    r.add_argument('--reuse-exact-complete-local-inventory',type=Path)
    args=p.parse_args()
    if args.mode=='build':build(args)
    elif not replay(args)['all_original_phase_final_QT_and_unit_domain_checks_pass']:raise SystemExit(1)
