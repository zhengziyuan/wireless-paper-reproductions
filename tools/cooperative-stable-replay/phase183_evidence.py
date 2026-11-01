"""Transport/replay every selected original Python183 phase endpoint.

Default replay freshly evaluates the complete183-case population at MP80/100.
Explicit local reuse requires the exact closed progress file, every original
complete reference and actual input byte, and unchanged current math sources.
"""
import argparse
from decimal import Decimal, InvalidOperation, localcontext
import gzip
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import tarfile
import zipfile

import audit_native_phase_mp as math_reader
import audit_native_case as layout
import mp_phase_reference as reference


def require(value, message):
    if not value:
        raise ValueError(message)


def read(path):
    return json.loads(path.read_bytes())


def encode(value):
    return (json.dumps(value, indent=2, allow_nan=False)+'\n').encode()


def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda:stream.read(1024*1024), b''):
            h.update(block)
    return h.hexdigest()


def safe(name):
    p=PurePosixPath(name)
    return bool(name) and not p.is_absolute() and '..' not in p.parts and '\\' not in name and ':' not in name


def sources():
    return {Path(m.__file__).name:sha(Path(m.__file__)) for m in (math_reader, layout, reference)}


def complete(progress):
    require(progress['expected_original_cases']==183 and progress['finished_cases']==183 and
            len(progress['records'])==183 and sorted(r['ordinal'] for r in progress['records'])==list(range(183)),
            'Every original selected0..182 case is required')
    require(progress['passed_phase_cases']==sum(r['phase_checks_pass'] for r in progress['records']) and
            progress['retained_failed_phase_cases']==sum(not r['phase_checks_pass'] for r in progress['records']),
            'Preserve every actual positive or failed original phase outcome')


def input_binding(container, matrix):
    return dict(result=sha(container), states=sha(matrix),
                auditor=sha(Path(math_reader.__file__)), reference=sha(Path(reference.__file__)))


