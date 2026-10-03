"""Freeze two actual full1000 native position components, never full300 figures."""
import hashlib
import json
from pathlib import Path
import numpy as np

HERE=Path(__file__).resolve().parent
WORK=HERE.parent.parent/'work'
OUTPUT=HERE/'validation/two-timescale-ma-corrected-source-v2-position-components'


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def read(path):return json.loads(path.read_text(encoding='utf-8-sig'))


def native_source_identity(config,runtime):
    package=HERE/'two-timescale-ma'
    h=hashlib.sha256(b'MATLAB-full-v2-history-storage\0')
    names=('run_strict_two_timescale_ma_full_v2.m','run_full_ma_figure_v2.m',
           'strict_ma_full_v2_implementation_fingerprint.m','ma_exact_coordinate.m')
    files={}
    for name in names:
        path=package/name;files['strict/two-timescale-ma/'+name]=sha(path)
        h.update(name.encode()+b'\0'+path.read_bytes()+b'\0')
    assert config['matlab_convex_solver']=='certified_exact_2d'
    h.update(b'certified_exact_2d\0')
    h.update(runtime['matlab_version'].encode()+b'\0'+runtime['blas_version'].encode()+b'\0'+runtime['lapack_version'].encode())
    trajectory=h.hexdigest()
    h=hashlib.sha256(b'corrected-source-MATLAB-full-v2-original-segmented-integral\0'+trajectory.encode()+b'\0')
    groups={
        'matlab-corrected-source-v2':('run_corrected_ma_figure_matlab_source_v2.m','evaluate_correlated_zf_matlab_source_v2.m',
            'validate_corrected_zf_source_matlab_full_v2.m','validate_corrected_zf_position_matlab_source_v2.m','corrected_zf_source_v2_matlab_fingerprint.m'),
        'two-timescale-ma':('correlated_zf_inverse_moment.m','correlated_zf_jensen_bound.m','corrected_zf_position_matlab.m','corrected_zf_context_matlab.m')}
    for folder,names in groups.items():
        for name in names:
            path=HERE/folder/name;relative='strict/'+folder+'/'+name
            files[relative]=sha(path);h.update(relative.encode()+b'\0'+path.read_bytes()+b'\0')
    h.update(runtime['matlab_version'].encode())
    return h.hexdigest(),files,trajectory


