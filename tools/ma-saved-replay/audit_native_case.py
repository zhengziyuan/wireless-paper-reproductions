"""Full saved native MA6 case with exact-input independent baseline reuse.

All native MRT/ZF pre/post/sweep states are physically recomputed on1000
draws. Fixed-array reference vectors may be reused only from a closed Python
math receipt with identical job/config bytes and unchanged independent sources.
No new MA position update or fixed-array optimization is performed here.
"""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import traceback

import numpy as np

from audit_population import MISSING,runtime,write
from case_archive import pack,read_member
from source_reader import load,read,require,sha


def audit(native_path,python_receipt_path,python_math_dir,job_path,config_path,output,repo):
    require(not output.exists(),'Preserve previous native independent case')
    cached_receipt=read(python_receipt_path);cached_archive=python_math_dir/'cases'/cached_receipt['archive']['file']
    require(sha(cached_archive)==cached_receipt['archive']['sha256'],'Actual independent Python case archive differs')
    py_report=json.loads(read_member(cached_archive,'actual-case-math.json'))
    require(py_report['gates'].get('whole_original_terminal1000_math') is True and py_report['source_and_case_inputs_unchanged'],'Complete independently checked fixed-array vectors required')
    jobbytes=job_path.read_bytes();cfgbytes=config_path.read_bytes();job=json.loads(jobbytes);cfg=json.loads(cfgbytes)
    fp=hashlib.sha256(b'strict-v1\0'+cfgbytes+b'\0'+jobbytes).hexdigest()
    require(fp==cached_receipt['input_fingerprint'] and sha(job_path)==cached_receipt['original_input_sha256'],'Exact same original job/config required for baseline reuse')
    require(hashlib.sha256(cfgbytes).hexdigest()==hashlib.sha256(read_member(cached_archive,'original-run-config.json')).hexdigest(),'Whole fixed-array controls differ')
    raw_native=read(native_path);require(raw_native['input_fingerprint']==fp,'Actual native input fingerprint differs')
    require((job['figure'],job['N'],job['M'],job['kappa'],job['A'])==(6,6,5,6,2),'Full original Fig6 scene required')
    require(raw_native['job_metadata']=={k:job[k] for k in ('N','M','kappa','power','A','figure','point','realization')},'Actual complete native scenario labels differ')
    require(raw_native['checks']['full_N']==6 and raw_native['checks']['full_M']==5 and raw_native['checks']['nlos_samples']==1000,'Original full native samples required')
    # This is an explicitly derived read view. The actual native JSON, its
    # underscore field names, numerical values and metadata remain untouched.
    view=copy.deepcopy(raw_native);families=view['metrics']['schemes']
    names={'MA_MRT':'MA-MRT','MA_ZF':'MA-ZF','FPA_MRT':'FPA-MRT','FPA_ZF':'FPA-ZF','FPA_OPT':'FPA-OPT'}
    require(set(families)==set(names),'All five native families required')
    view['metrics']['schemes']={new:families[old] for old,new in names.items()}
    c,original,independent,certificates,extension,_,proof,paths=load(repo)
    source_signature={str(p):sha(p) for p in paths}
    # Every physics, coordinate and control helper byte in the closed reference
    # must match the current independent reader; no approximate input cache.
    # The original E-root labels remain in the receipt. A new checking host
    # records its own roots; only repository-relative names are translated.
    # Every underlying source SHA is still compared exactly.
    expected_logical={p.resolve().relative_to(repo.resolve()).as_posix():source_signature[str(p)] for p in paths}
    actual_logical={};translation={}
    for label,value in cached_receipt['source_signature'].items():
        normalized=label.replace('\\','/');marker='/wireless-paper-reproductions/'
        require(marker in normalized,'Unrecognized saved source namespace')
        logical=normalized.rsplit(marker,1)[1]
        require(logical in expected_logical and logical not in actual_logical,'Unexpected/duplicated saved logical source')
        actual_logical[logical]=value;translation[label]=logical
    require(actual_logical==expected_logical,'Independent baseline source bytes differ')
    native_sources=raw_native['runtime_source_identity']['sources']
    wanted_native={'run_full_ma_figure_v2.m','run_strict_two_timescale_ma_full_v2.m','strict_ma_full_v2_implementation_fingerprint.m','ma_exact_coordinate.m'}
    require({s['name'] for s in native_sources}==wanted_native,'All four actual native numerical sources required')
    native_paths=[]
    for source in native_sources:
        path=repo/'strict/two-timescale-ma'/source['name'];require(sha(path)==source['sha256'],'Actual native source differs from recorded source bytes')
        native_paths.append(path)
    tracked=paths+native_paths+[Path(__file__),native_path,python_receipt_path,cached_archive,job_path,config_path]
    before={str(p):sha(p) for p in tracked};rt_before=runtime();output.mkdir(parents=True)
    # A public archive restores descriptive filenames such as original-input.
    # The source receipt, point and realization carry the actual case identity.
    stem=cached_receipt['case'];point_index=[9,12,15,18,21,24,27,30,33].index(job['point'])
    require(stem==f"case-{point_index:03d}-mc-{job['realization']:03d}",'Original receipt/point/realization case identity differs')
    casepath=output/'active-cases'/stem;casepath.mkdir(parents=True)
    stages={};gates={};failures=[]
    def terminal():
        initial,_,_,draws,noise,channel,_=independent.geometry_functions(job,cfg)
        require(draws.shape==(1000,6,5),'Exact same full original channel population')
        cached=py_report['stages']['whole_original_terminal1000_math'];reports={};values={}
        require(len(cached['all1000_scalar_vs_batched_oracles_each_original_baseline'])==3,'All1000 scalar/batched controls for all three fixed baselines required')
        for name in ('MA-MRT','MA-ZF','FPA-MRT','FPA-ZF','FPA-OPT'):
            saved=view['metrics']['schemes'][name];actual=np.asarray(saved['sample_sum_rates']).reshape(-1)
            require(actual.shape==(1000,) and np.all(np.isfinite(actual)),'All1000 actual native sample rates required')
            if name.startswith('MA-'):
                mode='mrt' if name=='MA-MRT' else 'zf';position=np.asarray(view['metrics'][mode+'_realized_positions'])
                reference,powers=independent.ma_rates(channel(position),job['power'],noise,mode)
                power_gate=bool(np.max(abs(np.asarray(saved['powers']).reshape(-1)-powers))<1e-9 and np.max(powers)-job['power']<1e-9)
                origin='independent physics at actual native optimized position'
            else:
                previous=cached['original_reader_reports'][name]
                require(previous['all1000_original_benchmark_stops_and_power_constraints_verified'] is True,'Actual independent complete baseline computation required')
                require(type(saved['nonconverged_samples']) is int and saved['nonconverged_samples']==0,'Original native cap/failure counter retained')
                reference=np.asarray(cached['independent_all1000_values'][name]);power_gate=previous['maximum_power_excess']<1e-9
                origin='exact same job/config and independent fixed-array evaluator; reuse closed full1000 scalar/batched reference'
            sample_error=float(np.max(abs(actual-reference)));mean_error=abs(float(saved['mean_sum_rate'])-float(np.mean(actual)))
            require(sample_error<1e-7 and mean_error<1e-9 and power_gate,'Actual native terminal sample/mean/power comparison failed: '+name)
            reports[name]=dict(sample_count=1000,maximum_saved_independent_sample_error=sample_error,stored_mean_error=mean_error,
                physical_power_comparison_pass=True,reference_origin=origin,historical_FPA_W_or_step_KKT_recovered=False)
            values[name]=reference.tolist()
        return dict(reports=reports,all1000_values=values,exact_input_baseline_cache_reuse=True,new_benchmark_optimizer_calls=0)
    tasks=[('complete_saved_state_extension',lambda:extension.complete_saved_state_audit(view,job,cfg,independent,certificates,casepath/'full-state-observations')),
        ('whole_original_history_math',lambda:original.history_audit(view,job,cfg,independent)[0]),
        ('whole_original_terminal1000_math',terminal),
        ('whole_original_coordinate_certificate_math',lambda:certificates.check_case(view,job,cfg))]
    for name,task in tasks:
        print(json.dumps(dict(case=stem,language='matlab',stage=name,status='started')),flush=True)
        try:
            value=task();gates[name]=bool(value.get('complete_saved_state_extension_gates_passed',True));stages[name]=value
            if not gates[name]:failures.append(dict(stage=name,explicit_failed_gate=True))
        except Exception as exc:
            item=dict(stage=name,type=type(exc).__name__,message=str(exc),traceback=traceback.format_exc());failures.append(item);gates[name]=False;stages[name]=dict(passed=False,failure=item)
    comparison=None
    if gates.get('whole_original_terminal1000_math'):
        py_raw=json.loads(read_member(cached_archive,'original-python-raw.json'))
        reference_values={'python':{k:np.asarray(v) for k,v in py_report['stages']['whole_original_terminal1000_math']['independent_all1000_values'].items()},
            'matlab':{k:np.asarray(v) for k,v in stages['whole_original_terminal1000_math']['all1000_values'].items()}}
        comparison=original.compare_states(py_raw,raw_native,reference_values)
    after={str(p):sha(p) for p in tracked};rt_after=runtime();unchanged=before==after and rt_before==rt_after
    good=len(gates)==4 and all(gates.values()) and not failures and unchanged
    report=dict(case=stem,language='matlab',figure=6,input_fingerprint=fp,gates=gates,stages=stages,failures=failures,
        original_native_json_sha256=sha(native_path),actual_Python_math_receipt_sha256=sha(python_receipt_path),actual_baseline_reference_archive_sha256=sha(cached_archive),
        actual_source_and_inputs_before=before,actual_source_and_inputs_after=after,source_and_case_inputs_unchanged=unchanged,
        original_source_namespace_to_current_logical_paths=translation,all_actual_native_four_source_bytes_match_recording=True,
        verifier_runtime_before=rt_before,verifier_runtime_after=rt_after,source_scope_proofs=proof,
        actual_independent_own_state_dual_language_comparison=comparison,
        complete_native_case_independent_math_passed=good,original_MA_positions_reoptimized=False,new_RNG_or_benchmark_optimizer_calls=0,
        native_raw_view_changes_only_five_scheme_field_names=True,**MISSING)
    c.fresh_json(casepath/'actual-native-case-math.json',report)
    for name,p in (('original-input.json',job_path),('original-native-raw.json',native_path),('original-run-config.json',config_path)):
        target=casepath/name;target.write_bytes(p.read_bytes());require(sha(target)==sha(p),'Exact original evidence copy differs')
    archive=pack(casepath,output/'cases'/(stem+'.tar.gz'),output)
    receipt=dict(case=stem,passed=good,input_fingerprint=fp,source_signature=source_signature,original_native_raw_sha256=sha(native_path),archive=archive,
        new_position_or_benchmark_optimizer_calls=0,source_and_case_inputs_unchanged=unchanged,full900_or_reference_or_paper_pass=False)
    write(output/'receipt.json',receipt);write(output/'summary.json',{k:v for k,v in report.items() if k not in ('stages','actual_source_and_inputs_before','actual_source_and_inputs_after','source_scope_proofs')})
    print(json.dumps(dict(case=stem,all4_native_saved_math_gates_pass=good,failed_stages=failures,archive_sha256=archive['sha256'],new_optimizer_or_RNG_calls=0)),flush=True)
    return receipt


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('native-result','python-receipt','python-math-dir','job','config','output-dir'):p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--repo',type=Path,default=Path(__file__).resolve().parents[2]);a=p.parse_args()
    if not audit(a.native_result,a.python_receipt,a.python_math_dir,a.job,a.config,a.output_dir,a.repo)['passed']:raise SystemExit(1)
