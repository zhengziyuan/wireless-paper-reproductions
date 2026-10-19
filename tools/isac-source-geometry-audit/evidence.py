"""Bounded, source-qualified transport for the full ISAC geometry evidence."""
from __future__ import annotations

import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import tarfile

SCOPE='original-ISAC11200-initial-support-23900-first-LoS-and-four-NoRIS-source-variants-v1'
EXPECTED_SCENES={'power-b0':500,'power-b2':500,'bs-count':500,'users':500,'rotation':5500,'rho':3700}
EXPECTED_SUPPORT={0:6279,1:4542,2:379}
VARIANTS=('supplied_R1_all_RIS_assisted_paths_removed','public_v2_RU_only_literal_wording')

def require(value,message):
    if not value:raise ValueError(message)

def read(path):return json.loads(Path(path).read_bytes())

def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda:stream.read(1024*1024),b''):h.update(block)
    return h.hexdigest()

def write(path,value):
    Path(path).write_text(json.dumps(value,indent=2,allow_nan=False)+'\n',encoding='utf-8')

def safe(name):
    return isinstance(name,str) and name and '\\' not in name and ':' not in name and not name.startswith('/') and all(
        p not in ('','.', '..') for p in name.split('/')) and str(PurePosixPath(name))==name

def checked_archive(packet):
    packet=Path(packet);m=read(packet/'archive-manifest.json')
    require(m['scope']==SCOPE and m['actual_original_scenes']==11200 and m['actual_original_user_first_ray_pairs']==23900 and
        m['actual_saved_NoRIS_states']==4,'Every original geometry/support/source-state scope is required')
    require(m['fresh_original_optimizers_or_native_streams']==0 and m['full_paper_or_literal_LoS_conformance_pass'] is False,
        'Original optimizer scope or the retained physical/source failure was relabeled')
    spec=m['archive'];blocks=[];seen=set()
    require(0<len(spec['parts'])<=128 and 0<spec['bytes']<=64*1024*1024,'Bounded complete evidence parts required')
    for i,p in enumerate(spec['parts']):
        name=p['file'];require(name==f'isac-source-geometry.tar.gz.part{i:03d}' and safe(name) and name not in seen,
            'A safe ordered complete archive part is required');seen.add(name)
        raw=(packet/name).read_bytes()
        require(len(raw)==p['bytes'] and 0<len(raw)<=512*1024 and hashlib.sha256(raw).hexdigest()==p['sha256'],
            'An original public evidence part differs')
        blocks.append(raw)
    raw=b''.join(blocks)
    require(len(raw)==spec['bytes'] and hashlib.sha256(raw).hexdigest()==spec['sha256'],'The complete source-qualified archive differs')
    require(0<len(m['files'])<=64 and all(safe(n) for n in m['files']),'A safe complete original payload inventory is required')
    payloads={};total=0
    with tarfile.open(fileobj=io.BytesIO(raw),mode='r:gz') as archive:
        for member in archive:
            require(member.isfile() and safe(member.name) and member.name in m['files'] and member.name not in payloads,
                'Unsafe, extra, substituted or duplicate source-geometry payload')
            prior=m['files'][member.name];total+=member.size
            require(member.size==prior['bytes'] and 0<=member.size<=64*1024*1024 and total<=128*1024*1024,
                'The bounded complete payload size differs')
            body=archive.extractfile(member).read()
            require(hashlib.sha256(body).hexdigest()==prior['sha256'],'A full original geometry/state payload differs')
            payloads[member.name]=body
    require(set(payloads)==set(m['files']),'An original full geometry/source-state payload is missing')
    return m,payloads

def restore(packet,output):
    output=Path(output);require(not output.exists(),'Preserve every prior restoration/replay epoch')
    manifest,payloads=checked_archive(packet);output.mkdir(parents=True)
    for name,body in payloads.items():
        p=output/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(body)
    return manifest

def check_restored(packet,root):
    manifest,payloads=checked_archive(packet);root=Path(root)
    for name,raw in payloads.items():
        p=root/name;require(p.is_file() and p.stat().st_size==len(raw) and sha(p)==manifest['files'][name]['sha256'],
            'A restored complete original primitive/reference payload differs')
    return manifest