def freeze():
    # The already bound native runtime strings reconstruct the exact MATLAB
    # scientific digest; they are not a newly manufactured execution receipt.
    native=read(WORK/'full-paper-banks/ma-figure03-20261004-ao10000-v2-matlab-source-v2/case-000-mc-000-matlab.json')
    runtime=native['runtime_source_identity']
    outputs={};checks=[];source_files=None
    for n,figure in ((6,16),(8,14)):
        bank=WORK/f'full-paper-banks/ma-figure{figure:02d}-20261004-corrected-v2'
        job_path=bank/'jobs/case-000-mc-000.json';config_path=bank/'run_config.json'
        receipt_path=WORK/f'ma-quadrature-audit/n{n}-position-new-source-v2-ACTUAL-20261004-v1.json'
        raw=read(receipt_path);job=read(job_path);config=read(config_path)
        expected,files,trajectory=native_source_identity(config,runtime)
        assert raw['evaluator_source_sha256']==expected and raw['original_integrator_context_position_sources_unchanged']
        assert trajectory==native['implementation_fingerprint']
        assert raw['input_job_sha256']==sha(job_path) and raw['input_config_sha256']==sha(config_path)
        assert raw['complete_position_evidence_passed'] and not raw['all_figure_geometries_or_trajectories_verified']
        assert raw['nlos_samples']==1000 and job['N']==n and job['M']==5 and job['figure']==figure
        assert len(job['nlos_re'])==len(job['nlos_im'])==1000
        beta=1e-4*np.asarray(job['geometry']['distances_m'])**(-2.8)
        aa=job['power']*beta/(5*1e-11)
        model_checks={}
        for name,model in raw['models'].items():
            assert name in ('iid','correlated')
            samples=np.asarray(model['actual_full1000_MC']['sample_sum_rates']);powers=np.asarray(model['actual_full1000_MC']['powers'])
            inverse=np.asarray(model['direct_MC_inverse_diagonal_samples'])
            moment=model['exact_original_model_Jensen'];conditionals=np.asarray(moment['conditional_inverse_moment_samples'])
            assert samples.shape==powers.shape==(1000,) and inverse.shape==conditionals.shape==(1000,5)
            assert np.all(np.isfinite(samples)) and np.all(np.isfinite(conditionals)) and np.min(conditionals)>0 and np.min(inverse)>0
            assert np.max(abs(powers-job['power']))<1e-10
            metric_error=float(np.max(abs(samples-np.sum(np.log2(1+aa/inverse),axis=1))))
            assert metric_error<1e-8
            mean_error=abs(float(np.mean(samples))-model['actual_full1000_MC']['mean_sum_rate']);assert mean_error<1e-10
            means=np.asarray(moment['mean_inverse_normalized_Gram_diagonal'])
            moment_error=float(np.max(abs(np.mean(conditionals,axis=0)-means)));assert moment_error<1e-10
            jensen=float(np.sum(np.log2(1+aa/means)));assert abs(jensen-moment['sum_rate'])<1e-10
            assert moment['outer_expectation_samples']==1000 and moment['modified_channel_or_Wishart_approximation'] is False
            assert model['all1000_times_M_Schur_identities_pass'] and model['all1000_ZF_beamformer_rate_identities_pass']
            assert model['quadrature_error_is_reported_estimate_not_interval_certificate'] and not model['finite_ensemble_bound_guaranteed']
            model_checks[name]={'full_draw_count':1000,'sample_inverse_Gram_rate_identity_error':metric_error,
                'mean_rate_record_error':mean_error,'conditional_moment_aggregation_error':moment_error,
                'population_Jensen_plugin_record_recomputed':True,'full_independent_conditional_integral_replay_claimed':False}
        checks.append({'N':n,'M':5,'figure':figure,'checks':model_checks,'actual_source_digest_reconstructed':True,
            'actual_native_source_digest':expected,'input_sha256':sha(job_path),'original_native_result_sha256':sha(receipt_path)})
        outputs[f'n{n}-actual-native-full1000-initial-position.json']=receipt_path.read_bytes()
        outputs[f'n{n}-generated-full1000-input.json']=job_path.read_bytes()
        if 'immutable-configuration.json' in outputs:assert outputs['immutable-configuration.json']==config_path.read_bytes()
        outputs['immutable-configuration.json']=config_path.read_bytes();source_files=files
    OUTPUT.mkdir(parents=True,exist_ok=True)
    for name,data in outputs.items():
        path=OUTPUT/name
        if path.exists():assert path.read_bytes()==data,'Never replace frozen public numerical bytes'
        else:path.write_bytes(data)
    report={'scope':'actual_native_N6_N8_full1000_initial_positions_NOT_full300_or_source_trajectories',
        'checks':checks,'source_file_sha256':source_files,'runtime_version_strings_used_for_digest':
            {k:runtime[k] for k in ('matlab_version','blas_version','lapack_version')},
        'actual_native_sources_interval_bound_by_original_evaluator_digest':True,
        'complete_runtime_binary_hash_inventory_available':False,
        'full_independent_conditional_integral_replay_claimed':False,
        'full300_native_figures_complete':False,'historical_figure_agreement_verified':False,'full_reproduction_pass':False}
    report_path=OUTPUT/'source-and-record-recheck.json';report_path.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    outputs[report_path.name]=report_path.read_bytes()
    manifest={'scope':report['scope'],'freezer_sha256':sha(Path(__file__)),
        'public_file_sha256':{name:hashlib.sha256(data).hexdigest() for name,data in outputs.items()},
        'full300_native_figures_complete':False,'full_reproduction_pass':False}
    manifest_path=OUTPUT/'freeze-manifest.json';manifest_path.write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'actual_native_position_components':2,'draws_per_position':1000,
        'reconstructed_source_and_input_and_record_checks_pass':True,'manifest_sha256':sha(manifest_path),'full300':False}))


if __name__=='__main__':freeze()
