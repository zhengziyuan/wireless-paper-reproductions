"""Independently replay complete72 paired final states and original144 ordinates.

Default recomputes all1152 endpoints at MP80/MP100. Optional exact local reuse
requires the same complete report and every restored input/current math-source
hash; it never converts a partial population into a completed one.
"""
import argparse
from pathlib import Path
from types import SimpleNamespace

import numpy as np

import audit_multi_single_curve_states_mp as math_reader
import mp_phase_reference as ref
from audit_native_case import sha
from build_power_curve_views import NAMES, read, require, verify_limits, write
from build_multi_single_curve_views import source_scenes
from compare_multi_single_reference import run as compare_references, selections
from unpack_multi_single_evidence import unpack


def run(args):
    require(not args.output_dir.exists(),'Use a fresh independent output directory')
    tools=Path(__file__).resolve().parent
    watched=[Path(__file__),tools/'unpack_multi_single_evidence.py',tools/'unpack_power_evidence.py',
             tools/'compare_multi_single_reference.py']
    before={str(p):sha(p) for p in watched}
    args.output_dir.mkdir(parents=True)
    restored=args.output_dir/'restored'
    unpack(args.packet,restored)
    manifest=read(args.packet/'archive-manifest.json')
    index=read(restored/'final-state-index.json')
    identities={c['ordinal']:c for c in source_scenes(
        tools.parents[1]/'strict/validation/cooperative-original183-inputs-20261017/original-case-index.json')}
    require(len(index['cases'])==144,'Every original paired source case required')
    provenance=read(restored/'source-and-audit-bindings.json')['records']
    require([p['identity']['ordinal'] for p in provenance]==list(range(111,183)),
            'All original configuration transport receipts required')
    for p in provenance:
        transport=p['native_configuration_transport']
        require(transport['every_numeric_value_unchanged'] and transport['original_result_modified'] is False,
                'Original configuration values and native JSON bytes must remain unchanged')
        if transport['exact_singleton_mapping_applied']:
            scene=p['identity']['full_reported_scene']
            require((scene['J'],scene['N'])==(1,48) and
                    transport['original_field']=='tuned_not_reported.satellite_latitudes_deg' and
                    transport['expected_singleton']==[transport['raw_scalar']] and
                    transport['all_other_fields_equal_without_mapping'],
                    'Only the exact single-satellite latitude representation may be transported')
    views={language:read(restored/(language+'-curve-view.json')) for language in ('python','matlab')}
    with np.load(restored/'final-states.npz',allow_pickle=False) as arrays:
        for language,view in views.items():
            cases=[c for c in index['cases'] if c['language']==language]
            require(sorted(c['ordinal'] for c in cases)==list(range(111,183)) and len(view['results'])==72,
                    'Missing or duplicate original case')
            for case in cases:
                identity=identities[case['ordinal']]
                group=index['groups'][case['input_group']]
                require(group['language']==language and len(group['data'])==11,'Every exact physical array required')
                shape=arrays[group['data']['d_mean']].shape
                require(shape==tuple(identity['full_reported_scene'][k] for k in ('J','U','N')) and
                        shape in ((3,2,16),(1,2,48)),'Both exact original J1/J3 scenes are required')
                verify_limits(arrays[case['power_limit']],arrays[case['interference_limit']],identity)
                point=[p for p in view['results'] if p['source_case_ordinal']==case['ordinal']]
                require(len(point)==1 and set(point[0]['schemes'])==set(NAMES) and
                        all(point[0][k]==identity[k] for k in ('sweep','parameter','value')),
                        'A stored point differs from its exact original source slot')
            for start in (111,123,135,147,159,171):
                cohort=sorted([c for c in cases if start<=c['ordinal']<start+12],key=lambda c:c['ordinal'])
                require(len(cohort)==12,'Every complete original cohort required')
                base=index['groups'][cohort[0]['input_group']]['data']
                for case in cohort[1:]:
                    other=index['groups'][case['input_group']]['data']
                    require(set(other)==set(base),'A physical channel field is missing')
                    for key in base:
                        a,b=arrays[base[key]],arrays[other[key]]
                        require(a.shape==b.shape and a.dtype==b.dtype and a.tobytes()==b.tobytes(),
                                'A physical input varied within a pure interference-threshold scan')
    plotted=read(restored/'source-comparison/multi-single-source-vs-reconstructed.json')
    require(plotted['actual_languages']==['python','matlab'] and
            plotted['complete72_paired_final_physics_checked'] and
            plotted['source_points']==144 and plotted['reconstructed_points']==288 and
            plotted['source_original_y_range']==[0,14] and
            plotted['all12_original_curves_and_all_actual_computed_points_retained'] and
            plotted['source_interference_W_versus_normalized_I_over_N_conflict_unresolved'],
            'All source/computed values, source vertical range and unit caveat required')
    require(plotted['source_curves']==read(restored/'reference-comparison/original-figure-11-vector-reference.json')['curves'],
            'A plotted original source ordinate or path coordinate differs from the actual reference')
    stem=restored/'source-comparison/multi-single-source-vs-reconstructed'
    preview=args.packet/'source-comparison-figure11.png'
    require(sha(preview)==sha(stem.with_suffix('.png'))==plotted['PNG_sha256'] and
            sha(stem.with_suffix('.svg'))==plotted['SVG_sha256'] and
            sha(preview)==manifest['preview_files'][preview.name]['sha256'] and
            preview.stat().st_size==manifest['preview_files'][preview.name]['bytes'],
            'Displayed image differs from its bound archived numerical diagnostic')
    for language,view in views.items():
        for label,sweep,scheme in selections():
            points=[p for p in view['results'] if p['sweep']==sweep]
            curve=plotted['reconstructed_curves'][language][label]
            require(curve['x']==[p['value'] for p in points] and
                    curve['y']==[float(np.min(p['schemes'][scheme]['evaluation']['sinr'])) for p in points],
                    'A plotted actual ordinate differs from the saved original scheme')
    compare_references(SimpleNamespace(reference_directory=restored/'reference-comparison',
        curve_directory=restored,output_dir=args.output_dir/'new-reference-comparison'))
    require(read(args.output_dir/'new-reference-comparison/original-reference-summary.json')['comparisons']==
            read(restored/'reference-comparison/original-reference-summary.json')['comparisons'],
            'Fresh complete original144-point comparisons differ')
    reused=args.reuse_exact_local_final_report is not None
    stored=read(restored/'independent-all1152-final-states-MP80-MP100.json')
    if reused:
        require(sha(args.reuse_exact_local_final_report)==sha(restored/'independent-all1152-final-states-MP80-MP100.json'),
                'Reuse requires the exact actual complete local1152-state report')
        actual=read(args.reuse_exact_local_final_report)
    else:
        actual=math_reader.audit(restored,args.output_dir/'new-all1152-final-physics-MP80-MP100.json')
    bindings=[restored/'final-state-index.json',restored/'final-states.npz',
        restored/'python-curve-view.json',restored/'matlab-curve-view.json',
        Path(math_reader.__file__),Path(ref.__file__),tools/'audit_native_physics_mp.py',
        tools/'build_power_curve_views.py',tools/'build_multi_single_curve_views.py',
        tools.parents[1]/'strict/validation/cooperative-original183-inputs-20261017/original-case-index.json']
    expected={str(i)+':'+p.name:sha(p) for i,p in enumerate(bindings)}
    require(actual['all_final_states_physics_and_precision_pass'] and
            actual['actual_final_states_per_precision']==1152 and actual['scalar_field_coordinates_per_precision']==7680 and
            actual['source_input_sha256']==stored['source_input_sha256']==expected,
            'Actual full math report does not bind these complete inputs and current math sources')
    require(before=={str(p):sha(p) for p in watched},'An active public transport reader changed')
    summary=dict(actual_archive_payloads_byte_verified=len(manifest['files']),original_cases_per_language=72,
        actual_final_states_recomputed_per_precision=0 if reused else 1152,
        actual_complete_local_final_report_reused_after_every_input_and_math_source_hash_matches=reused,
        certified_final_states_per_precision=1152,certified_scalar_physical_fields_per_precision=7680,
        all12_language_cohort_eleven_array_invariance_checks_pass=True,
        all_original144_reference_ordinates_per_language_freshly_compared=True,
        all288_computed_plotted_ordinates_match_the_actual_saved_scheme=True,
        original_source_y_range_zero_to14_preserved=True,
        exact_singleton_metadata_transport_receipts_preserve_every_original_value_and_native_byte=True,
        source_W_versus_normalized_I_over_N_conflict_unresolved=True,
        archive_SHA256=manifest['archive']['sha256'],optimizer_or_RNG_calls=0,
        original_phase_QT_or_configured_MC_RAW_tapes_reexecuted=False,
        figure11_contains_NoRIS_source_ordinates=False,
        original_reference_or_full183_or_paper_pass=False,replayer_SHA256=sha(Path(__file__)))
    write(args.output_dir/'summary.json',summary)
    print(summary,flush=True)
    return summary


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--packet',type=Path,required=True)
    p.add_argument('--output-dir',type=Path,required=True)
    p.add_argument('--reuse-exact-local-final-report',type=Path,
        help='Explicit exact local closed1152-state MP receipt; every current input/math-source hash must match.')
    run(p.parse_args())
