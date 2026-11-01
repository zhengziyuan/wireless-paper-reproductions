"""Prepare a fresh native MA6 full900 plan over an existing immutable bank.

This reads metadata and input bytes only. It never launches MATLAB or changes
numeric configuration. The native recorder requires a fresh output directory.
"""
import argparse
import hashlib
import json
from pathlib import Path


def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(4*1024*1024),b''):h.update(b)
    return h.hexdigest()


def run(a):
    bank=a.bank.resolve();plan_path=a.plan.resolve();parent=a.output_parent.resolve()
    if plan_path.exists():raise FileExistsError('Preserve an existing native plan')
    cfgpath=bank/'run_config.json';cfgbytes=cfgpath.read_bytes();cfg=json.loads(cfgbytes)
    manifest=json.loads((bank/'manifest.json').read_bytes());bankplan=json.loads((bank/'plan.json').read_bytes())
    if (manifest['expected_jobs'],manifest['case_count'],manifest['realizations_per_case'],manifest['nlos_per_geometry'],bankplan['figure'])!=(900,9,100,1000,6):raise ValueError('Complete exact Fig6 bank required')
    if sha(cfgpath)!='72bd6211cd90e238bfa34a25d4f8e56d29454b01c51aca32aa483488475a0d80' or manifest['config_sha256']!=sha(cfgpath):raise ValueError('Exact disclosed full configuration required')
    if (cfg['maximum_AO_iterations'],cfg['fractional_increase_threshold'],cfg['benchmark_solver']['maximum_iterations'])!=(10000,5e-5,1500):raise ValueError('Original configured controls required')
    rows=manifest['files'];identities={(r['case_index'],r['realization']) for r in rows}
    if len(rows)!=900 or identities!={(c,r) for c in range(9) for r in range(100)}:raise ValueError('All original900 slots required')
    inputs=[]
    for row in rows:
        name=f"case-{row['case_index']:03d}-mc-{row['realization']:03d}.json"
        if row['filename']!=name:raise ValueError('Original filename differs')
        path=bank/'jobs'/name;raw=path.read_bytes();job=json.loads(raw)
        if (job['figure'],job['N'],job['M'],job['kappa'],job['A'],job['point'])!=(6,6,5,6,2,9+3*row['case_index']):raise ValueError('Full original case dimensions/grid differ')
        fp=hashlib.sha256(b'strict-v1\0'+cfgbytes+b'\0'+raw).hexdigest()
        if fp!=row['input_fingerprint']:raise ValueError('Exact original input fingerprint differs')
        inputs.append(dict(filename=name,case_index=row['case_index'],realization=row['realization'],input_fingerprint=fp,path=str(path),sha256=sha(path)))
    repo=Path(__file__).resolve().parents[2];here=Path(__file__).resolve().parent
    native=[]
    for name in ('run_full_ma_figure_v2','run_strict_two_timescale_ma_full_v2','strict_ma_full_v2_implementation_fingerprint','ma_exact_coordinate'):
        path=repo/'strict/two-timescale-ma'/(name+'.m');native.append(dict(key=path.name,name=name,path=str(path),sha256=sha(path)))
    metadata=[dict(key=name,path=str(bank/name),sha256=sha(bank/name)) for name in ('run_config.json','manifest.json','plan.json')]
    own=[dict(key=p.name,path=str(p),sha256=sha(p)) for p in (Path(__file__),here/'run_owned_native_MA6_900.m',here/'recorder-scope-adaptation.json')]
    plan=dict(scope='CURRENT_GOAL_owned_native_MA6_full900_record_only_v1',figure=6,kappa=6,whole_population_count=900,
        configured_geometries_per_point=100,configured_NLoS_per_geometry=1000,schemes_per_case=5,AO_unreported_cap=10000,FPA_unreported_cap=1500,
        original_full_sweep_relative_stop=5e-5,selected_input_binding_path=str(bank/'manifest.json'),selected_input_binding_sha256=sha(bank/'manifest.json'),
        allowed_output_parent=str(parent),original_job_folder=str(bank/'jobs'),original_config_path=str(cfgpath),selected_original_sources=native,
        original_bank_metadata=metadata,original_inputs=inputs,own_sources=own,execution_performed_by_preparation=False,
        source_paper_unreported_caps_or_MC_counts_uniquely_recovered=False,independent_or_original_reference_pass=False)
    plan_path.parent.mkdir(parents=True,exist_ok=True);plan_path.write_bytes((json.dumps(plan,indent=2)+'\n').encode())
    print(json.dumps(dict(plan=str(plan_path),sha256=sha(plan_path),original_inputs=900,scientific_or_native_execution_started=False)))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('bank','plan','output-parent'):p.add_argument('--'+name,type=Path,required=True)
    run(p.parse_args())
