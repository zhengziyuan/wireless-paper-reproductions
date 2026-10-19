"""Restore all original MC vectors and independently check every exact group.

Default freshly evaluates all67 complete1000-draw groups. Explicit local-bank
reuse requires the actual complete183-case closure, byte-identical reports,
unchanged reference sources and exact numerical input/sample signatures.
"""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import tarfile

import numpy as np

from audit_historical_python_moment_stream import canonical,load_case,evaluate
from audit_native_case import sha
from build_power_curve_views import read,require,write
from unpack_power_evidence import safe


def unpack(packet,output):
    require(not output.exists(),'Preserve previous restored data')
    manifest=read(packet/'archive-manifest.json')
    require(manifest['case_scope']=='historical-Python183-channel-moment-streams' and
            manifest['original_case_ordinals']==list(range(183)) and manifest['language']=='python' and
            manifest['actual_original_cases']==183 and manifest['configured_draws_per_case']==1000 and
            manifest['unique_exact_physical_groups']==67 and
            manifest['full_original1000_channel_vectors_included_for_every_exact_group'] is True,
            'Every original source slot, complete1000-channel stream and exact group is required')
    spec=manifest['archive'];require(safe(spec['filename']) and spec['parts'],'Safe complete archive required')
    output.mkdir(parents=True)
    archive_path=output/'verified-source-archive.tar.gz';h=hashlib.sha256();size=0
    with archive_path.open('wb') as stream:
        for i,part in enumerate(spec['parts']):
            require(safe(part['file']) and part['file']==spec['filename']+f'.part{i:03d}',
                    'Unsafe or reordered archive part')
            raw=(packet/part['file']).read_bytes()
            require(len(raw)==part['bytes'] and hashlib.sha256(raw).hexdigest()==part['sha256'],'Archive part differs')
            stream.write(raw);h.update(raw);size+=len(raw)
    require(size==spec['bytes'] and h.hexdigest()==spec['sha256'],'Whole original numerical archive differs')
    restored=output/'payloads';restored.mkdir();seen=set()
    with tarfile.open(archive_path,'r:gz') as archive:
        for member in archive:
            name=member.name
            require(safe(name) and member.isfile() and name not in seen and name in manifest['files'],
                    'Unsafe, duplicated or unlisted original payload')
            expected=manifest['files'][name]
            require(member.size==expected['bytes'],'Payload size differs')
            raw=archive.extractfile(member).read()
            require(hashlib.sha256(raw).hexdigest()==expected['sha256'],'Original numerical payload differs')
            path=restored/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(raw);seen.add(name)
    require(seen==set(manifest['files']),'Missing original numerical payload')
    return restored,manifest


