"""Package one already closed actual complete case; never run mathematics."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil

from case_archive import read_member
from source_reader import read,require,sha


def package(directory,case,packet):
    require(not packet.exists(),'Preserve prior public packet')
    receipt_path=directory/'receipts'/(case+'.json');receipt=read(receipt_path)
    archive_path=directory/'cases'/receipt['archive']['file']
    require(receipt['passed'] and receipt['source_and_case_inputs_unchanged'] and sha(archive_path)==receipt['archive']['sha256'],'One actual closed passing case required')
    actual=json.loads(read_member(archive_path,'actual-case-math.json'))
    require(actual['complete_saved_case_independent_math_passed'] and len(actual['gates'])==4 and all(actual['gates'].values()),'All four actual mathematical stages required')
    packet.mkdir(parents=True);shutil.copyfile(receipt_path,packet/'actual-case-receipt.json')
    raw=archive_path.read_bytes();parts=[]
    for i,start in enumerate(range(0,len(raw),512*1024)):
        chunk=raw[start:start+512*1024];name=archive_path.name+f'.part{i:03d}';(packet/name).write_bytes(chunk)
        parts.append(dict(file=name,bytes=len(chunk),sha256=hashlib.sha256(chunk).hexdigest()))
    manifest=dict(scope='One actual closed full-size MA6 case and every saved coordinate/full1000-draw observation; not a full900 certificate',
        original_cases=1,figure=6,kappa=6,N=6,M=5,schemes=5,draws_per_case=1000,case=case,
        original_population=900,full900_execution_or_independent_or_native_or_reference_pass=False,
        archive=dict(filename=archive_path.name,bytes=len(raw),sha256=sha(archive_path),parts=parts),
        receipt=dict(file='actual-case-receipt.json',sha256=sha(packet/'actual-case-receipt.json')),
        original_plaintext_members=len(receipt['archive']['members']),packager_sha256=sha(Path(__file__)))
    (packet/'archive-manifest.json').write_bytes((json.dumps(manifest,indent=2)+'\n').encode())
    summary=dict(case=case,all4_mathematical_stages_pass=True,original_MA_positions_reoptimized=False,original_input_fingerprint=actual['input_fingerprint'],
        historical_producer_runtime_or_unsaved_FPA_W_recovered=False,stages={})
    for name,result in actual['stages'].items():
        if name=='complete_saved_state_extension':
            summary['stages'][name]={mode:dict(unique_exact_positions=result[mode]['unique_exact_state_count'],
                accepted_sweeps=len(result[mode]['all_source_order_sweeps']),coordinates=len(result[mode]['all_source_order_coordinates']),
                all1000_MC_recomputed_at_every_pre_post_state=True) for mode in ('mrt','zf')}
        elif name=='whole_original_terminal1000_math':
            summary['stages'][name]=result['original_reader_reports']
        else:summary['stages'][name]=result
    (packet/'actual-one-case-math-summary.json').write_bytes((json.dumps(summary,indent=2)+'\n').encode())
    print(json.dumps(dict(archive_bytes=len(raw),sha256=manifest['archive']['sha256'],parts=len(parts),members=manifest['original_plaintext_members'])))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--directory',type=Path,required=True);p.add_argument('--case',required=True);p.add_argument('--packet',type=Path,required=True)
    a=p.parse_args();package(a.directory,a.case,a.packet)
