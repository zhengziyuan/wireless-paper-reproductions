"""Bind all closed native183 inputs/references and freshly check phase domains.

Reads the complete original native population without optimization or RNG.
Configured channel-moment raw vectors and author source agreement retain
separate requirements. Complete original reports are preserved, including
every genuinely negative tolerance-qualified QT minimum-SINR increment.
"""
import argparse
from copy import deepcopy
from decimal import Decimal,localcontext
import hashlib
import json
from pathlib import Path

import mpmath as mp
import numpy as np
from scipy.io import loadmat

import phase183_evidence as phase
import audit_native_phase_mp as phase_math
import audit_native_physics_mp as physics_math
import audit_native_case as layout
import mp_phase_reference as reference
import audit_phase183_unit_domains as domain


def configuration_transport(native,source):
    """Interpret only MATLAB JSON's declared single-satellite latitude scalar.

    The original containers, MATs and every numerical value remain unchanged.
    Every other configuration field must compare exactly with the full source.
    """
    if native==source:return []
    phase.require(native['reported']['J']==source['reported']['J']==1,
                  'Only the declared J=1 latitude singleton may be interpreted')
    value=native['tuned_not_reported']['satellite_latitudes_deg']
    expected=source['tuned_not_reported']['satellite_latitudes_deg']
    phase.require(isinstance(value,(int,float)) and not isinstance(value,bool) and
        np.isfinite(value) and isinstance(expected,list) and len(expected)==1 and
        isinstance(expected[0],(int,float)) and not isinstance(expected[0],bool) and np.isfinite(expected[0]),
        'Require one finite numerical original latitude and an actual native JSON scalar')
    actual_bytes=np.asarray([value],dtype='<f8').tobytes()
    expected_bytes=np.asarray(expected,dtype='<f8').tobytes()
    phase.require(actual_bytes==expected_bytes,'A native latitude numerical byte differs from the exact original')
    compared=deepcopy(native)
    compared['tuned_not_reported']['satellite_latitudes_deg']=[value]
    phase.require(compared==source,'An unrelated original configuration field differs')
    return [dict(field='/tuned_not_reported/satellite_latitudes_deg',native_JSON_shape=[],
        original_source_shape=[1],original_J=1,numeric_comparison_dtype='<f8',
        actual_numeric_bytes_hex=actual_bytes.hex(),original_numeric_bytes_hex=expected_bytes.hex(),
        only_declared_singleton_interpretation=True,actual_source_files_or_numeric_values_modified=False)]


def modules():
    return {Path(m.__file__).name:phase.sha(Path(m.__file__))
            for m in (phase,phase_math,physics_math,layout,reference,domain)}


def descriptor(path):
    return dict(path=str(path.resolve()),bytes=path.stat().st_size,sha256=phase.sha(path))


def binding(container,matrix,auditor):
    return dict(result=phase.sha(container),states=phase.sha(matrix),
                auditor=phase.sha(Path(auditor.__file__)),reference=phase.sha(Path(reference.__file__)))


