"""Freeze actual cold sample41 TS,5 Python SDP and16 nativeMAT SDP proofs.

All input/runtime/result identities are checked. No manuscript, original
artwork, raw large native-state bank or private path is published. The old
CDF1000 bank remains incomplete/failed; no nativeMAT full chain is certified.
"""
import argparse
import hashlib
import json
from pathlib import Path

STRICT=Path(__file__).resolve().parent
ROOT=STRICT.parent.parent
BASE=STRICT/'hotspot-satcom'
WORK=ROOT/'work/hotspot-sdp-audit'


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def read(path):return json.loads(Path(path).read_text(encoding='utf-8-sig'))
def write(path,value):path.write_text(json.dumps(value,indent=2,allow_nan=False)+'\n',encoding='utf-8')


def main(args):
    sources={};native_inputs={}
    def bind(path):
        digest=sha(path);native_inputs[Path(path).name]={'sha256':digest,'bytes':Path(path).stat().st_size};return digest
    def verify_sources(record,directory):
        for name,digest in record.items():
            assert sha(directory/name)==digest
            key=('hotspot/'+name) if directory==BASE else ('WORK/'+name)
            if key in sources:assert sources[key]==digest
            sources[key]=digest
    phase_path=WORK/'cdf41-cold-original-RGD-cap100000.json'
    ts_path=WORK/'cdf41-complete-original-TS-cold-cap100000-python-v2.json'
    phase,ts=read(phase_path),read(ts_path)
    assert phase['phase_stage_original_stop_pass'] and ts['all_complete_TwoStage_original_gates_pass']
    assert all(ts['checks'].values()) and phase['source_unchanged_during_run'] and ts['source_unchanged_during_run']
    assert phase['old5000_prefix']['old5001_values_bitwise_equal'] and phase['old5000_prefix']['old_residual_bitwise_equal']
    assert phase['phase_stop']['iterations']==6753 and phase['phase_stop']['threshold']==1e-6
    assert ts['cold_phase_actual_receipt_sha256']==bind(phase_path)
    bind(ts_path)
    assert ts['independent80digit_final_gradient']['original1e6_gradient_stop_pass']
    assert float(ts['independent80digit_final_gradient']['riemannian_gradient_norm'])<1e-6
    verify_sources(phase['executed_source_hashes'],BASE);verify_sources(ts['executed_source_hashes'],BASE)
    verify_sources(phase['executed_WORK_hashes'],WORK);verify_sources(ts['WORK_source_hashes'],WORK)
    bank=BASE/'outputs/instantaneous-source-geometry-cdf20-full1000-final/cdf_kS20-e7bbabe7fe22cde6'
    old=read(bank/'sample-0041.json')
    assert old['sample']['valid_sample'] is False and old['sample']['convergence_pass'] is False
    assert bind(bank/'sample-0041.json')==ts['old_full_sample41_sha256']==phase['original_sample_sha256']
    assert bind(bank/'sample-0040.json')==phase['previous_rng_checkpoint_sha256']
    compact_ts={k:ts[k] for k in ('scope','actual_sample_index','only_changed_numerical_control','old5000_prefix',
        'phase_stop','QT_stop','same_physical_rate_evaluation','physical_constraint_maximum_violation','scheme_status',
        'checks','all_complete_TwoStage_original_gates_pass','independent80digit_final_gradient',
        'elapsed_seconds_QT_and_independent_audit','phase_elapsed_seconds','executed_source_hashes',
        'source_unchanged_during_run','old_sample41_failure_not_upgraded','actual_entire_sample_all_schemes_rerun',
        'MATLAB_complete_cold_same41_chain_verified','historical_author_inputs_recovered','full_reproduction_pass')}
    compact_ts.update(actual_full_dimensions={k:ts['configuration']['reported'][k] for k in ('N','J','U','K','M')},
        physical_reported_parameters=ts['configuration']['reported'],
        old5000_sample_still_failed=True,cold_phase_receipt_sha256=sha(phase_path),cold_TS_receipt_sha256=sha(ts_path),
        original_paper_iteration_cap5000_reported=False)
    stems={12:'cdf12-positive-scale-80digit-dual.json',22:'cdf22-positive-scale100-80digit-dual.json',
        32:'cdf32-positive-scale100-80digit-dual.json',43:'cdf43-positive-scale001-80digit-dual.json',56:'cdf56-positive-scale100-80digit-dual.json'}
    python=[]
    for index,stem in stems.items():
        path=WORK/stem;r=read(path)
        assert r['all_precision_checks_pass'] and all(r['checks'].values()) and r['source_unchanged_during_run']
        verify_sources(r['executed_source_hashes'],BASE);verify_sources(r['WORK_source_hashes'],WORK)
        for name in ('true_feasible_primal_dual_gap','actual_raw_primal_dual_gap'):assert 0<=float(r[name])<=1e-5
        assert r['actual_solver_attempt']['all_original_draws']==r['actual_solver_attempt']['actual_candidates_evaluated']==1000
        # Each input is a generated failure fixture, not author artwork/data.
        match=[p for p in (BASE/'outputs').glob('instantaneous-SDP-rounding-failure-*.mat') if sha(p)==r['fixture_sha256']]
        assert len(match)==1;bind(match[0]);bind(path)
        attempts_path=WORK/f'cdf{index}-positive-scale.json';attempts=read(attempts_path)
        assert len(attempts['actual_attempts'])==4 and attempts['fixture_sha256']==r['fixture_sha256']
        assert {x['scale'] for x in attempts['actual_attempts']}=={1,.01,100,10000};bind(attempts_path)
        python.append({'sample_index':index,**{k:r[k] for k in ('scope','checks','all_precision_checks_pass',
            'precision_decimal_digits','exact_positive_objective_scale','true_feasible_primal_objective',
            'independent_dual_upper_objective','true_feasible_primal_dual_gap','actual_raw_primal_dual_gap',
            'positive_dual_PSD_witness_lower_bound','fixture_sha256','source_unchanged_during_run')},
            'actual_successful_same1000_solver_attempt':r['actual_solver_attempt'],
            'all_four_diagnostic_attempts_preserved':attempts['actual_attempts'],
            'native_precision_receipt_sha256':sha(path),'native_four_attempts_sha256':sha(attempts_path),
            'old_failed_sample_repaired_in_full_bank':False})
    convention_path=WORK/'native-CVX-max-equality-sign-20261004-v4.json'
    convention=read(convention_path);assert convention['all_checks_pass'] and all(convention['checks'].values())
    assert abs(convention['maximum']['dual']+1)<1e-12 and abs(convention['minimum']['dual']-1)<1e-12
    assert abs(convention['scaled']['dual']+7)<1e-12;bind(convention_path)
    matlab=[]
    for index in (12,22,32,43):
        path=WORK/f'cdf{index}-ACTUAL-MATLAB80digits-corrected-CVX-sign-v3.json'
        r=read(path)
        assert r['source_unchanged_during_run'] and r['source_identity_before']==r['source_identity_after']
        verify_sources(r['source_identity_before'],WORK)
        assert r['native_convention_receipt_sha256']==sha(convention_path)
        native_path=WORK/f'cdf{index}-same-SDP-scaled-matlab-20261004-v2.json'
        native=read(native_path);assert native['source_unchanged_during_run']
        assert r['retained_wrong_sign_matlab_receipt_sha256']==bind(native_path)
        states=Path(str(native_path)+'.states.mat')
        assert r['actual_matlab_returned_states_sha256']==bind(states)==native['actual_returned_matrices_receipt']['sha256']
        assert len(r['actual_attempts'])==len(native['attempts'])==4
        assert {x['exact_positive_objective_scale'] for x in r['actual_attempts']}=={1,.01,100,10000}
        for attempt in r['actual_attempts']:
            assert attempt['complete_original_precision_attempt_passed'] and attempt['all_independent80digit_checks_pass']
            assert all(attempt['checks'].values()) and all(attempt['unchanged_actual1000_rounding_and_primal_checks'].values())
            assert attempt['old_wrong_sign_receipt_still_failed_and_retained']
            assert attempt['native_CVX_maximum_equality_dual_conversion']=='fixed_all_cases_minus_CVX_dual_divided_by_positive_objective_scale'
            for field in ('true_feasible_primal_dual_gap','actual_raw_primal_dual_gap'):assert 0<=float(attempt[field])<=1e-5
        assert all(a['all_original_precision_checks_pass'] is False for a in native['attempts'])
        for actual_source in native['executed_source_hashes']:
            name=actual_source['filename'];matches=[p for p in (WORK/name,BASE/name,BASE/'outputs'/name) if p.exists() and sha(p)==actual_source['sha256']]
            assert matches, f'Actual nativeMAT source/input not currently hash-matched:{name}'
            sources['nativeMAT/'+name]=actual_source['sha256']
        bind(path)
        matlab.append({'sample_index':index,'scope':r['scope'],'actual_all_four_native_attempts':r['actual_attempts'],
            'actual_corrected_convention_receipt_sha256':sha(path),
            'retained_wrong_sign_native_receipt_sha256':sha(native_path),
            'actual_returned_native_states_sha256':sha(states),
            'actual_native_runtime_source_hashes':native['executed_source_hashes'],
            'all_actual_native1000_and80digit_precision_attempts_pass':True,
            'old_wrong_sign_false_flags_not_retrofitted':True,'nativeMAT_full_CDF_or_whole_sample_executed':False})
    args.output_dir.mkdir(parents=True,exist_ok=True)
    write(args.output_dir/'sample41-cold-full-TwoStage-python.json',compact_ts)
    write(args.output_dir/'same-SDP-five-python-components.json',{
        'scope':'five_actual_failed_full_M25_SDP_components_same1000_draws_NOT_fullCDF',
        'actual_components':python,'all_five_precision_components_pass':True,
        'no_model_constraints_threshold_or_Gaussian_budget_changed':True,
        'four_reuses_of_same_fixed1000_normals_are_diagnostics_NOT_production_additional4000_budget':True,
        'future_production_retry_policy_must_validate_primal_dual_precision_before_single1000_rounding':True,
        'old_fullCDF_sample_flags_not_upgraded':True,'full_reproduction_pass':False})
    write(args.output_dir/'actual-nativeMAT-four-SDP-components.json',{
        'scope':'actual_returned_nativeMAT_full_M25_SDP_matrices_4samples_times4scales_AND80digit_dual_NOT_Python_resolve',
        'actual_samples':matlab,'actual_samples_count':4,'actual_full_precision_attempts':16,
        'all16_original_candidate_primal_AND80digit_precision_attempts_pass':True,
        'native_CVX_convention_actual_scalar_test':convention,
        'native_scalar_source_interval_receipt_available':False,
        'fixed_all_case_max_equality_dual_conversion':'lambda=-native_CVX_equality_dual/positive_objective_scale',
        'old_wrong_sign_failed_receipts_retained':True,'nativeMAT_fullCDF_executed':False,'full_reproduction_pass':False})
    (args.output_dir/'NUMERICAL_PRECISION_SCOPE.md').write_text(
        '# Same original SDP precision and cold two-stage stopping\n\n'
        'The old1000-sample CDF bank is not certified and its failed flags are unchanged. '
        'Sample41 is an actual separate Python cold complete Two-Stage chain, not a rerun of all schemes or a complete CDF. '
        'Only an unreported5000 safety cap was extended. The paper allows a maximum count but does not report5000. '
        'Every one of the first5001 objective values and the5000-step residual is bitwise unchanged; '
        'the same original RGD reaches the unchanged declared1e-6 gradient threshold at6753 steps. '
        'The original QT then stops in3 steps. Independent80-digit final-gradient and all original physical/QT checks pass. '
        'No nativeMAT complete cold sample41 result is certified here.\n\n'
        'Five actual original failed Python SDP inputs retain all1000 given Gaussian draws and all four diagnostic scales. '
        'Four of those same full-size inputs have actual nativeMAT results at each of four positive objective scales: '
        'all16 actual candidate/primal/identity checks and independent80-digit PSD/precision checks pass. '
        'This is component evidence, not a full AO or CDF bank. Positive scaling does not alter the feasible set or argmax.\n\n'
        '## Checker erratum: native CVX maximization equality-dual convention\n\n'
        'This is an implementation/checker error, not a claimed error in the author paper or solver. '
        'The earlier WORK checker used the native maximization equality dual with the wrong sign and reported false large gaps. '
        'Those false receipts remain preserved. For the equality diag(V)=1 and a concave maximization objective, '
        'native CVX uses the convention confirmed by actual scalar tests: max x with x=1 gives dual=-1; '
        'min x gives dual=+1; max7x gives dual=-7. The same fixed conversion applies to every case and scale.\n\n'
        'Let F(V)=sum_u log2(c_u+Tr(A_u V)), let V0 be an independently certified feasible PSD unit-diagonal matrix, '
        'and let B=gradient F(V0). Concavity gives F(V)<=F(V0)+Tr(B(V-V0)). '
        'Set lambda=-native_CVX_dual/objective_scale. A PSD slack S=diag(lambda)-B yields the true upper '
        'F(V0)+Tr(S V0), since diag(V)=1 and Tr(S V)>=0. '
        'The actual returned primal objective is a lower approximation, not itself a mathematically certified upper. '
        'Independent80-digit primal/dual gaps, PSD witnesses and the unchanged original1000-candidate/primal gate '
        'must separately pass1e-5; a loose enlarged upper is not used to hide bad original precision.\n\n'
        'The diagnostic true-primal PSD shift/congruence does not replace the actual optimizer output or Gaussian rounding. '
        'A prospective production retry policy must choose numerical precision before executing the original1000 randomizations once. '
        'No source scenario, channel covariance, objective, QoS, power or interference constraint is fitted to reference curves. '
        'Historical author inputs and published-curve agreement remain unverified. Raw author papers/artwork/private paths are not copied.\n',encoding='utf-8')
    files={p.name:{'sha256':sha(p),'bytes':p.stat().st_size} for p in args.output_dir.iterdir() if p.is_file() and p.name!='manifest.json'}
    write(args.output_dir/'manifest.json',{'scope':'actual_cold_TS41_Python_and_Py5_nativeMAT16_SDP_precision_components_NOT_completeCDF',
        'freezer_source_sha256':sha(__file__),'verified_executed_source_hashes':sources,
        'actual_native_input_and_result_hashes':native_inputs,'public_files':files,
        'old_fullCDF_flags_unchanged':True,'nativeMAT_cold_fullTS41_verified':False,'full_reproduction_pass':False})
    print(json.dumps({'public_folder':str(args.output_dir),'public_files':len(files)+1,
        'Python_cold_fullTS41_all_checks':True,'actual_Python_SDP_components':5,'actual_nativeMAT_SDP_precision_attempts':16,
        'all_nativeMAT_original_and80digit_precision_pass':True,'nativeMAT_fullCDF_certified':False,'full_reproduction_pass':False}),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output-dir',type=Path,default=STRICT/'validation/hotspot-cdf-numerical-components-v1');main(parser.parse_args())
