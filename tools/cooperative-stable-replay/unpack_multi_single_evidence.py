"""Restore exactly72 paired source cases,1152 endpoints and144 source ordinates."""
import argparse
import io
import json
from pathlib import Path
import tarfile

from build_power_curve_views import NAMES
from unpack_power_evidence import digest, safe


def unpack(packet, output):
    if output.exists():
        raise FileExistsError('Preserve previous output; use a fresh directory')
    manifest = json.loads((packet/'archive-manifest.json').read_bytes())
    wanted = dict(case_scope='multi-single',languages=['python','matlab'],cases_per_language=72,
        schemes_per_case=8,total_final_states=1152,physical_scalar_fields_per_precision=7680,
        exact_original_case_ordinals=list(range(111,183)),original_source_figures=[11],
        original_reference_ordinates_per_language=144)
    if any(manifest.get(k)!=v for k,v in wanted.items()):
        raise ValueError('Every original72 slot,1152 state and144 source-point identity is required')
    if manifest.get('source_W_versus_normalized_I_over_N_conflict_unresolved') is not True:
        raise ValueError('Preserve the unresolved printed W versus supplied normalized I/N scope')
    spec = manifest['archive']
    if not safe(spec['filename']) or not spec['parts']:
        raise ValueError('Unsafe or missing complete archive')
    chunks=[]
    for n,part in enumerate(spec['parts']):
        if not safe(part['file']) or part['file']!=spec['filename']+f'.part{n:03d}':
            raise ValueError('Unexpected or unsafe archive part')
        raw=(packet/part['file']).read_bytes()
        if len(raw)!=part['bytes'] or digest(raw)!=part['sha256']:
            raise ValueError('Archive part changed')
        chunks.append(raw)
    raw=b''.join(chunks)
    if len(raw)!=spec['bytes'] or digest(raw)!=spec['sha256']:
        raise ValueError('Whole numerical archive differs')
    files={}
    with tarfile.open(fileobj=io.BytesIO(raw),mode='r:gz') as archive:
        for member in archive:
            name=member.name
            if not safe(name) or not member.isfile() or name in files or name not in manifest['files']:
                raise ValueError('Unsafe, duplicated or unlisted archive member')
            payload=archive.extractfile(member).read()
            expected=manifest['files'][name]
            if len(payload)!=expected['bytes'] or digest(payload)!=expected['sha256']:
                raise ValueError('Actual payload differs')
            files[name]=payload
    if set(files)!=set(manifest['files']):
        raise ValueError('Missing actual payload')
    index=json.loads(files['final-state-index.json'])
    if (index.get('case_scope'),index.get('expected_case_ordinals'),index.get('original_source_figures'))!=(
            'multi-single',list(range(111,183)),[11]):
        raise ValueError('Restored original cohort differs')
    if index['array_bank_sha256']!=digest(files['final-states.npz']):
        raise ValueError('Final-array input binding differs')
    for language in ('python','matlab'):
        cases=[c for c in index['cases'] if c['language']==language]
        if sorted(c['ordinal'] for c in cases)!=list(range(111,183)) or any(
                [s['scheme'] for s in c['final_states']]!=list(NAMES) for c in cases):
            raise ValueError('A complete original source slot or scheme is missing/duplicated')
    output.mkdir(parents=True)
    for name,payload in files.items():
        path=output/name
        path.parent.mkdir(parents=True,exist_ok=True)
        path.write_bytes(payload)
    summary=dict(actual_payloads_verified=len(files),cases_per_language=72,actual_final_states=1152,
        physical_scalar_fields_per_precision=7680,original_reference_ordinates_per_language=144,
        source_W_versus_normalized_I_over_N_conflict_unresolved=True,
        archive_SHA256=spec['sha256'],optimizer_or_RNG_calls=0,
        archive_restoration_is_new_mathematical_or_original_reference_or_paper_certification=False)
    print(summary,flush=True)
    return summary


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--packet',type=Path,required=True)
    p.add_argument('--output-dir',type=Path,required=True)
    a=p.parse_args();unpack(a.packet,a.output_dir)
