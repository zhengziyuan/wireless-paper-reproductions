"""Freeze a small public qualified NoRIS CURRENT-model bound and proof.

Author manuscript/artwork and private filesystem paths are not published.
Actual completed WORK mp80 receipt and executed production hashes are checked.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
from audit_hotspot_no_ris_bound_certificate import verify


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


if __name__=='__main__':
    strict=Path(__file__).resolve().parent;workspace=strict.parents[1]
    parser=argparse.ArgumentParser();parser.add_argument('--input',type=Path,default=workspace/'work'/'hotspot-NoRIS-current-model-cluster-upper-bound-hermitian-exact.json')
    parser.add_argument('--output-dir',type=Path,default=strict/'validation'/'hotspot-statistical-validated18-python-v1')
    args=parser.parse_args();source=json.loads(args.input.read_text(encoding='utf-8'))
    base=strict/'hotspot-satcom';hashes=source['executed_source_hashes']
    assert source['source_unchanged_during_audit'] is True
    assert hashes=={n:sha(base/n) for n in hashes}
    assert sha(base/'outputs'/'statistical-validated18-final-python.json')==source['actual_native_receipt_sha256']
    case=next(c for c in source['cases'] if c['U']==6 and c['beta_db']==20)
    mp=case['independent_mp80_matrix_certificate'];assert mp['all_fixed_matrix_bounds_positive'] is True
    Q=mp['source_HU_Q_matrices']
    public=dict(schema_version=1,paper_id='hotspot-satcom',scope='CURRENT_declared_full16_feed_NoRIS_ratio_expected_powers_bound_NOT_universal_paper_impossibility',
        actual_case={'U':6,'J':16,'N':16,'K':10,'beta_db':20,'M':25},
        certificate_constants=dict(lower=case['lower_matrix_multiple'],upper=case['upper_matrix_multiple'],
            lambda_upper=case['Q0_max_eigenvalue_upper'],power_w=100,normalized_noise_variance=1),
        bound=case['current_approximate_metric_upper_bound'],actual_computed_NoRIS_rate=case['actual_approximate_metric'],
        original_reference_NoRIS_rate=case['original_reference_NoRIS_ordinate'],
        original_reference_exceeds_CURRENT_model_bound=case['reference_above_current_model_bound'],
        matrix_witness={'Q0':mp['source_reference_Q0'],'HU_Q':[{'real':r,'imag':i} for r,i in zip(Q['real'],Q['imag'])]},
        matrix_contract='Source metric is real(w^H rawQ w); exact Hermitian part H=(rawQ+rawQ^H)/2 represents this metric. Fraction verifier retains all raw entries and computes H exactly.',
        proof=source['proof'],independent_mp80={k:v for k,v in mp.items() if k not in ('source_HU_Q_matrices','source_reference_Q0')},
        current_model_scope={'reported_power_thermal_parameters':True,'early_per_feed_ESA_covariance':True,
            'declared_receive_gain_dbi':0,'declared_HU_radius_m':10,'historical_author_means_geometry_gain_recovered':False,
            'literal_later_scalar_mu_isotropic_covariance_recovery':False,'all_original_source_constraints_verified':False,
            'exact_Elog_bound_claimed':False,'full_reproduction_pass':False},
        original_reference_EPS_sha256=source['original_reference_input_sha256'],
        actual_native_receipt_sha256=source['actual_native_receipt_sha256'],executed_production_source_hashes=hashes,
        actual_WORK_input_receipt_sha256=sha(args.input),executed_freezer_sha256=sha(__file__),
        source_equation_anchors=['ch_third.tex:44-52','ch_third.tex:484-515','ch_third.tex:661','ch_third.tex:674-693','ch_third.tex:829-838'],
        no_author_manuscript_or_artwork_redistributed=True,no_curve_fit=True,no_optimizer_run=True,no_computed_point_changed=True)
    args.output_dir.mkdir(parents=True,exist_ok=True)
    certificate=args.output_dir/'CURRENT_MODEL_NORIS_BOUND.json'
    certificate.write_text(json.dumps(public,indent=2)+'\n',encoding='utf-8')
    exact=verify(certificate);exactPath=args.output_dir/'CURRENT_MODEL_NORIS_BOUND_EXACT_RATIONAL.json'
    exactPath.write_text(json.dumps(exact,indent=2)+'\n',encoding='utf-8')
    assert hashes=={n:sha(base/n) for n in hashes}
    published=['CURRENT_MODEL_NORIS_BOUND.json','CURRENT_MODEL_NORIS_BOUND_EXACT_RATIONAL.json','CURRENT_MODEL_NORIS_BOUND.md']
    manifest=dict(scope='additional_qualified_CURRENT_model_bound_proof_artifacts_NOT_upgrade_of_historical_reproduction',
        files={n:sha(args.output_dir/n) for n in published},
        sources={'strict/freeze_hotspot_no_ris_model_bound.py':sha(__file__),
                 'strict/audit_hotspot_no_ris_bound_certificate.py':sha(strict/'audit_hotspot_no_ris_bound_certificate.py')},
        exact_rational_all13_matrix_certificates_pass=exact['all_passed'],all_original_source_constraints_verified=False,
        historical_author_model_verified=False,full_reproduction_pass=False)
    (args.output_dir/'no-ris-bound-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'all13_exact_matrix_proofs_pass':exact['all_passed'],'bound':public['bound'],
        'original_reference':public['original_reference_NoRIS_rate'],'elapsed_exact_seconds':exact['elapsed_seconds']}),flush=True)
