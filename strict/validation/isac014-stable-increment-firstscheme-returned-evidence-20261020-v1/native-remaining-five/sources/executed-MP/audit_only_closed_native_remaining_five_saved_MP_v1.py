"""Future one-shot consumer of native ord2..6 saved states; never runs a producer."""
from pathlib import Path
import argparse
import copy
import hashlib
import importlib.util
import json
import time
import traceback
from native_remaining_saved_binding_v1 import PLAN_PATH, NAMES, guard_closed_lane, need, put, sha_bytes

def sha(path):
    return sha_bytes(Path(path).read_bytes())

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--admission',type=Path,required=True)
    parser.add_argument('--output-dir',type=Path,required=True)
    args = parser.parse_args()
    plan_raw = PLAN_PATH.read_bytes()
    plan = json.loads(plan_raw)
    admission = json.loads(args.admission.read_bytes())
    need(admission.get('root_admitted_only_closed_native_ord2_to6_saved_MP') is True, 'A future true saved-only root admission is required')
    need(admission.get('prepared_plan_SHA256') == sha_bytes(plan_raw), 'Admission must bind frozen reader plan')
    need(admission.get('allowed_scheme_ordinals') == [2,3,4,5,6], 'Only native ordinals 2..6 are in scope')
    need(args.output_dir.resolve() == Path(plan['fresh_output_directory']).resolve() and not args.output_dir.exists(), 'Do not repeat or overwrite any saved audit')
    expected = plan['future_actual_files']
    pins = admission['actual_closed_file_pins']
    need(set(pins) == set(expected.values()), 'Future admission must bind precisely the listed final evidence files')
    for path,digest in pins.items():
        need(isinstance(digest,str) and len(digest) == 64 and sha(path) == digest, 'Wrong/missing closed actual file: '+path)
    before = {path:sha(path) for path in plan['source_and_input_pins']}
    need(before == plan['source_and_input_pins'], 'Frozen reader/provider/source input changed')
    watched = dict(before)
    watched.update(pins)
    watched[str(PLAN_PATH)] = sha_bytes(plan_raw)
    watched[str(args.admission)] = sha(args.admission)
    journal,lane = guard_closed_lane(plan,{key:Path(expected[key]).read_bytes() for key in ('journal','lane_closure')})
    args.output_dir.mkdir(parents=True,exist_ok=False)
    started = time.perf_counter()
    rows = []
    failure = None
    try:
        module_path = Path(plan['per_scheme_existing_math_entry'])
        spec = importlib.util.spec_from_file_location('native_missing_saved_existing_MP',module_path)
        math = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(math)
        for ordinal,name in NAMES.items():
            prior = plan['exact_completed_prior_schemes'].get(str(ordinal))
            if prior is not None:
                prior_path = Path(prior['report'])
                need(sha(prior_path) == prior['report_SHA256'], 'Completed prior report bytes changed')
                prior_report = json.loads(prior_path.read_bytes())
                need(prior_report['source_input_interval_closed'] and prior_report['source_input_before'] == prior_report['source_input_after'], 'Completed prior report source interval not closed')
                need(prior_report['actual_native_MAT_SHA256'] == pins[expected[f'scheme_{ordinal}_MAT']], 'Prior report is not for the same actual native MAT')
                need(prior_report['all_new_states_physics_feasibility_and_corresponding_gradient_formula_checks_pass'] is True and prior_report['crossprecision_pass'] is True, 'Prior completed science not established')
                previous = json.loads(Path(plan['prior_partial_aggregate']).read_bytes())
                row = next(x for x in previous['actual_schemes'] if x['scheme_ordinal'] == ordinal)
                need(row['report'] == str(prior_path) and row['report_SHA256'] == prior['report_SHA256'] and row['scheme_name'] == name, 'Wrong prior aggregate scope')
                rows.append(copy.deepcopy(row) | dict(exact_completed_MP_report_reused=True,new_MP_calls_for_this_scheme=0))
                continue
            actual_result = json.loads(Path(expected[f'scheme_{ordinal}_result']).read_bytes())
            actual_row = lane['rows'][ordinal-2]
            need(actual_row['ordinal'] == ordinal and actual_row['scheme'] == name, 'Closed native ordinal/name mismatch')
            one_result = actual_result.get('checks',[])
            if not actual_result.get('capture_complete_for_returned_scheme') or len(one_result) != 1 or one_result[0].get('status') != 'executed':
                rows.append(dict(scheme_ordinal=ordinal,scheme_name=name,producer_entry_exit=actual_row['actual_entry_exit'],original_algorithm_full_stop=actual_row['algorithm_full_stop'],saved_state_science_complete=False,scientific_PASS=None,scope='Original failed/partial scheme retained; no synthetic final state, RCG return, or inherited PASS. Available partial states are retained in producer output and are not audited by this complete-return consumer.'))
                continue
            folder = args.output_dir/f'scheme-{ordinal:02d}'
            folder.mkdir(exist_ok=False)
            case = copy.deepcopy(plan)
            case.update(scheme_ordinal=ordinal,scheme_name=name,source_and_input_pins=watched)
            case['actual_inputs'] = dict(journal=expected['journal'],lane_closure=expected['lane_closure'],MAT=expected[f'scheme_{ordinal}_MAT'],result=expected[f'scheme_{ordinal}_result'],scheme_closure=expected[f'scheme_{ordinal}_closure'],scheme_root_closure=expected[f'scheme_{ordinal}_root_closure'],scene=plan['original_scene'],configuration=plan['configuration'])
            math.NATIVE_PLAN = case
            math.OUT = folder
            math.NATIVE_ADMISSION_PATH = args.admission
            code = 0
            try:
                math.run()
            except SystemExit as error:
                need(type(error.code) is int and error.code == 1, 'Unexpected existing-math exit')
                code = 1
            report_path = folder/'ACTUAL_NATIVE_ONE_REMAINING_SCHEME_AND_FINAL_EXISTING_MP80_MP100_V1.json'
            report = json.loads(report_path.read_bytes())
            rows.append(dict(scheme_ordinal=ordinal,scheme_name=name,producer_entry_exit=actual_row['actual_entry_exit'],original_algorithm_full_stop=actual_row['algorithm_full_stop'],saved_state_science_complete=True,scientific_field_and_gradient_formula_PASS=report['all_new_states_physics_feasibility_and_corresponding_gradient_formula_checks_pass'],existing_math_gate_exit=code,returned_inner_blocks=report['returned_inner_blocks'],actual_outer_blocks=report['actual_outer_blocks'],strict_RCG_failed_block_calls=report['strict_RCG_failed_block_calls'],strict_PGA_failed_block_calls=report['strict_PGA_failed_block_calls'],RCG_applicable=ordinal<5,final_joint_gradient_residuals=report['final_joint_state_gradient_residuals'],W_absolute_author_stationarity_gate_assigned=False,report=str(report_path),report_SHA256=sha(report_path)))
    except BaseException as error:
        failure = dict(type=type(error).__name__,message=str(error),traceback=traceback.format_exc(),no_automatic_retry=True)
    after = {path:sha(path) for path in watched}
    closed = watched == after
    complete = len(rows) == 5 and all(row['saved_state_science_complete'] for row in rows)
    science = complete and all(row.get('scientific_field_and_gradient_formula_PASS') is True for row in rows)
    code = 1 if failure or not closed else (0 if science else 2)
    report = dict(schema='actual-only-native-missing-ord2-to6-returned-states-and-final-saved-MP80-MP100-v1',source_input_before=watched,source_input_after=after,source_input_interval_closed=closed,held_producer_exit=journal['actual_child_terminal_exit_code'],original_source_and_input_interval_closed=True,scheme_ordinals=[2,3,4,5,6],new_MP_scheme_ordinals=[4,5,6],exact_completed_MP_scheme_ordinals_reused=[2,3],actual_schemes=rows,scope_complete=complete,all_five_actual_saved_state_physics_feasibility_and_gradient_formula_gates_PASS=science,effective_reader_exit_code=code,retained_host_or_schema_failure=failure,old_completed_firstscheme_not_loaded=True,MP_precisions=[80,100],native_MAT_complex_class_shape_signed_zero_authoritative=True,common_Python64_at_native_states_is_not_captured_native_analytic_vectors=True,NoRIS_only_W_PGA_no_RCG_PASS_invention=True,block_stops_and_final_joint_residuals_remain_separate=True,W_MM_or_relative_stop_not_absolute_KKT_PASS=True,original_reference_dual_language_full_six_or_paper_PASS=False,new_optimization_solver_MC_RNG_trials=0,elapsed_seconds=time.perf_counter()-started)
    output = args.output_dir/'ACTUAL_NATIVE_REMAINING_FIVE_SAVED_MP_SCOPE_CLOSURE_V1.json'
    put(output,report)
    print(json.dumps(dict(report=str(output),SHA256=sha(output),exit_code=code,scope_complete=complete,scientific_field_and_gradient_formula_PASS=science)),flush=True)
    return code

if __name__ == '__main__':
    raise SystemExit(main())
