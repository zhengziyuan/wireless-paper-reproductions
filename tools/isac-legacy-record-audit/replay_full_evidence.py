"""Cold-replay all preserved records and the complete initial physical state.

Exit0 verifies this qualified evidence. It preserves the source/cohort/model
discrepancies and certifies no optimized paper figure or original ensemble.
"""
from datetime import datetime
import argparse
import json
from pathlib import Path
import shutil
import time
import evidence as e
import legacy_fields
import records
import physical_replay


def transport_controls(packet,output):
    packet,output=Path(packet),Path(output);e.require(not output.exists(),'Keep prior complete transport-control fixtures');output.mkdir();controls=[]
    def reject(name,mutate):
        target=output/name;shutil.copytree(packet,target);manifest=e.read(target/'archive-manifest.json');mutate(target,manifest)
        e.write(target/'archive-manifest.json',manifest)
        try:e.checked_archive(target)
        except (ValueError,OSError,EOFError) as error:
            controls.append(dict(control=name,rejected=True,reason=str(error),actual_modified_manifest_SHA256=e.sha(target/'archive-manifest.json')));return
        raise AssertionError('Invalid complete preserved-record transport accepted: '+name)
    def corrupt(target,manifest):
        path=target/manifest['archive']['parts'][0]['file'];raw=bytearray(path.read_bytes());raw[len(raw)//2]^=1;path.write_bytes(raw)
    def omit(target,manifest):
        path=target/manifest['archive']['parts'][0]['file'];e.require(path.resolve().is_relative_to(target.resolve()),'Fixture path escaped its own fresh directory')
        path.rename(path.with_suffix(path.suffix+'.omitted-control'))
    def unsafe(target,manifest):manifest['files']['../outside-evidence.json']=manifest['files'].pop('scope.json')
    reject('one_archive_part_byte_changed',corrupt)
    reject('one_complete_archive_part_omitted',omit)
    reject('original1000_native_table_scope_reduced',lambda target,m:m.update(actual_saved_native_table_shape=[999,13]))
    reject('unsafe_payload_member_name',unsafe)
    reject('one_complete_required_payload_omitted',lambda target,m:m['files'].pop('scope.json'))
    reject('legacy_records_mislabeled_as_full_paper_pass',lambda target,m:m.update(full_original_model_algorithm_reference_or_six_paper_pass=True))
    e.require(len(controls)==6,'All six complete transport/source-scope controls are required')
    return dict(actual_negative_controls=6,all_expected_complete_transport_and_scope_controls_rejected=True,controls=controls)


def run(packet,output):
    packet,output=Path(packet).resolve(),Path(output).resolve();e.require(not output.exists(),'Keep prior complete, partial and failed public replay epochs')
    output.mkdir(parents=True);started=time.perf_counter();tool=Path(__file__).resolve().parent
    manifest=e.read(packet/'archive-manifest.json')
    sources=[tool/name for name in ('evidence.py','legacy_fields.py','records.py','physical_replay.py','replay_full_evidence.py','requirements.txt')]
    sources+=[Path(legacy_fields.ref.__file__),packet/'archive-manifest.json']
    sources+=[packet/part['file'] for part in manifest['archive']['parts']]
    before={str(path):e.sha(path) for path in sources}
    e.restore(packet,output/'restored')
    e.write(output/'progress.json',dict(phase='complete17_preserved_record_and_reference_payloads_restored',original_optimizer_calls=0))
    record_report,record_context=records.replay(output/'restored',output/'fresh-records')
    e.write(output/'progress.json',dict(phase='all13000_saved_table_values138_numeric_variables_and_original_grid_values_replayed',original_optimizer_calls=0))
    record_controls=records.controls(record_context,output/'record-controls')
    physical_report,physical_context=physical_replay.replay(output/'restored',record_context,output/'fresh-physical')
    physical_controls=physical_replay.controls(physical_context,output/'physical-controls')
    transport=transport_controls(packet,output/'transport-controls')
    e.write(output/'actual6-transport-and-source-scope-controls.json',transport)
    e.check_restored(packet,output/'restored');after={path:e.sha(path) for path in before}
    e.require(before==after,'A public source, input packet or sealed reference changed during the complete replay')
    e.require(record_controls['actual_negative_controls']+physical_controls['actual_negative_controls']+transport['actual_negative_controls']==27,
        'Every complete field, source-cohort, table, grid and transport negative control is required')
    report=dict(observed_local=datetime.now().astimezone().isoformat(),scope=e.SCOPE,
        actual_complete_native_table_shape=[1000,13],actual_complete_native_binary64_values=13000,
        actual_distinct_original_CSV_rows=20,actual_saved_initial_numeric_variables=138,
        actual_full_fresh_physical_matrices_per_precision=11,actual_fresh_matrix_real_imag_coordinates_per_precision=7940,
        actual_complete_physical_scalar_metrics_per_precision=69,
        actual_original_saved_physical_coordinates_per_precision=772,actual_original_saved_metrics_per_precision=69,
        every_complete_given_record_source_declaration_and_initial_physical_field_replay_pass=True,
        actual_negative_controls=27,all_expected_invalid_complete_fields_records_cohorts_grids_and_transport_controls_rejected=True,
        actual_control_counts=dict(complete_records_source_and_grids=14,complete_physical_fields=7,transport_and_scope=6),
        records=record_report,physical=physical_report,
        actual_fresh_original_optimizer_initializer_sampler_native_MAT_export_or_author_source_calls=0,
        actual_fresh_full_archived_source_MAT_or_publisher_documents_read=0,
        retained_local_whole49_source_binding_and_four_successful_readers_are_not_fresh_CI_source_inspection=True,
        original_source_generation_recipe_model_conformance_reference_dual_language_or_full_six_paper_pass=False,
        source_before=before,source_after=after,elapsed_seconds=time.perf_counter()-started)
    e.write(output/'summary.json',report)
    e.write(output/'progress.json',dict(phase='all_complete_qualified_record_and_field_replay_and27_controls_closed',summary_SHA256=e.sha(output/'summary.json')))
    print(json.dumps({key:value for key,value in report.items() if key not in ('source_before','source_after','records','physical')}),flush=True)
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--packet',type=Path,default=Path(__file__).resolve().parents[2]/'strict/validation/isac-preserved49-legacy-records-20261018')
    parser.add_argument('--output-dir',type=Path,required=True)
    args=parser.parse_args();run(args.packet,args.output_dir)
