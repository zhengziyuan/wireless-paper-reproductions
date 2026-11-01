"""Bounded transport of complete preserved ISAC records and qualified proofs."""
from __future__ import annotations

import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import tarfile

SCOPE='preserved-local-ISAC49-legacy1000x13-and-initial138-MP-fields-v1'
FILES={
    'scope.json','local-archive49-member-metadata.json','saved-initial138-numeric-exact-hex.json.gz',
    'native1000x13-exact-binary64.json','native1000x13-generated.csv','original-distinct20.csv',
    'complete20x5-grid.json','complete10x6-power-grid.json',
    'sealed-initial-full-MP80-MP100-fields.json.gz','sealed-initial-exact-first-ray-geometry.json',
    'sealed-all20-original-CSV-to-MAT-comparisons.json','source-driver-candidates.json',
    'source-driver-static-flow.json','source-pre-RNG-parameter-declarations.json',
    'actual-local-closed-source-proof-receipts.json','actual-local-full-audit-summaries.json',
    'retained-host-control-failure-diagnosis.json'}

def require(value,message):
    if not value:raise ValueError(message)

def read(path):return json.loads(Path(path).read_bytes())

def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as handle:
        for block in iter(lambda:handle.read(1024*1024),b''):h.update(block)
    return h.hexdigest()

def write(path,value):
    Path(path).write_text(json.dumps(value,indent=2,allow_nan=False)+'\n',encoding='utf-8')

def safe(name):
    return isinstance(name,str) and name and '\\' not in name and ':' not in name and not name.startswith('/') and all(
        part not in ('','.', '..') for part in name.split('/')) and str(PurePosixPath(name))==name

def checked_archive(packet):
    packet=Path(packet);manifest=read(packet/'archive-manifest.json')
    require(manifest['scope']==SCOPE and manifest['preserved_local_archive_members']==49 and
        manifest['actual_saved_native_table_shape']==[1000,13] and manifest['actual_distinct_original_CSV_rows']==20 and
        manifest['actual_saved_initial_numeric_variables']==138,'Every complete original saved record scope is required')
    require(manifest['fresh_original_optimizers_samplers_or_native_MAT_exports']==0 and
        manifest['full_original_model_algorithm_reference_or_six_paper_pass'] is False,
        'The preserved evidence was relabeled as fresh original reproduction or final-paper conformance')
    require(set(manifest['files'])==FILES and all(safe(name) for name in manifest['files']),
        'The complete safe preserved-source payload inventory is required')
    archive=manifest['archive'];parts=[];seen=set()
    require(0<len(archive['parts'])<=16 and 0<archive['bytes']<=8*1024*1024,'A bounded complete preserved-record archive is required')
    for i,part in enumerate(archive['parts']):
        name=part['file'];require(safe(name) and name==f'isac-legacy-records.tar.gz.part{i:03d}' and name not in seen,
            'One ordered complete preserved-record part is missing, duplicated or unsafe');seen.add(name)
        raw=(packet/name).read_bytes()
        require(0<len(raw)<=512*1024 and len(raw)==part['bytes'] and hashlib.sha256(raw).hexdigest()==part['sha256'],
            'A preserved complete record part differs');parts.append(raw)
    raw=b''.join(parts)
    require(len(raw)==archive['bytes'] and hashlib.sha256(raw).hexdigest()==archive['sha256'],
        'The complete preserved-source record archive differs')
    payloads={};total=0
    with tarfile.open(fileobj=io.BytesIO(raw),mode='r:gz') as handle:
        for member in handle:
            require(member.isfile() and safe(member.name) and member.name in FILES and member.name not in payloads,
                'An unsafe, extra or duplicated preserved record payload was supplied')
            spec=manifest['files'][member.name];total+=member.size
            require(member.size==spec['bytes'] and 0<=member.size<=8*1024*1024 and total<=32*1024*1024,
                'A complete bounded preserved record payload size differs')
            value=handle.extractfile(member).read()
            require(hashlib.sha256(value).hexdigest()==spec['sha256'],'One complete preserved source/record payload differs')
            payloads[member.name]=value
    require(set(payloads)==FILES,'One complete required saved record payload is absent')
    return manifest,payloads

def restore(packet,output):
    output=Path(output);require(not output.exists(),'Keep previous complete, partial and failed restoration epochs')
    manifest,payloads=checked_archive(packet);output.mkdir(parents=True)
    for name,value in payloads.items():(output/name).write_bytes(value)
    return manifest

def check_restored(packet,root):
    manifest,payloads=checked_archive(packet);root=Path(root)
    for name,value in payloads.items():
        require((root/name).is_file() and (root/name).stat().st_size==len(value) and
            sha(root/name)==manifest['files'][name]['sha256'],'A restored complete original record changed')
    return manifest
