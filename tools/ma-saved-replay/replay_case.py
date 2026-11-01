"""Restore and numerically replay one complete actual MA6 witness.

The separate all900 population reader remains the full-scope command. This
public witness includes every saved coordinate and all1000 original draws;
one-case CI is never promoted to a complete900 or native/reference result.
"""
import argparse
import hashlib
import io
import json
from pathlib import Path,PurePosixPath
import tarfile
import traceback

from audit_population import runtime,write,MISSING
from source_reader import load,read,require,sha,source_paths


def restore(packet,output):
    m=read(packet/'archive-manifest.json');require(not output.exists(),'Fresh public restoration directory required')
    require((m['original_cases'],m['figure'],m['kappa'],m['N'],m['M'],m['schemes'],m['draws_per_case'])==(1,6,6,6,5,5,1000),'Exact full-size one-case witness required')
    chunks=[];spec=m['archive']
    for i,part in enumerate(spec['parts']):
        require(part['file']==spec['filename']+f'.part{i:03d}','Exact ordered archive parts')
        p=packet/part['file'];raw=p.read_bytes()
        require(len(raw)==part['bytes'] and hashlib.sha256(raw).hexdigest()==part['sha256'],'Archive part differs');chunks.append(raw)
    raw=b''.join(chunks);require(len(raw)==spec['bytes'] and hashlib.sha256(raw).hexdigest()==spec['sha256'],'Whole actual case archive differs')
    receipt_path=packet/m['receipt']['file'];require(sha(receipt_path)==m['receipt']['sha256'],'Actual closed case receipt differs')
    receipt=read(receipt_path);require(receipt['archive']['sha256']==spec['sha256'],'Receipt/archive identity differs')
    files={}
    with tarfile.open(fileobj=io.BytesIO(raw),mode='r:gz') as archive:
        for member in archive:
            name=member.name;logical=PurePosixPath(name)
            require(member.isfile() and not logical.is_absolute() and '..' not in logical.parts and '\\' not in name and ':' not in name and name not in files,'Unsafe or duplicate logical payload')
            require(name in receipt['archive']['members'],'Unexpected case payload')
            payload=archive.extractfile(member).read();wanted=receipt['archive']['members'][name]
            require(len(payload)==wanted['bytes'] and hashlib.sha256(payload).hexdigest()==wanted['sha256'],'Actual plaintext numerical payload differs')
            files[name]=payload
    require(set(files)==set(receipt['archive']['members']),'Missing actual observation')
    output.mkdir(parents=True)
    for name,payload in files.items():
        p=output/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(payload)
    return receipt,files


def replay(packet,output,repo):
    require(not output.exists(),'Preserve previous public replay')
    receipt,files=restore(packet,output/'restored')
    c,original,independent,certificates,extension,terminal,proof,paths=load(repo)
    tracked=paths+[Path(__file__)];before={str(p):sha(p) for p in tracked};rt_before=runtime()
    cfgbytes=files['original-run-config.json'];jobbytes=files['original-input.json']
    cfg=json.loads(cfgbytes);job=json.loads(jobbytes);raw=json.loads(files['original-python-raw.json'])
    fp=hashlib.sha256(b'strict-v1\0'+cfgbytes+b'\0'+jobbytes).hexdigest()
    require(fp==receipt['input_fingerprint']==raw['input_fingerprint'],'Exact restored original input fingerprint')
    require((job['figure'],job['N'],job['M'],job['kappa'],job['A'])==(6,6,5,6,2),'Actual full original scene required')
    require((cfg['geometry_realizations'],cfg['nlos_realizations_per_geometry'],cfg['maximum_AO_iterations'],cfg['fractional_increase_threshold'],cfg['verification_tolerance'])==(100,1000,10000,5e-5,1e-6),'Original complete controls')
    require(cfg['convex_solver']['options']['objective_gap_absolute_tolerance']==cfg['convex_solver']['options']['objective_gap_relative_tolerance']==1e-10,'Original coordinate gaps')
    require(cfg['benchmark_solver']==dict(maximum_iterations=1500,fractional_tolerance=5e-5,bisection_tolerance=1e-12,spectral_zero_tolerance=1e-12),'Original complete baseline controls')
    initial,_,_,_,noise,channel,_=independent.geometry_functions(job,cfg)
    stages={};failures=[]
    tasks=[('complete_saved_state_extension',lambda:extension.complete_saved_state_audit(raw,job,cfg,independent,certificates,output/'new-independent-full-state-observations')),
        ('whole_original_history_math',lambda:original.history_audit(raw,job,cfg,independent)[0]),
        ('whole_original_terminal1000_math',lambda:terminal(raw,job,cfg,independent,initial,noise,channel,'python',{},scalar_oracle=True)),
        ('whole_original_coordinate_certificate_math',lambda:certificates.check_case(raw,job,cfg))]
    for name,task in tasks:
        print(json.dumps(dict(stage=name,status='started',cases=1,original_population=900)),flush=True)
        try:
            result=task()
            if name=='whole_original_terminal1000_math':
                schemes,values,scalar=result
                result=dict(schemes=schemes,independent_values={k:v.tolist() for k,v in values.items()},all1000_scalar_oracles=scalar,
                    current_independent_baseline_calculations=True,historical_W_or_KKT_transcript_recovered=False)
            good=result.get('complete_saved_state_extension_gates_passed',True)
            stages[name]=dict(passed=bool(good),result=result)
            if not good:failures.append(dict(stage=name,failed_gate=True))
        except Exception as exc:
            item=dict(stage=name,type=type(exc).__name__,message=str(exc),traceback=traceback.format_exc());failures.append(item);stages[name]=dict(passed=False,failure=item)
    after={str(p):sha(p) for p in tracked};rt_after=runtime()
    report=dict(scope=__doc__,original_cases=1,all_actual_archive_payloads_verified=len(files),
        actual_full_size_case_fingerprint=fp,stages=stages,failures=failures,source_scope_proofs=proof,
        source_before=before,source_after=after,actual_runtime_before=rt_before,actual_runtime_after=rt_after,
        all_one_case_independent_saved_math_passed=not failures and len(stages)==4 and all(s['passed'] for s in stages.values()) and before==after and rt_before==rt_after,
        original_MA_positions_reoptimized=False,new_RNG_calls=0,independent_fixed_benchmark_iterations_are_new=True,
        full900_population_independently_certified_by_this_command=False,**MISSING)
    write(output/'replay-summary.json',report)
    print(json.dumps({k:v for k,v in report.items() if k not in ('stages','failures','source_scope_proofs','source_before','source_after','actual_runtime_before','actual_runtime_after')}),flush=True)
    return report


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--packet',type=Path,required=True);p.add_argument('--output-dir',type=Path,required=True)
    p.add_argument('--repo',type=Path,default=Path(__file__).resolve().parents[2]);a=p.parse_args()
    if not replay(a.packet,a.output_dir,a.repo)['all_one_case_independent_saved_math_passed']:raise SystemExit(1)