def build(args):
    require(not args.packet.exists() and not args.work_dir.exists(), 'Preserve previous packet/work epochs')
    progress=read(args.progress);complete(progress)
    closure=read(args.terminal_receipt)
    require(closure['status']=='actual_scientific_child_returned' and closure['actual_child_terminal_exit_code']==0 and
            closure['all_watched_source_and_job_bytes_unchanged'] and closure['source_before']==closure['source_after'],
            'An actual natural terminal0/source closure is required')
    for path,digest in progress['source_before'].items():
        require(sha(Path(path))==digest, 'A closed coordinator/independent source changed')
    before=sources();control_before=sha(Path(__file__))
    repo=Path(__file__).resolve().parents[2]
    case_index_path=repo/'strict/validation/cooperative-original183-inputs-20261017/original-case-index.json'
    identities={x['ordinal']:x for x in read(case_index_path)['cases']}
    require(sorted(identities)==list(range(183)), 'Every exact original source-index slot is required')
    original_bank=repo.parent/'work/full-paper-banks/cooperative-v4-recording183-PREPARED-20261004-v1'
    args.work_dir.mkdir(parents=True)
    payload={};cases=[];phase_total=coordinates=0
    def add(name,path):
        require(safe(name) and name not in payload, 'Unsafe/duplicate numerical payload')
        payload[name]=dict(path=Path(path),bytes=Path(path).stat().st_size,sha256=sha(Path(path)))
    add('actual-complete-selected183-progress.json',args.progress)
    add('actual-original183-source-case-index.json',case_index_path)
    terminal=dict(actual_phase_controller_natural_exit_code=0,actual_owner=closure['owner'],
        actual_child=closure['child'],all_controller_and_job_source_bytes_unchanged=True,
        actual_original_phase_cases=183,original_optimizer_or_RNG_calls=0,
        exact_private_terminal_receipt_SHA256=sha(args.terminal_receipt),
        original_QT_MC_outer_source_curve_or_full_paper_pass=False)
    terminal_path=args.work_dir/'actual-phase-terminal-closure.json';terminal_path.write_bytes(encode(terminal))
    add('actual-phase-terminal-closure.json',terminal_path)
    for record in sorted(progress['records'],key=lambda r:r['ordinal']):
        n=record['ordinal'];container=Path(record['container']);document=read(container)
        matrix=container.parent/document['state_recording']['filename'];folder=Path(record['phase_dir'])
        summary=read(folder/'summary.json');binding=input_binding(container,matrix)
        original_case=original_bank/f'case-{n:03d}'
        require(document['configuration']==read(original_case/'configuration.json'),
                'Every actual selected phase configuration must equal its original full source case')
        identity=identities[n]['full_reported_scene']
        require(summary['dimensions']=={k:identity[k] for k in ('J','U','N','M')},
                'No reported scene dimension may be reduced or substituted')
        for name,digest in record['source_origin_SHA256'].items():
            path=Path(name)
            if not path.is_absolute():path=original_case/name
            require(sha(path)==digest, 'A selected original source/input byte changed')
        require(sha(container)==record['container_SHA256'] and sha(folder/'summary.json')==record['phase_summary_SHA256'] and
                summary['source_input_sha256']==binding and summary['source_and_input_unchanged'],
                'Every exact original input and current independent math byte must match')
        count=summary['stages'];require(count==record['actual_phase_endpoints']==document['state_recording']['phase_endpoints'] and
            len(summary['phase_summaries'])==count and count>0, 'Every actual original endpoint is required')
        prefix=f'case-{n:03d}';container_name=prefix+'/'+container.name;matrix_name=prefix+'/'+matrix.name
        add(container_name,container);add(matrix_name,matrix)
        receipts=[]
        for name in ('actual-lossless-phase-adapter-receipt.json','actual-byte-level-roundtrip-verification.json',
                     'actual-additional-byte-level-roundtrip-verification.json'):
            path=container.parent/name
            if path.exists():
                public_name=prefix+'/serialization/'+name;add(public_name,path)
                receipts.append(dict(file=public_name,sha256=sha(path)))
        members=[];bundle=args.work_dir/f'case-{n:03d}-complete-original-phase-references.zip'
        files=['summary.json']+[f'phase-{i:03d}.json' for i in range(count)]
        with zipfile.ZipFile(bundle,'x',compression=zipfile.ZIP_STORED) as archive:
            for name in files:
                path=folder/name;raw=path.read_bytes();doc=json.loads(raw)
                if name!='summary.json':
                    require(doc['index']==len(members)-1 and set(doc['lanes'])=={'80','100'},
                            'A complete original precision lane or endpoint is missing')
                    require(doc['passed']==summary['phase_summaries'][doc['index']]['passed'],
                            'Preserve the actual original positive/failed phase result')
                info=zipfile.ZipInfo(name,(1980,1,1,0,0,0));info.external_attr=0o100644<<16
                archive.writestr(info,raw)
                members.append(dict(file=name,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest()))
        bundle_name=prefix+'/complete-original-phase-references.zip';add(bundle_name,bundle)
        cases.append(dict(ordinal=n,container=container_name,states=matrix_name,phase_bundle=bundle_name,
            input_binding=binding,actual_phase_endpoints=count,
            actual_complex_gradient_coordinates_per_precision=summary['complex_coordinates_per_lane'],
            original_phase_checks_pass=summary['all_MP_fields_original_stop_and_precision_checks_pass'],
            actual_reported_scene_dimensions=summary['dimensions'],
            selected_original_Python_epoch=record['selected_Python_epoch'],
            original_source_origin_SHA256=record['source_origin_SHA256'],reference_members=members,
            actual_lossless_serialization_receipts=receipts))
        phase_total+=count;coordinates+=summary['complex_coordinates_per_lane']
        if len(cases)%12==0:
            print(json.dumps(dict(actual_complete_phase_cases_bound=len(cases),expected=183,
                                  actual_original_phase_endpoints=phase_total)),flush=True)
    require(phase_total==progress['actual_selected_phase_endpoints_closed'] and
            coordinates==progress['actual_selected_complex_gradient_coordinates_per_precision'], 'Complete original totals differ')
    index=dict(case_scope='selected-Python183-phase',language='python',exact_original_ordinals=list(range(183)),
        original_cases=183,actual_phase_endpoints=phase_total,complex_gradient_coordinates_per_precision=coordinates,
        current_math_sources_SHA256=before,cases=cases,exact_complete_progress_SHA256=sha(args.progress),
        original_source_case_index_SHA256=sha(case_index_path),
        original_phase_threshold='1e-6',field_comparison='1e-9+1e-10*abs(reference)',precision_absolute_bound='1e-40',
        all_actual_phase_fields_stops_and_precision_pass=progress['all183_selected_Python_phase_fields_and_original_stops_pass'],
        old056_065_failed_epochs_remain_separate_from_selected_new_epochs=True,
        every_original_inner_iterate_QT_MC_outer_source_curve_or_full_paper_pass=False)
    index_path=args.work_dir/'complete-phase-case-index.json';index_path.write_bytes(encode(index))
    add('complete-phase-case-index.json',index_path)
    archive_path=args.work_dir/'selected-Python183-complete-phase-inputs-and-references.tar.gz'
    with archive_path.open('xb') as raw:
        with gzip.GzipFile(fileobj=raw,mode='wb',filename='',mtime=0) as compressed:
            with tarfile.open(fileobj=compressed,mode='w|') as archive:
                for name,spec in sorted(payload.items()):
                    require(sha(spec['path'])==spec['sha256'], 'A sealed numerical input changed')
                    entry=tarfile.TarInfo(name);entry.size=spec['bytes'];entry.mode=0o644;entry.mtime=0
                    with spec['path'].open('rb') as stream:archive.addfile(entry,stream)
    require(sources()==before and sha(Path(__file__))==control_before, 'An active math/transport source changed')
    args.packet.mkdir(parents=True);parts=[]
    with archive_path.open('rb') as stream:
        for n,raw in enumerate(iter(lambda:stream.read(512*1024),b'')):
            name=archive_path.name+f'.part{n:03d}';(args.packet/name).write_bytes(raw)
            parts.append(dict(file=name,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest()))
    manifest=dict(case_scope=index['case_scope'],language='python',exact_original_ordinals=list(range(183)),
        original_cases=183,actual_phase_endpoints=phase_total,complex_gradient_coordinates_per_precision=coordinates,
        archive=dict(filename=archive_path.name,bytes=archive_path.stat().st_size,sha256=sha(archive_path),parts=parts),
        files={n:{k:s[k] for k in ('bytes','sha256')} for n,s in payload.items()},
        all_actual_phase_fields_stops_and_precision_pass=index['all_actual_phase_fields_stops_and_precision_pass'],
        packager_SHA256=control_before,
        original_optimizer_or_RNG_calls=0,original_QT_MC_outer_source_curve_or_full_paper_pass=False)
    (args.packet/'archive-manifest.json').write_bytes(encode(manifest))
    summary={k:v for k,v in index.items() if k!='cases'}
    (args.packet/'complete-phase-scope-summary.json').write_bytes(encode(summary))
    print(json.dumps(dict(actual_cases=183,phase_endpoints=phase_total,coordinates_per_precision=coordinates,
        archive_bytes=manifest['archive']['bytes'],archive_SHA256=manifest['archive']['sha256'],
        parts=len(parts),actual_payloads=len(payload))),flush=True)


