"""Package saved numerical inputs/results only; no manuscripts/solver binaries."""
import argparse
import gzip
import hashlib
import io
import json
from pathlib import Path
import re
import tarfile

from audit_saved_native import read,sha,write


def package(bank,contexts,archive):
    if archive.exists():raise ValueError('Preserve previous package')
    original=read(bank/'execution-progress.json');entries=read(contexts/'index.json')['cases']
    records=original['records'];payloads={};bindings=[];portable=[]
    if len(entries)!=18 or len(records)!=18:raise ValueError('Complete original 18 cases required')
    for row,entry in zip(records,entries):
        if (row['U'],row['kappa_satellite_db'])!=(entry['U'],entry['beta_db']):raise ValueError('Case ordering differs')
        for filename in (row['configuration_filename'],row['result_filename']):
            if Path(filename).name!=filename or '\\' in filename or ':' in filename:raise ValueError('Unexpected nonlocal filename')
            path=bank/filename;raw=path.read_bytes()
            if re.search(rb'[CDE]:[\\/]|OneDrive|sk-(?:proj-|live-)|ghp_[A-Za-z0-9]{20,}|PRIVATE KEY',raw,re.I):
                raise ValueError('Unexpected private-path/credential-like data in '+filename)
            payloads['bank/'+filename]=raw
        context=contexts/entry['context_file'];payloads['contexts/'+entry['context_file']]=context.read_bytes()
        if sha(bank/row['result_filename'])!=entry['result_sha256']:raise ValueError('Changed original result')
        bindings.append(dict(U=row['U'],beta_db=row['kappa_satellite_db'],result_file=row['result_filename'],result_sha256=entry['result_sha256']))
        portable.append({key:row[key] for key in ('U','kappa_satellite_db','configuration_filename','result_filename')})
    payloads['contexts/index.json']=(contexts/'index.json').read_bytes()
    portable_index=dict(scope='portable_file_index_derived_from_saved_native_bank_not_a_new_execution_receipt',
                        completed_cases=18,expected_cases=18,records=portable)
    payloads['bank/execution-progress.json']=(json.dumps(portable_index,indent=2)+'\n').encode()
    provenance=dict(scope='unchanged_saved_native18_numerical_files_and_replayed_model_contexts',cases=bindings,
                    original_producer_progress_sha256=sha(bank/'execution-progress.json'),
                    private_manuscripts_included=False,solver_binaries_included=False,
                    new_optimizer_execution_claimed=False,full_reproduction_pass=False,
                    files={name:hashlib.sha256(raw).hexdigest() for name,raw in payloads.items()})
    payloads['provenance.json']=(json.dumps(provenance,indent=2)+'\n').encode()
    archive.parent.mkdir(parents=True,exist_ok=True)
    with archive.open('wb') as destination,gzip.GzipFile(fileobj=destination,filename='',mode='wb',mtime=0) as compressed,tarfile.open(fileobj=compressed,mode='w|') as tar:
        for name,raw in sorted(payloads.items()):
            info=tarfile.TarInfo('native18-saved-inputs/'+name);info.size=len(raw);info.mtime=0;info.mode=0o644
            tar.addfile(info,io.BytesIO(raw))
    result=dict(archive=archive.name,bytes=archive.stat().st_size,sha256=sha(archive),cases=18,
                starts=243,recorded_rate_samples=54000,files=len(payloads),native_source_case_bytes_preserved=True,
                bulky_replayed_channel_files_included=False,full_reproduction_pass=False)
    write(archive.with_suffix(archive.suffix+'.manifest.json'),result);return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--bank',type=Path,required=True)
    p.add_argument('--contexts',type=Path,required=True);p.add_argument('--archive',type=Path,required=True)
    a=p.parse_args();print(json.dumps(package(a.bank,a.contexts,a.archive)))