def run(args):
    phase.require(not args.output_dir.exists(),'Preserve previous complete native evidence')
    closure=phase.read(args.closure);phase_progress=phase.read(args.phase_progress)
    physics_progress=phase.read(args.physics_progress)
    phase.require(closure['producer_actual_terminal_exit_code_observed']==0 and
        closure['actual_original_cases_completed']==183,'Actual complete original native producer0 is required')
    for key,path,progress in (('phase',args.phase_progress,phase_progress),
                              ('physical_QT',args.physics_progress,physics_progress)):
        closed=closure['independent_closed_native_gates'][key]
        phase.require(closed['actual_terminal_exit_code_observed']==0 and
            closed['progress_SHA256']==phase.sha(path),'Actual original independent terminal0/progress binding differs')
        phase.require(progress['expected']==progress['finished']==183 and
            [r['ordinal'] for r in progress['records']]==list(range(183)),
            'Every original native0..182 slot is required')
        phase.require(progress['passed']==sum(r['passed'] for r in progress['records']),
            'Retain every actual positive or failed independent outcome')
    phase.require(phase.sha(args.bank/'summary.json')==closure['summary_SHA256'],
                  'The actual completed native producer summary changed')
    original_index=phase.read(args.original_case_index)
    identities={c['ordinal']:c for c in original_index['cases']}
    phase.require(sorted(identities)==list(range(183)),'Every original source-index case is required')
    watched=[Path(__file__),args.closure,args.phase_progress,args.physics_progress,
             args.bank/'summary.json',args.bank/'progress.json',args.original_case_index]
    before={str(p):phase.sha(p) for p in watched};math_before=modules()
    args.output_dir.mkdir(parents=True)
    cases=[];domains=[];negative=[];phase_count=coordinates=QT_count=scalars=0
    maxima={80:mp.mpf(0),100:mp.mpf(0)};max_gap=mp.mpf(0)
    for n,(phase_row,physics_row) in enumerate(zip(phase_progress['records'],physics_progress['records'])):
        container=args.bank/f'case-{n:03d}-matlab.json';document=phase.read(container)
        matrix=container.parent/document['state_recording']['filename']
        phase.require(phase.sha(container)==closure['actual_native_result_JSON_SHA256'][container.name] and
            phase.sha(matrix)==document['state_recording']['sha256'] and document['source_unchanged_during_run'],
            'An actual closed native result, recording or source guard differs')
        original_configuration=args.original_bank/f'case-{n:03d}'/'configuration.json'
        phase.require(phase.sha(original_configuration)==identities[n]['configuration_sha256'],
                      'Every original full configuration must match the published complete183 source index')
        configuration_receipt=configuration_transport(document['configuration'],phase.read(original_configuration))
        dimensions={k:identities[n]['full_reported_scene'][k] for k in ('J','U','N','M')}
        phase_directory=Path(phase_row['MP_output']);phase_summary_path=phase_directory/'summary.json'
        physics_path=args.first_physics if n==0 else args.physics_progress.parent/f'case-{n:03d}-MP-physics.json'
        phase_summary=phase.read(phase_summary_path);physics=phase.read(physics_path)
        phase_identity=binding(container,matrix,phase_math);physics_identity=binding(container,matrix,physics_math)
        phase.require(phase.sha(phase_summary_path)==phase_row['MP_summary_sha256'] and
            phase_summary['source_input_sha256']==phase_identity and phase_summary['source_and_input_unchanged'] and
            phase.sha(physics_path)==physics_row['report_sha256'] and
            physics['source_input_sha256']==physics_identity and physics['source_and_inputs_unchanged'],
            'Every complete original phase/physics reference and current math byte must match')
        phase.require(phase_summary['dimensions']==physics['dimensions']==dimensions,
                      'All original J/U/N/M dimensions must be retained')
        count=phase_summary['stages'];U,M=(dimensions[k] for k in ('U','M'))
        phase.require(count==phase_row['stages']==document['state_recording']['phase_endpoints'] and
            phase_summary['complex_coordinates_per_lane']==count*U*M and
            physics['final_states']==document['state_recording']['final_scheme_states']==8 and
            physics['QT_candidates']==physics_row['QT_candidates']==document['state_recording']['QT_candidates'],
            'All actual native phase endpoints, complex coordinates, final states and QT candidates are required')
        members=[dict(file='summary.json',**descriptor(phase_summary_path))]
        for i in range(count):
            path=phase_directory/f'phase-{i:03d}.json';row=phase.read(path)
            phase.require(row['index']==i and set(row['lanes'])=={'80','100'} and
                all(len(lane['gradient'])==U*M for lane in row['lanes'].values()) and
                row['passed']==phase_summary['phase_summaries'][i]['passed'],
                'A complete original phase reference member or precision lane is missing')
            members.append(dict(file=path.name,**descriptor(path)))
        phase.require(phase_summary['all_MP_fields_original_stop_and_precision_checks_pass']==phase_row['passed'] and
            physics['all_physical_QT_and_precision_checks_pass']==physics_row['passed'],
            'Preserve the actual original positive or failed scientific outcome')
        for digits in ('80','100'):
            lane=physics['lanes'][digits]
            phase.require(len(lane['final_states'])==8 and len(lane['QT_candidates'])==physics['QT_candidates'],
                          'No actual physical reference endpoint may be omitted')
        with localcontext() as context:
            context.prec=130
            for item in physics['lanes']['100']['QT_candidates']:
                delta=min(map(Decimal,item['after_fields']['sinr']['reference']))-min(map(Decimal,item['before_fields']['sinr']['reference']))
                if delta<0:negative.append(dict(ordinal=n,QT_index=item['index'],kind=item['kind'],
                    MP100_minimum_SINR_delta=str(delta),within_original1e_minus5_nondecrease_tolerance=delta>=Decimal('-1e-5')))
        native=loadmat(matrix,simplify_cells=True)['recording']
        actual_latitudes=np.asarray(native['input']['configuration']['tuned_not_reported']['satellite_latitudes_deg'],dtype='<f8').reshape(-1)
        original_latitudes=np.asarray(phase.read(original_configuration)['tuned_not_reported']['satellite_latitudes_deg'],dtype='<f8').reshape(-1)
        phase.require(actual_latitudes.size==original_latitudes.size==dimensions['J'] and
            actual_latitudes.tobytes()==original_latitudes.tobytes(),
            'Every actual native MAT latitude value must retain the exact original full vector bytes')
        endpoints=layout.sequence(native['phase_endpoints'])
        phase.require(len(endpoints)==count,'The actual complete native endpoint MAT differs')
        unit_rows=[]
        for i,state in enumerate(endpoints):
            values=np.asarray(state['final_phi'],complex)
            phase.require(values.size==U*M,'Every actual native complex phase coordinate is required')
            errors={digits:domain.unit_error(values,digits) for digits in (80,100)}
            with mp.workdps(110):
                gap=abs(errors[80]-errors[100]);max_gap=max(max_gap,gap)
                passed=all(x<=reference.real(1e-10) for x in errors.values()) and gap<=mp.mpf('1e-40')
                for digits,value in errors.items():maxima[digits]=max(maxima[digits],value)
                unit_rows.append(dict(index=i,complex_phase_coordinates=values.size,
                    maximum_unit_modulus_error={str(d):mp.nstr(v,105) for d,v in errors.items()},
                    maximum_crossprecision_difference=mp.nstr(gap,105),passed=bool(passed)))
        phase.require(binding(container,matrix,phase_math)==phase_identity,
                      'An actual native input changed during fresh domain evaluation')
        domains.append(dict(ordinal=n,actual_phase_endpoints=count,
                            all_actual_phase_domains_pass=all(x['passed'] for x in unit_rows),phases=unit_rows))
        cases.append(dict(ordinal=n,dimensions=dimensions,actual_configuration_transport_receipt=configuration_receipt,container=descriptor(container),states=descriptor(matrix),
            original_configuration=descriptor(original_configuration),original_source_index=identities[n],
            phase_binding=phase_identity,physics_binding=physics_identity,
            phase_reference_members=members,physics_reference=descriptor(physics_path),
            actual_phase_endpoints=count,complex_gradient_coordinates_per_precision=count*U*M,
            actual_final_states=8,actual_QT_candidates=physics['QT_candidates'],
            actual_physical_QT_scalar_values_per_precision=physics['scalar_values_per_precision'],
            original_phase_fields_and_stops_pass=phase_row['passed'],original_final_QT_physics_pass=physics_row['passed']))
        phase_count+=count;coordinates+=count*U*M;QT_count+=physics['QT_candidates'];scalars+=physics['scalar_values_per_precision']
        if len(cases)%12==0:
            print(json.dumps(dict(actual_original_native_cases_bound=len(cases),expected=183,
                actual_phase_endpoints=phase_count,actual_QT_candidates=QT_count)),flush=True)
    phase.require(before=={str(p):phase.sha(p) for p in watched} and modules()==math_before,
                  'A closed original coordinator, input index or active math source changed')
    with mp.workdps(110):
        unit_report=dict(language='matlab',actual_original_cases=183,actual_phase_endpoints_checked=phase_count,
            actual_complex_phase_coordinates_per_precision=coordinates,precisions=[80,100],
            original_unit_modulus_absolute_bound='1e-10',crossprecision_absolute_bound='1e-40',
            maximum_actual_unit_modulus_error={str(d):mp.nstr(v,105) for d,v in maxima.items()},
            maximum_MP80_MP100_difference=mp.nstr(max_gap,105),
            all_actual_original_phase_unit_domains_and_precision_pass=all(c['all_actual_phase_domains_pass'] for c in domains),
            cases=domains)
    inventory=dict(scope='complete-original-native183-phase-final-QT-evidence-inventory',language='matlab',
        exact_original_ordinals=list(range(183)),actual_original_cases=183,actual_phase_endpoints=phase_count,
        actual_complex_gradient_coordinates_per_precision=coordinates,actual_final_states=1464,
        actual_QT_candidates=QT_count,actual_physical_QT_scalar_values_per_precision=scalars,
        exact_closed_inputs_and_references_SHA256=before,current_independent_math_sources_SHA256=math_before,
        actual_source_guarded_inventory_SHA256=phase.sha(Path(__file__)),
        all_original_phase_fields_and_stops_pass=all(c['original_phase_fields_and_stops_pass'] for c in cases),
        all_original_final_QT_physics_pass=all(c['original_final_QT_physics_pass'] for c in cases),
        all_original_phase_unit_domains_pass=unit_report['all_actual_original_phase_unit_domains_and_precision_pass'],
        actual_declared_configuration_singleton_transports=sum(len(c['actual_configuration_transport_receipt']) for c in cases),
        original_native_JSON_MAT_and_numeric_values_unchanged=True,
        actual_MP100_negative_QT_events=negative,original_optimizer_RNG_or_fresh_gradient_calls=0,
        fresh_unit_domain_endpoints=phase_count,all_watched_sources_and_closed_journals_unchanged=True,
        configured_moment_vectors_every_inner_iterate_original_dual_author_source_curve_or_full_paper_pass=False,cases=cases)
    (args.output_dir/'complete-native183-input-and-reference-inventory.json').write_bytes(phase.encode(inventory))
    (args.output_dir/'actual-all-native-phase-unit-domains-MP80-MP100.json').write_bytes(phase.encode(unit_report))
    summary={k:v for k,v in inventory.items() if k not in ('cases','exact_closed_inputs_and_references_SHA256')}
    (args.output_dir/'summary.json').write_bytes(phase.encode(summary))
    print(json.dumps(summary),flush=True)
    return inventory


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('closure','bank','phase-progress','physics-progress','first-physics',
                 'original-case-index','original-bank','output-dir'):
        p.add_argument('--'+name,type=Path,required=True)
    result=run(p.parse_args())
    if not all(result[k] for k in ('all_original_phase_fields_and_stops_pass','all_original_final_QT_physics_pass',
                                   'all_original_phase_unit_domains_pass')):raise SystemExit(1)