def unpack(packet,output):
    require(not output.exists(), 'Use a fresh restored numerical destination')
    manifest=read(packet/'archive-manifest.json')
    require(manifest['case_scope']=='selected-Python183-phase' and manifest['language']=='python' and
            manifest['original_cases']==183 and manifest['exact_original_ordinals']==list(range(183)),
            'Require the complete selected original Python183 scope')
    archive=manifest['archive'];require(safe(archive['filename']) and archive['parts'], 'Safe complete numerical archive required')
    output.mkdir(parents=True);transport=output/'verified-complete-numerical-transport.tar.gz';digest=hashlib.sha256();length=0
    with transport.open('xb') as stream:
        for n,part in enumerate(archive['parts']):
            require(part['file']==archive['filename']+f'.part{n:03d}' and safe(part['file']), 'Unsafe or missing archive part')
            raw=(packet/part['file']).read_bytes()
            require(len(raw)==part['bytes'] and hashlib.sha256(raw).hexdigest()==part['sha256'], 'Actual archive part differs')
            stream.write(raw);digest.update(raw);length+=len(raw)
    require(length==archive['bytes'] and digest.hexdigest()==archive['sha256'], 'Whole archive differs')
    restored=output/'restored';restored.mkdir();found=set()
    with tarfile.open(transport,'r|gz') as source:
        for member in source:
            name=member.name
            require(safe(name) and member.isfile() and name in manifest['files'] and name not in found,
                    'Unsafe, duplicated or unlisted actual payload')
            wanted=manifest['files'][name];require(member.size==wanted['bytes'], 'Actual member size differs')
            target=restored/name;target.parent.mkdir(parents=True,exist_ok=True);h=hashlib.sha256()
            with target.open('xb') as stream:
                original=source.extractfile(member)
                for raw in iter(lambda:original.read(1024*1024),b''):stream.write(raw);h.update(raw)
            require(h.hexdigest()==wanted['sha256'], 'Actual numerical member differs');found.add(name)
    require(found==set(manifest['files']), 'A complete numerical payload is missing')
    index=read(restored/'complete-phase-case-index.json')
    require(index['original_cases']==183 and index['exact_original_ordinals']==list(range(183)) and
            [c['ordinal'] for c in index['cases']]==list(range(183)) and index['current_math_sources_SHA256']==sources(),
            'Every original case and exact current math source is required')
    for case in index['cases']:
        folder=restored/f"case-{case['ordinal']:03d}"/'original-complete-phase-reference'
        folder.mkdir();specs={x['file']:x for x in case['reference_members']}
        expected={'summary.json'}|{f'phase-{i:03d}.json' for i in range(case['actual_phase_endpoints'])}
        require(set(specs)==expected, 'Missing complete original phase reference')
        with zipfile.ZipFile(restored/case['phase_bundle']) as source:
            require(set(source.namelist())==expected and len(source.namelist())==len(expected), 'Missing/duplicate original phase member')
            for name in source.namelist():
                require(safe(name) and '/' not in name and not source.getinfo(name).is_dir(), 'Unsafe original reference name')
                raw=source.read(name);wanted=specs[name]
                require(len(raw)==wanted['bytes'] and hashlib.sha256(raw).hexdigest()==wanted['sha256'], 'Original reference bytes differ')
                (folder/name).write_bytes(raw)
    return manifest,index,restored


