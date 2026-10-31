"""All original183 phase fields/stops plus every saved unit-modulus domain."""
import argparse
import json
from pathlib import Path

import phase183_evidence as phase
import audit_phase183_unit_domains as domain


def run(args):
    watched=[Path(__file__),Path(phase.__file__),Path(domain.__file__)]
    before={str(p):phase.sha(p) for p in watched}
    fields=phase.replay(args)
    domains=domain.audit(args.output_dir/'restored',args.output_dir/'all-original-phase-unit-domains-MP80-MP100.json')
    phase.require(before=={str(p):phase.sha(p) for p in watched},'An active complete replay source changed')
    summary=dict(actual_original_cases=183,actual_original_phase_endpoints=fields['actual_original_phase_endpoints'],
        actual_complex_gradient_and_unit_domain_coordinates_per_precision=fields['actual_complex_gradient_coordinates_per_precision'],
        actual_cases_with_fresh_gradient_and_criterion_recalculation=fields['actual_cases_freshly_recomputed'],
        actual_unit_domain_endpoints_freshly_checked=domains['actual_phase_endpoints_checked'],
        every_original_input_reference_payload_and_current_math_source_verified=True,
        all_original_phase_gradient_criterion_precision_and_norm_stops_pass=fields['all_original_phase_fields_stops_and_precision_pass'],
        all_original_unit_modulus_domains_and_precision_pass=domains['all_actual_original_phase_unit_domains_and_precision_pass'],
        exact_complete_local_reference_reuse_is_explicit=fields['exact_complete_local_references_reused_after_all_actual_input_and_math_hashes_match'],
        original_QT_MC_outer_every_inner_iterate_source_curve_global_optimum_or_full_paper_pass=False,
        original_optimizer_or_RNG_calls=0,archive_SHA256=fields['archive_SHA256'],
        complete_driver_current_source_SHA256=before)
    (args.output_dir/'complete-phase-and-domain-summary.json').write_bytes(phase.encode(summary))
    print(json.dumps(summary),flush=True)
    return summary


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('packet','output-dir'):p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--reuse-exact-complete-local-progress',type=Path)
    r=run(p.parse_args())
    if not(r['all_original_phase_gradient_criterion_precision_and_norm_stops_pass'] and
           r['all_original_unit_modulus_domains_and_precision_pass']):raise SystemExit(1)
