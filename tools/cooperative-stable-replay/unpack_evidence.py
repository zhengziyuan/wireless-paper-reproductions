"""Verify a declared immutable cooperative archive and every complete payload."""
import argparse
import hashlib
import io
import json
from pathlib import Path,PurePosixPath
import tarfile


def unpack(archive,output,expected_sha):
    if archive.exists():payload=archive.read_bytes()
    else:
        split=json.loads(archive.with_name(archive.name+'.parts.json').read_bytes())
        if split['archive_sha256']!=expected_sha:raise ValueError('Split archive identity differs')
        chunks=[]
        for part in split['parts']:
            path=archive.parent/part['file']
            if not path.resolve().is_relative_to(archive.parent.resolve()):raise ValueError('Part escapes archive directory')
            chunk=path.read_bytes()
            if len(chunk)!=part['bytes'] or hashlib.sha256(chunk).hexdigest()!=part['sha256']:raise ValueError('Archive part differs')
            chunks.append(chunk)
        payload=b''.join(chunks)
    if hashlib.sha256(payload).hexdigest()!=expected_sha:raise ValueError('Archive identity differs')
    if output.exists():raise FileExistsError('Fresh directory required')
    with tarfile.open(fileobj=io.BytesIO(payload),mode='r:gz') as tar:
        members=tar.getmembers(); names=[m.name for m in members]
        if len(names)!=len(set(names)) or any(not m.isfile() or PurePosixPath(m.name).is_absolute() or '..' in PurePosixPath(m.name).parts for m in members):raise ValueError('Unsafe archive member')
        manifest=json.load(tar.extractfile('manifest.json'))
        if set(names)!=set(manifest['files'])|{'manifest.json'}:raise ValueError('Missing or extra payload')
        if 'stage_count' in manifest:
            if manifest['stage_count']!=91 or manifest['complex_gradient_coordinates']!=8190:raise ValueError('Incomplete endpoint population')
        elif manifest.get('corrected_python_case_ordinals')==[56,65]:
            if (manifest.get('original_cases'),manifest.get('final_schemes'),manifest.get('phase_endpoints'),manifest.get('QT_candidates'))!=(2,8,91,66):raise ValueError('Incomplete corrected Python controls')
        elif manifest.get('original_cases')!=1 or manifest.get('final_schemes')!=8:raise ValueError('Incomplete original case population')
        data={m.name:tar.extractfile(m).read() for m in members}
    for name,spec in manifest['files'].items():
        if len(data[name])!=spec['bytes'] or hashlib.sha256(data[name]).hexdigest()!=spec['sha256']:raise ValueError('Payload differs')
    output.mkdir(parents=True)
    for name,payload in data.items():
        path=output/name
        if not path.resolve().is_relative_to(output.resolve()):raise ValueError('Output escapes target')
        path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(payload)
    population={k:manifest[k] for k in ('stage_count','complex_gradient_coordinates','original_cases','final_schemes','phase_endpoints','QT_candidates') if k in manifest}
    print(json.dumps(dict(verified_payload_files=len(manifest['files']),**population)))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--archive',type=Path,required=True)
    p.add_argument('--output-dir',type=Path,required=True);p.add_argument('--expected-sha256',required=True)
    a=p.parse_args();unpack(a.archive,a.output_dir,a.expected_sha256)
