"""Freeze five ACTUAL native SDP/one1000 components; no whole-CDF upgrade."""
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import shutil

STRICT=Path(__file__).resolve().parent
ROOT=STRICT.parent.parent
WORK=ROOT/'work/hotspot-sdp-audit'
PUBLIC=STRICT/'validation/hotspot-native-before-one1000-components-v1'


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    assert not PUBLIC.exists(),'Use a new identity; never replace evidence'
    products={};bindings=[];summaries=[]
    for case in (12,22,32,43,56):
        native=WORK/f'cdf{case}-prospective-before-ONE1000-ACTUAL-MATLAB-v1.json'
        mp=WORK/f'cdf{case}-prospective-before-ONE1000-ACTUAL-MATLAB80digits-v1.json'
        states=Path(str(native)+'.states.mat')
        a=json.loads(native.read_text(encoding='utf-8-sig'))
        b=json.loads(mp.read_text(encoding='utf-8-sig'))
        assert a['source_unchanged_during_run'] and b['actual_source_interval_and_current_recorded_hashes_pass']
        assert sha(native)==b['actual_native_receipt_sha256']
        assert sha(states)==b['actual_native_states_sha256']==a['actual_returned_matrices_receipt']['sha256']
        assert a['fixed_scale_schedule']==b['fixed_four_scale_schedule']==[1,.01,100,10000]
        assert a['accepted_scale_chosen_before_any_randomization'] and not a['preselection_uses_reference_or_candidate_quality']
        assert a['native_CVX_max_diagonal_dual_conversion']=='-native_dual/positive_scale'
        assert a['original_precision_threshold']==1e-5
        assert b['selected_actual_SDP_independent80digit_precision_pass']
        assert b['actual_single_original1000_batch_and_candidate_precision_gates_pass']
        index=b['actual_selected_attempt_one_based']
        assert index==a['actual_selected_attempt']==1
        assert len(a['actual_attempts'])==len(b['actual_attempts'])==1
        assert a['actual_attempts'][0]['exact_positive_objective_scale']==1
        assert a['actual_attempts'][0]['randomization_candidates_evaluated_for_this_attempt']==0
        assert a['actual_attempts'][0]['double_precision_guard_before_rounding_pass']
        selected=b['actual_attempts'][0]
        assert all(selected['checks'].values()) and selected['all_independent80digit_checks_pass']
        assert selected['precision_decimal_digits']==80 and selected['native_CVX_dual_sign_convention_independently_verified']
        for key in ('true_feasible_primal_dual_gap','actual_raw_primal_dual_gap'):
            assert Decimal(0)<=Decimal(selected[key])<=Decimal('1e-5')
        rounding=a['actual_original_rounding']
        assert rounding==b['actual_single1000_rounding']
        assert rounding['original_precision_and_candidate_gates_pass']
        assert rounding['randomization_batches_executed']==1 and rounding['actual_original_candidates_evaluated']==1000
        assert rounding['no_second_rounding_after_candidate_gate']
        assert b['independent_actual_best_phase_original_surrogate_error']<=1e-8
        assert not b['every_actual1000_candidate_matrix_independently_saved_and_recomputed']
        assert not b['all_selected_backend_MAT_and_MEX_runtime_bytes_bound']
        assert not b['native_production_precision_policy_certified'] and not b['native_whole_sample_or_CDF_verified']
        assert not a['full_reproduction_pass'] and not b['full_reproduction_pass']
        for name,digest in b['WORK_source_hashes'].items():
            assert sha(WORK/name)==digest,name
        for suffix,p in (('actual-native',native),('independent-actual-state80digits',mp)):
            # Native compact files already contain only basenames, not private
            # paths. Copy actual bytes unchanged, never rewrite old flags.
            text=p.read_text(encoding='utf-8-sig')
            assert 'C:\\' not in text and 'C:/' not in text and 'D:\\' not in text and 'D:/' not in text
            products[f'cdf{case}-{suffix}.json']=p
        bindings.extend({'kind':kind,'filename':p.name,'sha256':sha(p)}
            for kind,p in (('actual_native_receipt',native),('actual_saved_native_matrices',states),('actual_independent80digit_receipt',mp)))
        summaries.append({'case':case,'actual_selected_scale':1,'actual_solver_attempts':1,
            'independent80digit_precision_pass':True,'actual_randomization_batches':1,
            'actual_candidates':1000,'actual_original_candidate_gates_pass':True,
            'actual_original_best_phase_surrogate_replay_error':b['independent_actual_best_phase_original_surrogate_error'],
            'true_feasible_primal_dual_gap':selected['true_feasible_primal_dual_gap'],
            'actual_raw_primal_dual_gap':selected['actual_raw_primal_dual_gap']})
    PUBLIC.mkdir(parents=True)
    for name,path in products.items():shutil.copyfile(path,PUBLIC/name)
    aggregate={'scope':'five_actual_native_same_SDP_components_selected_by_precision_before_exactly_one_original1000_batch_NOT_complete_CDF_or_production_policy',
        'actual_case_records':summaries,'all_five_selected_actual_matrices_independent80digit_pass':True,
        'actual_total_randomization_candidates':5000,'actual_total_batches':5,
        'actual_all_five_selected_first_scale':True,'later_fixed_scales_exercised_in_this_protocol_run':False,
        'old_failures_and_historical_receipts_not_upgraded':True,
        'every_actual_candidate_matrix_saved_and_recomputed':False,
        'all_selected_backend_MAT_and_MEX_bytes_runtime_bound':False,
        'native_production_policy_certified':False,'whole_AO_or_full_CDF_certified':False,'full_reproduction_pass':False}
    (PUBLIC/'independent-five-actual-record-audit.json').write_text(json.dumps(aggregate,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    readme='''# Five native precision-before-one1000 components

The five retained numerical inputs (12,22,32,43,56) were actually executed in
native MATLAB. Each selected the first fixed scale (1) using precision gates
before any candidate evaluation, then executed exactly one original batch of
1000 randomizations. No candidate/reference curve selected a solver scale.
No later scale was exercised in these five protocol runs; they do not certify
the fallback branches. The earlier four-scale diagnostics remain separate.

The subsequent Python verifier did not resolve an SDP. It independently
rebuilt the original coefficients and checked the actually returned native
matrices at 80 decimal digits: true feasible primal, PSD dual witness,
unmodified 1e-5 feasible/raw primal-dual gaps, and the maximization equality
dual conversion `-native_CVX_dual/positive_scale`. This sign conversion is a
CVX convention/validator correction, not a paper model correction. A raw
maximization primal objective is not itself a certified upper bound.

Native receipts retain their originally false "independent recheck complete"
flags unchanged. The later independent receipts and aggregate supply the
separate actual recheck evidence; old bytes are not relabeled retrospectively.
All original 1000-candidate gate records and the saved best phase's original
surrogate replay pass. Every candidate matrix was not saved/recomputed, and
the prototype did not bind the entire selected backend MAT/MEX inventory.

These are five components, not complete AO/QT chains, a full1000 CDF bank,
production retry-policy certification, publisher/author-history recovery, or
published-curve agreement. All such flags remain false. Old failed samples
and old incorrect-sign receipts remain unchanged. The manifest binds the
actual raw matrix files and inputs without uploading private author sources.
'''
    (PUBLIC/'README.md').write_text(readme,encoding='utf-8')
    manifest={'scope':'unchanged_actual_component_receipts_plus_separate_independent_record_audit',
        'inputs':bindings,'executed_WORK_verifier_sources':json.loads(mp.read_text(encoding='utf-8-sig'))['WORK_source_hashes'],
        'freezer_source_sha256':sha(Path(__file__)),'full_reproduction_pass':False,
        'public_files':[{ 'filename':p.name,'sha256':sha(p),'bytes':p.stat().st_size} for p in sorted(PUBLIC.iterdir())]}
    (PUBLIC/'manifest.json').write_text(json.dumps(manifest,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    print(json.dumps({'five_actual_components_independent_pass':True,'public_files':len(list(PUBLIC.iterdir())),
        'manifest_sha256':sha(PUBLIC/'manifest.json'),'full_reproduction_pass':False}))


if __name__=='__main__':main()
