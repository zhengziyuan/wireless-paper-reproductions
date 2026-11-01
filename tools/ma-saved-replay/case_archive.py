"""Losslessly archive only newly generated observations, then verify bytes.

Original input/result files are read-only. Plain temporary observations are
removed only after exact archive-member SHA/size checks; their logical names,
plaintext hashes and numeric JSON bytes are retained without transformation.
"""
import gzip
import hashlib
from pathlib import Path,PurePosixPath
import tarfile


def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda:f.read(4*1024*1024),b''):h.update(b)
    return h.hexdigest()


def pack(case_dir,target,owned_output):
    case_dir=case_dir.resolve();owned_output=owned_output.resolve();target=target.resolve()
    if (case_dir.parent!=owned_output/'active-cases' or not case_dir.name.startswith('case-') or
        target.parent!=owned_output/'cases' or target.exists()):raise ValueError('Exact new owned case/output paths required')
    members={}
    for p in sorted(case_dir.rglob('*')):
        if p.is_symlink():raise ValueError('No observation links')
        if p.is_file():members[p.relative_to(case_dir).as_posix()]=dict(bytes=p.stat().st_size,sha256=sha(p))
    if not members:raise ValueError('No closed case observations')
    target.parent.mkdir(parents=True,exist_ok=True)
    temporary=target.with_name(target.name+'.tmp')
    if temporary.exists():raise FileExistsError('Preserve an uncertain prior archive')
    with temporary.open('xb') as raw:
        with gzip.GzipFile(fileobj=raw,mode='wb',mtime=0,filename='') as compressed:
            with tarfile.open(fileobj=compressed,mode='w') as archive:
                for name in members:archive.add(case_dir/name,arcname=name,recursive=False)
    with tarfile.open(temporary,'r:gz') as archive:
        seen=set()
        for member in archive:
            name=member.name
            if not member.isfile() or name not in members or name in seen:raise ValueError('Unexpected archive member')
            data=archive.extractfile(member).read();spec=members[name]
            if len(data)!=spec['bytes'] or hashlib.sha256(data).hexdigest()!=spec['sha256']:raise ValueError('Plain observation changed')
            seen.add(name)
        if seen!=set(members):raise ValueError('Missing case observation')
    temporary.replace(target)
    # Verify the resolved deletion target and exact plaintext bytes AGAIN.
    if case_dir.parent!=owned_output/'active-cases' or not case_dir.is_relative_to(owned_output):raise ValueError('Outside owned workspace')
    for name,spec in members.items():
        p=case_dir/name
        if p.resolve().parent!=p.parent.resolve() or p.is_symlink() or p.stat().st_size!=spec['bytes'] or sha(p)!=spec['sha256']:
            raise ValueError('Temporary observation differs; retained instead of deleting')
    for name in members:(case_dir/name).unlink()
    for directory in sorted((p for p in case_dir.rglob('*') if p.is_dir()),key=lambda p:len(p.parts),reverse=True):directory.rmdir()
    case_dir.rmdir()
    return dict(file=target.name,bytes=target.stat().st_size,sha256=sha(target),members=members,
        every_plaintext_observation_byte_verified_before_removing_owned_temporaries=True,
        original_input_or_result_files_modified=False)


def read_member(archive_path,name):
    logical=PurePosixPath(name)
    if logical.is_absolute() or '..' in logical.parts or '\\' in name:raise ValueError('Unsafe logical member')
    with tarfile.open(archive_path,'r:gz') as archive:return archive.extractfile(name).read()