def run(args):
    require(not args.output_dir.exists(),'Use a fresh public replay destination')
    tools=Path(__file__).resolve().parent
    reference=tools/'mp_phase_reference.py';auditor=tools/'audit_historical_python_moment_stream.py'
    watch={str(p):sha(p) for p in (Path(__file__),auditor,reference,tools/'unpack_power_evidence.py')}
    restored,manifest=unpack(args.packet,args.output_dir)
    index=tools.parents[1]/'strict/validation/cooperative-original183-inputs-20261017/original-case-index.json'
    require(sha(index)==manifest['source_case_index_SHA256'],'Original complete source-case index differs')
    closed=read(restored/'actual-complete-original-moment-audit-progress.json')
    require(closed['finished_cases']==closed['passed_moment_cases']==183 and
            closed['all183_actual_historical_moment_stream_checks_pass'] and len(closed['groups'])==67 and
            sha(restored/'actual-complete-original-moment-audit-progress.json')==manifest['original_complete_MC_progress_SHA256'],
            'Actual complete reference closure must be retained')
    reused=args.reuse_exact_complete_local_reference_bank is not None
    local=None
    if reused:
        require(sha(args.reuse_exact_complete_local_reference_bank)==manifest['original_complete_MC_progress_SHA256'],
                'Reuse requires the exact actual complete183-case local closure')
        local=read(args.reuse_exact_complete_local_reference_bank)
        require(all(Path(p).is_file() and sha(Path(p))==digest for p,digest in local['source_before'].items()),
                'Every declared actual local reference source must still match')
    groups=read(restored/'all67-exact-physical-groups.json')
    require(len(groups)==67 and len({g['input_signature'] for g in groups})==67,'Every exact complete group required')
    facts={};fresh=0;maximum_sample_error=0.
    for g in groups:
        signature=g['input_signature'];relative=g['relative_directory']
        require(relative=='groups/'+signature and len(signature)==64 and all(c in '0123456789abcdef' for c in signature),
                'Safe exact group identity required')
        folder=restored/relative;loaded=load_case(folder)
        prior_path=folder/'original-complete-reference.json';prior=read(prior_path)
        require(sha(prior_path)==g['original_complete_reference_SHA256'] and
                loaded['input_signature']==prior['input_signature']==signature and
                loaded['actual_sample_bank_SHA256']==prior['actual_sample_bank_SHA256']==g['actual_sample_bank_SHA256'] and
                canonical(loaded['RNG_before'])==canonical(prior['recorded_RNG_before']) and
                canonical(loaded['RNG_after'])==canonical(prior['recorded_RNG_after']) and
                prior['all_independent_moment_stream_checks_pass'],
                'Every original numerical input/channel/RNG signature must match its complete reference')
        math_sources={name.replace('\\','/').split('/')[-1]:digest for name,digest in prior['independent_auditor_and_reference_SHA256'].items()}
        require(math_sources=={auditor.name:sha(auditor),reference.name:sha(reference)},
                'Current independent reference sources differ from the actual complete report')
        if reused:
            p=Path(local['groups'][signature]['report'])
            require(p.is_file() and sha(p)==sha(prior_path)==local['groups'][signature]['report_SHA256'],
                    'Reuse requires each exact full local1000-draw report')
            actual=prior
        else:
            report_path=args.output_dir/'fresh-reference-groups'/(signature+'.json')
            report_path.parent.mkdir(exist_ok=True)
            actual=evaluate(loaded,report_path);fresh+=1
        require(actual['all_independent_moment_stream_checks_pass'] and actual['actual_original_draws']==1000,
                'An actual complete independent group failed')
        require(abs(actual['second_moment_max_relative_error']-prior['second_moment_max_relative_error'])<=1e-9 and
                abs(actual['fourth_moment_max_relative_error']-prior['fourth_moment_max_relative_error'])<=1e-9,
                'Fresh original moment error metrics differ')
        maximum_sample_error=max(maximum_sample_error,actual['maximum_complex_sample_error'])
        facts[signature]=dict(dimensions=loaded['dimensions'],RNG_before=loaded['RNG_before'],
            actual_sample_bank_SHA256=loaded['actual_sample_bank_SHA256'],
            second_error=actual['second_moment_max_relative_error'],fourth_error=actual['fourth_moment_max_relative_error'])
    mapping=read(restored/'all183-exact-source-case-mapping.json')
    require([r['ordinal'] for r in mapping]==list(range(183)),'No source case may be missing, duplicated or selected as a survivor')
    identities={c['ordinal']:c for c in read(index)['cases']};coordinates=0
    for row in mapping:
        n=row['ordinal'];fact=facts[row['input_signature']];configuration=row['original_configuration']
        require(row['source_identity']==identities[n] and row['actual_original_draws']==1000 and
                row['actual_sample_bank_SHA256']==fact['actual_sample_bank_SHA256'] and
                all(row['actual_closed_checks'].values()),'Every actual complete-case channel stream must remain bound')
        require(tuple(int(configuration['reported'][k]) for k in ('J','U','N','M'))==fact['dimensions'],
                'An original alias differs in physical dimensions')
        seed=configuration['tuned_not_reported']['seed']
        require(float(seed)==int(seed) and canonical(np.random.PCG64(int(seed)).state)==canonical(fact['RNG_before']),
                'Each original configured seed must produce the actual saved before state')
        mc=row['original_reported_MC']
        require(mc['count']==1000 and abs(mc['second_moment_max_relative_error']-fact['second_error'])<=1e-9 and
                abs(mc['fourth_moment_max_relative_error']-fact['fourth_error'])<=1e-9,
                'An original reported moment metric differs from its exact complete stream')
        coordinates+=1000*np.prod(fact['dimensions'][:3])
    require(int(coordinates)==manifest['actual_complex_channel_coordinates_covered']==17568000,
            'Every actual original complex channel coordinate must be represented')
    require(watch=={p:sha(Path(p)) for p in watch},'An active public reference/reader changed')
    summary=dict(actual_payloads_byte_verified=len(manifest['files']),actual_original_cases=183,
        configured_draws_per_case=1000,exact_complete_physical_groups=67,actual_original_draw_rows_covered=183000,
        actual_original_complex_channel_coordinates_covered=int(coordinates),
        every_unique_original1000_channel_vector_bank_present_and_verified=True,
        actual_groups_freshly_evaluated=fresh,actual_independent_reference_RNG_replay_realizations=fresh*1000,
        actual_complete_local_references_reused_after_exact_input_sample_and_source_bindings=reused,
        every_original_seed_after_state_and_reported_error_metric_matches=True,
        maximum_independent_complex_sample_error=maximum_sample_error,
        archive_SHA256=manifest['archive']['sha256'],new_original_optimizer_or_production_RNG_calls=0,
        extra_optimized_performance_MC_populations=0,author_reported_MC_count_recovered=False,
        original_phase_QT_GEO_GT_histories_or_reference_or_full_paper_pass=False,replayer_SHA256=sha(Path(__file__)))
    write(args.output_dir/'summary.json',summary);print(summary,flush=True)
    return summary


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--packet',type=Path,required=True)
    p.add_argument('--output-dir',type=Path,required=True)
    p.add_argument('--reuse-exact-complete-local-reference-bank',type=Path,
        help='Actual complete183-case local progress.json, with all exact reports and reference source files still present.')
    run(p.parse_args())
