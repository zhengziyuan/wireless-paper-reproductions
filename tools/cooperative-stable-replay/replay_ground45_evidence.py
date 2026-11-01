"""Restore/recheck all45 ground-factor pairs without any optimization or RNG.

By default all720 final states are freshly evaluated at MP80/MP100. An
explicit exact local closed-report reuse option avoids duplicate mathematics
only after every input and current math-source hash matches. The
phase/QT histories and configured moment streams retain their archived receipt
scope; this compact command does not recreate their absent complete RAW tapes.
"""
import argparse
from pathlib import Path
from types import SimpleNamespace

import numpy as np

from audit_native_case import sha
from audit_no_ris_input_bound import audit as audit_bound
from audit_power_curve_states_mp import audit as audit_final
from build_power_curve_views import NAMES, read, require, write
from compare_power_references import run as compare_references
from unpack_power_evidence import unpack
import mp_phase_reference


def run(args):
    require(not args.output_dir.exists(),'Use a fresh output directory')
    manifest = read(args.packet/'archive-manifest.json')
    require(manifest['case_scope']=='ground' and manifest['cases_per_language']==45 and
            manifest['exact_original_case_ordinals']==list(range(66,111)) and
            manifest['total_final_states']==720 and manifest['original_source_figures']==[8,9,10],
            'Every original15x3 ground-factor cohort and both languages are required')
    args.output_dir.mkdir(parents=True)
    restored = args.output_dir/'restored'
    unpack(args.packet,restored)
    views = {language:read(restored/(language+'-curve-view.json')) for language in ('python','matlab')}
    index = read(restored/'final-state-index.json')
    require(len(index['cases'])==90,'All45 paired cases required')
    for language in views:
        require(sorted(c['ordinal'] for c in index['cases'] if c['language']==language)==list(range(66,111)),
                'Missing/duplicated original state slot')
        require(len(views[language]['results'])==45,'All45 returned points required')
        for kappa in (0,10,20):
            selected = [p for p in views[language]['results'] if p['sweep']==f'ground_kL{kappa}']
            require([p['value'] for p in selected]==list(range(-12,31,3)) and
                    all(set(p['schemes'])==set(NAMES) for p in selected),'All15 original points and eight schemes required')
    with np.load(restored/'final-states.npz',allow_pickle=False) as arrays:
        for language in views:
            for first in (66,81,96):
                cohort = [c for c in index['cases'] if c['language']==language and first<=c['ordinal']<first+15]
                require(len(cohort)==15,'All15 physical inputs required for each invariance check')
                for field in ('d_mean','d_var','gt_second','geo_d_mean','geo_d_var'):
                    base = arrays[index['groups'][cohort[0]['input_group']]['data'][field]]
                    for case in cohort[1:]:
                        other = arrays[index['groups'][case['input_group']]['data'][field]]
                        require(base.shape==other.shape and base.dtype==other.dtype and base.tobytes()==other.tobytes(),
                                'A NoRIS input changed with the RIS-to-LU ground factor')
    for figure,kappa,ymin,ymax in ((8,0,1,4),(9,10,2,6.5),(10,20,2.5,7.5)):
        source = read(restored/f'reference-comparison/original-figure-{figure}-vector-reference.json')
        require(source['axis_calibration']['y_range']==[ymin,ymax] and len(source['curves'])==8 and
                all(len(c['x'])==len(c['y'])==15 for c in source['curves']),
                'Every source ordinate and the original nonzero vertical minimum required')
        stem = restored/f'source-comparison/ground-factor-source-vs-reconstructed-{figure}'
        plotted = read(stem.with_suffix('.json'))
        preview_name=f'source-comparison-figure{figure}.png'
        preview_spec=manifest['preview_files'][preview_name]
        require((args.packet/preview_name).stat().st_size==preview_spec['bytes'] and
                sha(args.packet/preview_name)==preview_spec['sha256']==plotted['PNG_sha256'],
                'Displayed preview differs from its verified archived plot')
        require(plotted['original_y_range']==[ymin,ymax] and plotted['source_points']==120 and
                plotted['reconstructed_points']==240 and plotted['all_reconstructed_ordinates_retained'] and
                plotted['PNG_sha256']==sha(stem.with_suffix('.png')) and plotted['SVG_sha256']==sha(stem.with_suffix('.svg')),
                'Rendered diagnostics do not bind the complete source and computed curves')
        for name in NAMES:
            for language in views:
                selected = [p for p in views[language]['results'] if p['sweep']==f'ground_kL{kappa}']
                require(plotted['reconstructed_curves'][name][language]==[
                    float(np.min(p['schemes'][name]['evaluation']['sinr'])) for p in selected],
                    'A plotted numeric return differs from the actual saved scheme')
    compare_references(SimpleNamespace(case_scope='ground',eps_directory=None,axes_verified=False,
        reference_directory=restored/'reference-comparison',curve_directory=restored,
        output_dir=args.output_dir/'new-reference-comparison'))
    saved_reference = read(restored/'reference-comparison/original-reference-summary.json')
    new_reference = read(args.output_dir/'new-reference-comparison/original-reference-summary.json')
    require(new_reference['comparisons']==saved_reference['comparisons'],'Unfitted source comparison differs')
    reused = getattr(args,'reuse_exact_local_final_report',None) is not None
    if reused:
        require(sha(args.reuse_exact_local_final_report)==sha(restored/'independent-all720-final-states-MP80-MP100.json'),
                'Reuse requires the exact complete local report, not a partial or changed summary')
        actual = read(args.reuse_exact_local_final_report)
    else:
        actual = audit_final(restored,args.output_dir/'new-all720-final-physics-MP80-MP100.json')
    require(actual['all_final_states_physics_and_precision_pass'] and actual['actual_final_states_per_precision']==720 and
            actual['scalar_field_coordinates_per_precision']==5760,
            'A newly evaluated final physical state failed')
    stored = read(restored/'independent-all720-final-states-MP80-MP100.json')
    tools = Path(__file__).resolve().parent
    bindings = [restored/'final-state-index.json',restored/'final-states.npz',
        restored/'python-curve-view.json',restored/'matlab-curve-view.json',
        tools/'audit_power_curve_states_mp.py',Path(mp_phase_reference.__file__),
        tools.parents[1]/'strict/validation/cooperative-original183-inputs-20261017/original-case-index.json']
    expected = {str(i)+':'+p.name:sha(p) for i,p in enumerate(bindings)}
    require(actual['source_input_sha256']==stored['source_input_sha256']==expected,
            'Stored full MP receipt is not bound to these exact inputs and current math sources')
    bound = audit_bound(restored,restored/'reference-comparison',args.output_dir/'new-NoRIS-bound-MP80-MP100.json')
    previous = read(restored/'independent-NoRIS-input-bound-MP80-MP100.json')
    require(bound['all_bound_evaluations_and_source_bindings_pass'] and bound['comparisons']==previous['comparisons'],
            'New fixed-input NoRIS bound does not match the actual stored diagnostic')
    summary = dict(actual_archive_payloads_byte_verified=len(manifest['files']),
        original_source_cases_per_language=45,actual_final_states_recomputed_per_precision=0 if reused else 720,
        actual_complete_local_final_report_reused_after_all_input_and_math_source_hashes_match=reused,
        certified_final_states_per_precision=720,certified_physical_scalar_fields_per_precision=5760,
        all6_language_cohort_NoRIS_five_array_invariance_checks_pass=True,
        all_final_physical_report_bindings_and_fresh_NoRIS_bound_checks_pass=True,
        all360_original_reference_ordinates_per_language_compared_without_fitting=True,
        all_source_nonzero_y_minima_and720_plotted_reconstructed_ordinates_preserved=True,
        archive_SHA256=manifest['archive']['sha256'],optimizer_or_RNG_calls=0,
        original_phase_QT_or_configured_MC_RAW_tapes_reexecuted=False,
        original_curve_or_full183_or_full_paper_pass=False,replayer_SHA256=sha(Path(__file__)))
    write(args.output_dir/'summary.json',summary)
    print(summary,flush=True)
    return summary


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--packet',type=Path,required=True)
    p.add_argument('--output-dir',type=Path,required=True)
    p.add_argument('--reuse-exact-local-final-report',type=Path,
        help='Optional already completed local720-state MP report; all exact input/math hashes must match. Default recomputes all720.')
    run(p.parse_args())
