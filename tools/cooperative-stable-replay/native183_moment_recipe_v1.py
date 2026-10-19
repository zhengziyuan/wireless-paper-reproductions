"""Reconstruct/check every full native configured1000 moment group and183 aliases.

The recipe preserves complete per-draw moments and exact full-vector hashes.
MATLAB materializes all r,G,d operands using the unchanged original exporter.
Local reuse requires the same complete binary operands, never norms. This is
the configured fixed-phi moment validation, not author performance Monte Carlo.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time

import mpmath as mp
import numpy as np
import audit_moment_draws as original
import native183_evidence as transport
import phase183_evidence as phase

REPO=Path(__file__).resolve().parents[2]
SCOPE='complete-native183-configured1000-full-vector-regeneration-recipe-v1'
FIELDS=('second','fourth','independent_second','independent_fourth')


def read(path):return json.loads(path.read_bytes())
def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda:stream.read(1024*1024),b''):h.update(block)
    return h.hexdigest()
def require(condition,message):
    if not condition:raise ValueError(message)
def save(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    temporary=path.with_name(path.name+'.stage')
    temporary.write_text(json.dumps(value,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    temporary.replace(path)


def checked_file(root,name,spec):
    require(phase.safe(name),'Unsafe recipe or native member')
    path=root/name
    require(path.is_file() and path.stat().st_size==spec['bytes'] and sha(path)==spec['sha256'],
            'A complete recipe/native numerical member differs: '+name)
    return path


def validate_recipe(packet,native_packet):
    manifest=read(packet/'recipe-manifest.json')
    require(manifest['scope']==SCOPE and manifest['actual_original_cases']==183 and
            manifest['actual_exact_groups']==67,'Require the complete183 cases and67 groups')
    for name,spec in manifest['files'].items():checked_file(packet,name,spec)
    index=read(packet/'complete-native183-moment-recipe.json')
    require(index['scope']==SCOPE and [x['ordinal'] for x in index['cases']]==list(range(183)) and
            [g['ordinal'] for g in index['groups']]==list(range(67)),
            'A complete original case/group ordinal is missing or duplicated')
    source=read(native_packet/'archive-manifest.json')
    require(index['native_packet_archive_sha256']==source['archive']['sha256'] and
            sha(native_packet/'archive-manifest.json')==index['native_packet_manifest_sha256'],
            'Use the exact published full native183 input packet')
    for name,digest in index['current_math_and_export_sources_sha256'].items():
        require(phase.safe(name) and sha(REPO/name)==digest,'A native moment math/export source changed: '+name)
    signatures=set();covered=[]
    for group in index['groups']:
        require(group['input_signature'] not in signatures,'Duplicated exact native input group')
        signatures.add(group['input_signature']);dims=group['dimensions'];J,U,N,M=(dims[k] for k in ('J','U','N','M'))
        require(all(isinstance(v,int) and v>0 for v in (J,U,N,M)) and group['count']==1000,
                'Require complete original dimensions and1000 draws')
        require(group['raw_primitive_bytes']==1000*U*(2*M+J*(2*N*M+2*N+2))*8,
                'Full r,G,d and both per-link powers are required')
        meta=read(packet/group['original_native_export_index']);prior=read(packet/group['original_independent_report'])
        require(meta['count']==1000 and [meta[k] for k in ('J','U','N','M')]==[J,U,N,M] and
                meta['payload_sha256']==group['raw_primitive_sha256'] and
                prior['raw_primitive_payload_sha256']==group['raw_primitive_sha256'] and
                prior['input_signature']==group['input_signature'] and prior['all_independent_checks_pass'],
                'The original full native vector and math bindings differ')
        require(group['case_ordinals'] and group['representative_case'] in group['case_ordinals'],
                'A full native group needs its actual original representative')
        covered.extend(group['case_ordinals'])
    require(sorted(covered)==list(range(183)),'Every original case must occur in exactly one exact group')
    for case in index['cases']:
        group=index['groups'][case['group_ordinal']]
        require(case['ordinal'] in group['case_ordinals'] and case['input_signature']==group['input_signature'],
                'A native case was assigned to different exact coefficients/seed/count/source')
    return manifest,index,source


def validate_native_inputs(restored,native_manifest,index):
    """Check all complete transport members; do not rely on an old green label."""
    for name,spec in native_manifest['files'].items():checked_file(restored,name,spec)
    native=read(restored/'complete-native183-case-index.json')
    require([x['ordinal'] for x in native['cases']]==list(range(183)),'Native full input scope differs')
    results={}
    for case in index['cases']:
        n=case['ordinal'];actual=native['cases'][n]
        require(case['container']==actual['container'] and case['states']==actual['states'],
                'A native original input path differs')
        result=restored/case['container']
        require(sha(result)==case['container_sha256'] and sha(restored/case['states'])==case['states_sha256'],
                'An original native full JSON or MAT byte differs')
        document,_,dims,signature=original.input_data(result)
        require(signature==case['input_signature'] and list(dims)==[case['dimensions'][k] for k in ('J','U','N','M')],
                'Every complete actual coefficient array, shape, seed, count and source must match')
        require(document['results'][0]['monte_carlo']['count']==1000,'An original moment count differs')
        results[n]=(result,document)
    return results


def validate_operands(group,folder,packet):
    """Full binary64 operands, including every complex coordinate, are required."""
    meta=read(folder/'index.json');prior=read(packet/group['original_native_export_index'])
    require(meta==prior,'The full declared native moment export header differs')
    require(phase.safe(meta['payload']),'Unsafe native primitive path')
    raw=folder/meta['payload']
    require(raw.is_file() and raw.stat().st_size==group['raw_primitive_bytes'] and
            sha(raw)==group['raw_primitive_sha256'],'Every actual full r,G,d operand byte must match')
    return raw


def compare_draws(group,actual_file,packet):
    shape=(1000,group['dimensions']['J'],group['dimensions']['U'])
    with np.load(packet/group['original_sample_moments'],allow_pickle=False) as prior, np.load(actual_file,allow_pickle=False) as actual:
        require(set(prior.files)==set(actual.files)==set(FIELDS),'Missing or substituted complete draw arrays')
        for name in FIELDS:
            a=actual[name];b=prior[name]
            require(a.shape==b.shape==shape and a.dtype==b.dtype==np.dtype('float64') and
                    np.isfinite(a).all() and np.isfinite(b).all(),'Changed shape/dtype or nonfinite per-draw moment')
            if name in ('second','fourth'):
                require(a.tobytes(order='C')==b.tobytes(order='C'),'Original native per-draw powers differ')
            else:require(original.within(a,b),'A freshly reconstructed per-draw received-signal moment differs')


def compare_theory(actual,prior):
    with mp.workdps(110):
        for precision in ('80','100'):
            for field in ('second','fourth'):
                aa=actual['MP_expected_moments'][precision][field];bb=prior['MP_expected_moments'][precision][field]
                require(len(aa)==len(bb) and all(len(a)==len(b) for a,b in zip(aa,bb)),
                        'An independent finite-Rician moment dimension differs')
                for a,b in zip(aa,bb):
                    require(all(mp.isfinite(mp.mpf(x)) and abs(mp.mpf(x)-mp.mpf(y))<=mp.mpf('1e-40') for x,y in zip(a,b)),
                            'An independently recomputed MP80/MP100 expected moment differs')
    for field in ('second_moment_max_relative_error','fourth_moment_max_relative_error'):
        require(abs(actual[field]-prior[field])<=1e-9,'An original configured MC metric differs')


def quote(path):return "'"+str(path).replace('\\','/').replace("'","''")+"'"


def run(args):
    require(not args.output_dir.exists(),'Use a fresh full native moment replay output; preserve failed epochs')
    _,index,native_manifest=validate_recipe(args.recipe,args.native_packet)
    sources={REPO/name:digest for name,digest in index['current_math_and_export_sources_sha256'].items()}
    sources[Path(__file__).resolve()]=sha(Path(__file__).resolve())
    before={str(p):sha(p) for p in sources}
    reuse=None
    if args.reuse_exact_primitives_index:
        reuse=read(args.reuse_exact_primitives_index)
        require(reuse['scope']==SCOPE and len(reuse['groups'])==67 and
                [x['ordinal'] for x in reuse['groups']]==list(range(67)),
                'Local reuse requires all67 full exact primitive banks')
    args.output_dir.mkdir(parents=True);start=time.perf_counter()
    if args.native_restored:
        restored=args.native_restored
    else:
        _,_,restored=transport.unpack(args.native_packet,args.output_dir/'native-input-transport')
    results=validate_native_inputs(restored,native_manifest,index)
    rows=[];cases=[];values=0;primitive_coordinates=0
    for group in index['groups']:
        n=group['ordinal'];folder=args.output_dir/f'group-{n:03d}';folder.mkdir()
        case_number=group['representative_case'];result,document=results[case_number]
        require(sha(result)==read(args.recipe/group['original_native_export_index'])['source_result_sha256'],
                'Use the original representative export input')
        if reuse is not None:
            row=reuse['groups'][n]
            require(row['input_signature']==group['input_signature'],'A reusable full native group differs')
            raw=Path(row['raw_directory'])
        else:
            raw=folder/'fresh-declared-native-primitives'
            expression='restoredefaultpath;addpath('+quote(Path(__file__).parent)+');export_saved_moment_draws('+quote(REPO)+','+quote(result)+','+quote(raw)+');'
            env=dict(os.environ);prefs=folder/'matlab-preferences';prefs.mkdir();env['MATLAB_PREFDIR']=str(prefs)
            command=[str(args.matlab),*(['-wait'] if os.name=='nt' else []),'-singleCompThread','-batch',expression]
            with (folder/'actual-native-export.log').open('xb') as log:
                process=subprocess.run(command,stdout=log,stderr=subprocess.STDOUT,env=env,
                    **(dict(creationflags=subprocess.CREATE_NO_WINDOW) if os.name=='nt' else {}))
            save(folder/'actual-native-export-terminal.json',dict(actual_exit_code=process.returncode))
            require(process.returncode==0,'Retain the actual failed native full-vector export')
        payload=validate_operands(group,raw,args.recipe)
        report=original.audit(result,raw,folder/'fresh-independent')
        require(report['all_independent_checks_pass'],'Retain a failed full-vector physical moment check')
        prior=read(args.recipe/group['original_independent_report']);compare_theory(report,prior)
        compare_draws(group,folder/'fresh-independent/all1000_native_sample_moments.npz',args.recipe)
        require(sha(payload)==group['raw_primitive_sha256'] and
                sha(result)==index['cases'][case_number]['container_sha256'] and
                sha(restored/index['cases'][case_number]['states'])==index['cases'][case_number]['states_sha256'],
                'A complete native input/vector changed during fresh evaluation')
        for ordinal in group['case_ordinals']:
            _,other=results[ordinal];metrics=other['results'][0]['monte_carlo']
            require(metrics['count']==1000 and all(abs(metrics[key]-report[key])<=1e-9 for key in
                    ('second_moment_max_relative_error','fourth_moment_max_relative_error')),
                    'An actual native case MC metric differs from its exact coefficient group')
            cases.append(dict(ordinal=ordinal,group_ordinal=n,full_exact_input_and_saved_MC_fields_pass=True))
        J,U,N,M=(group['dimensions'][k] for k in ('J','U','N','M'))
        values+=2*1000*J*U;primitive_coordinates+=1000*U*(M+J*(N*M+N))
        require(all(sha(Path(p))==h for p,h in before.items()),'A native moment source changed during replay')
        rows.append(dict(ordinal=n,passed=True,actual_full_primitive_sha256=sha(payload),actual_full_primitive_bytes=payload.stat().st_size,
            actual_full_vector_stream_freshly_regenerated=reuse is None,
            actual_independent_full_draw_checks_freshly_recomputed=True,
            actual_independent_report_sha256=sha(folder/'fresh-independent/summary.json'),
            actual_original_sample_archive_sha256=sha(args.recipe/group['original_sample_moments'])))
        summary=dict(scope=SCOPE,actual_original_cases=len(cases),actual_exact_groups=len(rows),
            actual_distinct_configured_draws=1000*len(rows),actual_per_case_configured_draws=1000*len(cases),
            actual_complete_complex_primitive_coordinates=primitive_coordinates,actual_per_draw_second_fourth_values=values,
            actual_full_primitive_bytes=sum(x['actual_full_primitive_bytes'] for x in rows),
            actual_groups_with_fresh_native_vector_regeneration=sum(x['actual_full_vector_stream_freshly_regenerated'] for x in rows),
            actual_groups_with_fresh_independent_full_draw_and_MP80_MP100_checks=len(rows),
            all67_full_vectors_and_all183_saved_configured_MC_checks_pass=len(rows)==67 and len(cases)==183,
            original_optimization_calls=0,configured1000_is_author_optimized_performance_MC=False,
            original_historical_callback_buffers_recovered=False,dual_language_curve_original_reference_or_full_paper_pass=False,
            source_before=before,source_after={str(p):sha(p) for p in sources},
            elapsed_seconds=time.perf_counter()-start,groups=rows,cases=sorted(cases,key=lambda c:c['ordinal']))
        save(args.output_dir/'progress.json',summary)
        print(json.dumps({k:summary[k] for k in ('actual_original_cases','actual_exact_groups','actual_full_primitive_bytes','actual_groups_with_fresh_native_vector_regeneration')}),flush=True)
    require([x['ordinal'] for x in summary['cases']]==list(range(183)) and summary['source_before']==summary['source_after'],
            'Full native scope/source closure failed')
    validate_recipe(args.recipe,args.native_packet)
    save(args.output_dir/'summary.json',summary)
    return summary


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--recipe',type=Path,required=True)
    parser.add_argument('--native-packet',type=Path,required=True)
    parser.add_argument('--native-restored',type=Path)
    parser.add_argument('--output-dir',type=Path,required=True)
    mode=parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--matlab',type=Path)
    mode.add_argument('--reuse-exact-primitives-index',type=Path)
    arguments=parser.parse_args()
    if not run(arguments)['all67_full_vectors_and_all183_saved_configured_MC_checks_pass']:raise SystemExit(1)
