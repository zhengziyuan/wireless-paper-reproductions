"""Restore and independently replay the complete source-qualified ISAC evidence.

Exit0 verifies the evidence, including the retained literal-LoS incompatibility.
It does not certify optimized figures, source-equivalent hidden inputs or the
complete six-paper objective. No original optimization or native MC is run.
"""
from __future__ import annotations

import argparse
from datetime import datetime
import json
from pathlib import Path
import shutil
import time

import evidence as e
import geometry_replay
import NoRIS_replay
import physical_states


def transport_controls(packet,output):
    packet,output=Path(packet),Path(output);e.require(not output.exists(),'Preserve all prior invalid-transport fixtures');output.mkdir();controls=[]
    def reject(name,mutate):
        target=output/name;shutil.copytree(packet,target);manifest=e.read(target/'archive-manifest.json');mutate(target,manifest)
        e.write(target/'archive-manifest.json',manifest)
        try:e.checked_archive(target)
        except (ValueError,OSError,EOFError) as error:
            controls.append(dict(control=name,rejected=True,reason=str(error),actual_modified_manifest_SHA256=e.sha(target/'archive-manifest.json')));return
        raise AssertionError('Invalid full original evidence transport accepted: '+name)
    def corrupt(target,manifest):
        path=target/manifest['archive']['parts'][0]['file'];raw=bytearray(path.read_bytes());raw[len(raw)//2]^=1;path.write_bytes(raw)
    def omit(target,manifest):
        path=target/manifest['archive']['parts'][0]['file'];e.require(path.resolve().is_relative_to(target.resolve()),'A fixture part escaped its own fresh directory')
        path.rename(path.with_suffix(path.suffix+'.omitted-control'))
    reject('one_complete_archive_part_byte_changed',corrupt)
    reject('one_complete_archive_part_omitted',omit)
    reject('original11200_scene_scope_reduced',lambda target,m:m.update(actual_original_scenes=11199))
    def unsafe(target,m):m['files']['../outside-evidence.json']=m['files'].pop('scope.json')
    reject('unsafe_payload_member_name',unsafe)
    reject('one_complete_required_payload_missing',lambda target,m:m['files'].pop('scope.json'))
    reject('original_archive_part_order_substituted',lambda target,m:m['archive']['parts'].__setitem__(1,m['archive']['parts'][0]))
    e.require(len(controls)==6,'Every complete-transport control is required')
    return dict(actual_negative_controls=6,all_expected_invalid_transport_or_complete_scope_controls_rejected=True,controls=controls)


def run(packet,output):
    packet,output=Path(packet).resolve(),Path(output).resolve()
    e.require(not output.exists(),'Choose a fresh complete replay directory; all partial/failed epochs stay preserved')
    output.mkdir(parents=True);started=time.perf_counter()
    tool=Path(__file__).resolve().parent
    sources=[tool/name for name in ('evidence.py','exact_geometry.py','physical_states.py','geometry_replay.py','NoRIS_replay.py','replay_full_evidence.py')]
    sources += [Path(physical_states.ref.__file__),packet/'archive-manifest.json']
    manifest=e.read(packet/'archive-manifest.json');sources += [packet/p['file'] for p in manifest['archive']['parts']]
    before={str(p):e.sha(p) for p in sources}
    manifest=e.restore(packet,output/'restored')
    e.write(output/'progress.json',dict(phase='all_complete_primitive_and_saved_state_payloads_restored',actual_payload_files=len(manifest['files']),
        actual_original_scenes=11200,actual_original_first_user_pairs=23900,actual_original_optimizers_called=0))
    geometry,geometry_context=geometry_replay.replay(output/'restored')
    e.write(output/'complete-original11200-and23900-geometry-replay.json',geometry)
    e.write(output/'progress.json',dict(phase='every_original_primitive_and_exact_geometry_row_replayed',geometry=geometry))
    geometry_controls=geometry_replay.controls(geometry_context,output/'exact-geometry-controls')
    e.write(output/'actual17-exact-geometry-controls.json',geometry_controls)
    physical,physical_context=NoRIS_replay.replay(output/'restored',output/'fresh-NoRIS')
    e.write(output/'complete-four-NoRIS-source-variant-field-replay.json',physical)
    physical_controls=NoRIS_replay.controls(physical_context,output/'NoRIS-field-controls')
    e.write(output/'actual9-NoRIS-field-controls.json',physical_controls)
    transport=transport_controls(packet,output/'transport-controls')
    e.write(output/'actual6-transport-controls.json',transport)
    e.check_restored(packet,output/'restored')
    e.require(before=={p:e.sha(p) for p in before},'A source/packet byte changed during the full original evidence replay')
    report=dict(observed_local=datetime.now().astimezone().isoformat(),scope=e.SCOPE,
        actual_complete_original_scene_primitive_rows=11200,actual_complete_original_user_first_ray_pairs=23900,
        actual_full_primitive_coordinate_observations=322600,actual_saved_NoRIS_states=4,
        actual_complete_NoRIS_field_coordinates_per_precision={'80':61056,'100':61056},
        every_complete_primitive_geometry_and_fresh_NoRIS_field_replay_pass=True,
        actual_negative_controls=32,all_expected_invalid_support_geometry_fields_source_scope_and_transport_controls_rejected=True,
        geometry=geometry,NoRIS=physical,actual_control_counts=dict(exact_geometry=17,NoRIS_fields=9,transport=6),
        actual_fresh_original_optimizers_initializers_samplers_or_native_MC_streams=0,
        actual_fresh_full_optimizer_scenario_files_read=2,actual_fresh_full_optimizer_result_histories_read=0,
        actual_fresh_author_or_publisher_full_source_documents_read=0,
        literal_first_LoS_geometry_conformance_pass=False,
        author_hidden_input_recovery_original_reference_performance_dual_language_or_full_six_paper_pass=False,
        source_before=before,source_after={p:e.sha(p) for p in before},elapsed_seconds=time.perf_counter()-started)
    e.write(output/'summary.json',report)
    e.write(output/'progress.json',dict(phase='all_complete_original_evidence_replay_and_controls_closed',summary_SHA256=e.sha(output/'summary.json')))
    print(json.dumps({k:v for k,v in report.items() if k not in ('geometry','NoRIS','source_before','source_after')}),flush=True)
    return report


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--packet',type=Path,default=Path(__file__).resolve().parents[2]/'strict/validation/isac-full11200-source-geometry-20261018')
    p.add_argument('--output-dir',type=Path,required=True)
    a=p.parse_args();run(a.packet,a.output_dir)