def equivalent(a,b):
    if type(a) is not type(b):return False
    if isinstance(a,dict):return a.keys()==b.keys() and all(equivalent(a[k],b[k]) for k in a)
    if isinstance(a,list):return len(a)==len(b) and all(equivalent(x,y) for x,y in zip(a,b))
    if a==b:return True
    if isinstance(a,str):
        try:
            with localcontext() as context:
                context.prec=130;x,y=Decimal(a),Decimal(b)
                return x.is_finite() and y.is_finite() and abs(x-y)<=Decimal('1e-40')
        except InvalidOperation:return False
    return False


def replay(args):
    control_before=sha(Path(__file__))
    require(not args.output_dir.exists(), 'Preserve previous replay')
    manifest,index,restored=unpack(args.packet,args.output_dir)
    reuse=args.reuse_exact_complete_local_progress
    local=None
    if reuse is not None:
        require(sha(reuse)==index['exact_complete_progress_SHA256']==sha(restored/'actual-complete-selected183-progress.json'),
                'Local reuse requires the exact actual complete183 progress')
        progress=read(reuse);complete(progress);local={r['ordinal']:r for r in progress['records']}
    phase_total=coordinates=0;rows=[]
    for case in index['cases']:
        n=case['ordinal'];container=restored/case['container'];matrix=restored/case['states']
        expected=input_binding(container,matrix)
        require(expected==case['input_binding'], 'Actual original state/code bytes differ')
        stored=restored/f'case-{n:03d}'/'original-complete-phase-reference';prior=read(stored/'summary.json')
        require(prior['source_input_sha256']==expected and prior['stages']==case['actual_phase_endpoints'],
                'Archived reference has different complete original inputs')
        if local is not None:
            old=local[n];folder=Path(old['phase_dir']);original_container=Path(old['container'])
            require(original_container.resolve().is_relative_to(reuse.parent.parent.resolve()) and
                    folder.resolve().is_relative_to(reuse.parent.parent.resolve()), 'Only the explicitly selected local completed bank may be read')
            original_matrix=original_container.parent/read(original_container)['state_recording']['filename']
            require(input_binding(original_container,original_matrix)==expected and sha(folder/'summary.json')==old['phase_summary_SHA256'],
                    'Complete local original input/reference differs')
            for member in case['reference_members']:
                require(sha(folder/member['file'])==member['sha256'], 'A local complete phase reference changed')
            actual=prior;fresh=None
        else:
            fresh=args.output_dir/f'fresh-case-{n:03d}-MP80-MP100'
            actual=math_reader.audit(container,fresh)
        require(actual['source_input_sha256']==expected and actual['source_and_input_unchanged'] and
                actual['stages']==case['actual_phase_endpoints'] and
                actual['complex_coordinates_per_lane']==case['actual_complex_gradient_coordinates_per_precision'] and
                actual['all_MP_fields_original_stop_and_precision_checks_pass']==case['original_phase_checks_pass'],
                'Fresh complete input/count/original-stop result differs')
        for i in range(case['actual_phase_endpoints']):
            reference_row=read(stored/f'phase-{i:03d}.json')
            if fresh is not None:require(equivalent(read(fresh/f'phase-{i:03d}.json'),reference_row), 'A fresh original gradient, criterion or stop differs')
        phase_total+=actual['stages'];coordinates+=actual['complex_coordinates_per_lane']
        rows.append(dict(ordinal=n,actual_original_phase_endpoints=actual['stages'],
            complex_coordinates_per_precision=actual['complex_coordinates_per_lane'],
            original_fields_stops_and_precision_pass=actual['all_MP_fields_original_stop_and_precision_checks_pass']))
        print(json.dumps(dict(complete_original_cases=len(rows),expected=183,phase_endpoints=phase_total)),flush=True)
    require(phase_total==index['actual_phase_endpoints'] and coordinates==index['complex_gradient_coordinates_per_precision'],
            'Every complete original endpoint and gradient coordinate is required')
    require(sha(Path(__file__))==control_before and sources()==index['current_math_sources_SHA256'],
            'An active replay or independent math source changed')
    summary=dict(actual_original_cases=183,actual_original_phase_endpoints=phase_total,
        actual_complex_gradient_coordinates_per_precision=coordinates,
        actual_cases_freshly_recomputed=0 if local is not None else 183,
        exact_complete_local_references_reused_after_all_actual_input_and_math_hashes_match=local is not None,
        actual_archive_payloads_byte_verified=len(manifest['files']),all_actual_MP80_MP100_values_and_original_stops_match=True,
        all_original_phase_fields_stops_and_precision_pass=all(r['original_fields_stops_and_precision_pass'] for r in rows),
        old_failed_epochs_or_other_QT_MC_outer_source_reference_or_full_paper_promoted=False,
        original_optimizer_or_RNG_calls=0,archive_SHA256=manifest['archive']['sha256'],cases=rows)
    summary.update(replayer_SHA256=control_before,current_math_sources_SHA256=sources())
    (args.output_dir/'summary.json').write_bytes(encode(summary))
    print(json.dumps({k:v for k,v in summary.items() if k!='cases'}),flush=True)
    return summary


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='mode',required=True)
    b=sub.add_parser('build')
    for name in ('progress','terminal-receipt','work-dir','packet'):b.add_argument('--'+name,type=Path,required=True)
    r=sub.add_parser('replay')
    for name in ('packet','output-dir'):r.add_argument('--'+name,type=Path,required=True)
    r.add_argument('--reuse-exact-complete-local-progress',type=Path)
    a=p.parse_args();build(a) if a.mode=='build' else replay(a)
