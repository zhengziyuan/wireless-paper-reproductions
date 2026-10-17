"""Restore the public numerical archive into a fresh bounded directory."""
import argparse
import json
from pathlib import Path,PurePosixPath
import shutil
import tarfile
from audit_saved_native import read,sha


def unpack(archive,output):
    if output.exists():raise ValueError('Choose a fresh extraction directory')
    manifest=read(archive.with_suffix(archive.suffix+'.manifest.json'))
    if manifest['sha256']!=sha(archive):raise ValueError('Archive digest differs')
    root=output.resolve()
    with tarfile.open(archive,'r:gz') as source:
        members=source.getmembers()
        for member in members:
            name=PurePosixPath(member.name)
            if (name.is_absolute() or '..' in name.parts or '\\' in member.name or ':' in member.name
                    or not name.parts or name.parts[0]!='native18-saved-inputs' or not member.isfile()
                    or not (root/str(name)).resolve().is_relative_to(root)):
                raise ValueError('Unsafe/unexpected archive member')
        output.mkdir(parents=True)
        for member in members:
            target=root/member.name;target.parent.mkdir(parents=True,exist_ok=True)
            with source.extractfile(member) as data,target.open('xb') as destination:shutil.copyfileobj(data,destination)
    base=root/'native18-saved-inputs';provenance=read(base/'provenance.json')
    for relative,expected in provenance['files'].items():
        path=(base/relative).resolve()
        if not path.is_relative_to(base) or not path.is_file() or sha(path)!=expected:
            raise ValueError('Changed/missing portable numerical input')
    if len(provenance['cases'])!=18:raise ValueError('Missing original cases')
    return dict(cases=18,verified_payload_files=len(provenance['files']),root=str(base),full_reproduction_pass=False)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--archive',type=Path,required=True)
    p.add_argument('--output-dir',type=Path,required=True);a=p.parse_args();print(json.dumps(unpack(a.archive,a.output_dir)))
