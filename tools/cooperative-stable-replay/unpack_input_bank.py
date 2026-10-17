"""Restore all183 unchanged original configurations from the verified input packet."""
import argparse
import hashlib
import io
import json
from pathlib import Path,PurePosixPath
import tarfile


def sha(data):return hashlib.sha256(data).hexdigest()


def unpack(packet,output):
    if output.exists():raise FileExistsError('Preserve existing configurations and results')
    manifest=json.loads((packet/'archive-manifest.json').read_bytes());archive=packet/manifest['archive']['filename'];raw=archive.read_bytes()
    if sha(raw)!=manifest['archive']['sha256'] or len(raw)!=manifest['archive']['bytes']:raise ValueError('Actual full input archive differs')
    expected=manifest['files'];wanted={'execution-plan.json'}|{f'case-{n:03d}/configuration.json' for n in range(183)}
    if set(expected)!=wanted:raise ValueError('All183 original input slots and dispatcher required')
    payload={}
    with tarfile.open(fileobj=io.BytesIO(raw),mode='r:gz') as source:
        for member in source:
            name=member.name;path=PurePosixPath(name)
            if name not in wanted or name in payload or not member.isfile() or path.is_absolute() or '..' in path.parts or ':' in name or '\\' in name:
                raise ValueError('Unexpected or unsafe input archive member')
            data=source.extractfile(member).read();signature=expected[name]
            if len(data)!=signature['bytes'] or sha(data)!=signature['sha256']:raise ValueError('Original input file changed: '+name)
            json.loads(data);payload[name]=data
    if set(payload)!=wanted:raise ValueError('Missing original input slot')
    case_index=None
    if 'case_index' in manifest:
        index=manifest['case_index']
        if index['filename']!='original-case-index.json':raise ValueError('Unexpected case index path')
        case_index=(packet/index['filename']).read_bytes()
        if len(case_index)!=index['bytes'] or sha(case_index)!=index['sha256']:raise ValueError('Original curve/case index differs')
        labels=json.loads(case_index)['cases']
        if len(labels)!=183:raise ValueError('Every original curve association is required')
        for n,label in enumerate(labels):
            name=f'case-{n:03d}/configuration.json'
            if label['ordinal']!=n or label['configuration']!=name or label['configuration_sha256']!=expected[name]['sha256']:
                raise ValueError('Curve/case label bound to a different configuration')
            if label['full_reported_scene']!=json.loads(payload[name])['reported']:raise ValueError('Original scene label differs from exact input')
    plan=json.loads(payload['execution-plan.json'])
    assert plan['required_points']==183 and len(plan['required_schemes_per_point'])==8 and plan['required_original_moment_draws_per_successfully_completed_point']==1000
    output.mkdir(parents=True)
    for name,data in payload.items():
        p=output/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
    if case_index is not None:(output/'original-case-index.json').write_bytes(case_index)
    print(json.dumps(dict(original_configurations=183,verified_files=184+int(case_index is not None),original_config_bytes_unchanged=True,
        original_curve_labels_restored=case_index is not None,new_optimization_or_full183_pass=False)),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--packet',type=Path,required=True);p.add_argument('--output-dir',type=Path,required=True);a=p.parse_args();unpack(a.packet,a.output_dir)
