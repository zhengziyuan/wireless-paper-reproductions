"""Package all72 actual paired cases only after full physics and actual plot QA."""
import argparse
import gzip
import hashlib
import io
from pathlib import Path
import tarfile

from audit_native_case import sha
from build_power_curve_views import read, require, write


def package(directory,packet):
    require(not packet.exists(),'Preserve prior public packet')
    index=read(directory/'final-state-index.json')
    require(index['case_scope']=='multi-single' and index['expected_case_ordinals']==list(range(111,183)) and
            index['original_source_figures']==[11] and index['expected_cases_per_language']==72 and
            index['expected_schemes_per_case']==8,'The exact complete72 original paired slots are required')
    math_file='independent-all1152-final-states-MP80-MP100.json'
    physics=read(directory/math_file)
    require(physics['all_final_states_physics_and_precision_pass'] and
            physics['actual_final_states_per_precision']==1152 and
            physics['scalar_field_coordinates_per_precision']==7680,
            'All actual paired final states must pass unchanged independent physical criteria')
    scene=read(directory/'multi-single-scene-binding.json')
    require(scene['all_actual_scenes_have48_total_antennas_and150W'] and
            scene['physical_scalar_fields_per_precision']==7680 and
            scene['source_reference_ordinates_per_language']==144,
            'Both original J1/J3 scenes and their different physical field counts are required')
    build=read(directory/'build-receipt.json')
    require(build['all_original_slots_and_all_eight_schemes'] and build['cases_per_language']==72 and
            build['native_phase_QT_and_configured_MC_receipts_checked']==72,
            'Every original native phase/QT/configured-moment binding must be retained')
    provenance=read(directory/'source-and-audit-bindings.json')['records']
    require([p['identity']['ordinal'] for p in provenance]==list(range(111,183)) and
            all(p['native_configuration_transport']['every_numeric_value_unchanged'] and
                p['native_configuration_transport']['original_result_modified'] is False for p in provenance),
            'Every source configuration and exact singleton transport must preserve original values/bytes')
    reference=read(directory/'reference-comparison/original-reference-summary.json')
    require(reference['source_points_per_language']==144 and
            reference['source_interference_W_versus_normalized_I_over_N_conflict_unresolved'] is True and
            len(reference['comparisons'])==2 and all(c['points']==144 and c['all_curves_and_grids_complete']
                for c in reference['comparisons']),'All original144 points/language and the unit caveat required')
    controller=read(directory/'actual-closed-evidence-controller.json')
    require(controller['phase']=='complete_numeric_and_internal_rendering_awaiting_actual_visual_QA' and
            controller['all72_native_and_python_paired'] and
            controller['all1152_final_physical_states_MP80_MP100_checked'] and
            len(controller['steps'])==3 and all(s['exit_code']==0 for s in controller['steps']),
            'Actual closed dependency/evidence steps required')
    plotted=read(directory/'source-comparison/multi-single-source-vs-reconstructed.json')
    require(plotted['actual_languages']==['python','matlab'] and
            plotted['complete72_paired_final_physics_checked'] and plotted['source_points']==144 and
            plotted['reconstructed_points']==288 and plotted['source_original_y_range']==[0,14] and
            plotted['source_interference_W_versus_normalized_I_over_N_conflict_unresolved'],
            'Require the actual complete paired diagnostic, not a Python-only layout preflight')
    visual=read(directory/'actual-complete-plot-visual-QA.json')
    require(visual['all_generated_figure11_PNGs_actually_inspected'] and
            visual['all_legend_entries_and_curves_visible'] and
            visual['source_original_y_range_preserved']==[0,14] and
            visual['source_W_vs_normalized_I_over_N_caveat_visible'],
            'Actual complete visual inspection is required before publication')
    pngs={p.relative_to(directory).as_posix():sha(p) for p in directory.rglob('*.png')}
    require(len(pngs)==3 and {p['relative_path']:p['sha256'] for p in visual['plots']}==pngs,
            'Visual QA must bind all three actual new PNG bytes')
    require(plotted['PNG_sha256']==pngs['source-comparison/multi-single-source-vs-reconstructed.png'],
            'Displayed diagnostic differs from its numerical plot receipt')
    files={}
    for path in sorted(directory.rglob('*')):
        if path.is_file():
            require(path.suffix in ('.json','.npz','.mat','.png','.svg'),
                    'Keep private EPS, manuscripts, logs and unrelated files outside the public packet')
            files[path.relative_to(directory).as_posix()]=path.read_bytes()
    buffer=io.BytesIO()
    with gzip.GzipFile(fileobj=buffer,mode='wb',mtime=0,filename='') as compressed:
        with tarfile.open(fileobj=compressed,mode='w') as archive:
            for name,payload in files.items():
                item=tarfile.TarInfo(name);item.size=len(payload);item.mtime=0;item.mode=0o644
                archive.addfile(item,io.BytesIO(payload))
    require(all(sha(directory/name)==hashlib.sha256(payload).hexdigest() for name,payload in files.items()),
            'An original numerical or QA payload changed while packaging')
    packet.mkdir(parents=True)
    raw=buffer.getvalue();stem='multi-single72-dual-final-states-and-curves.tar.gz';parts=[]
    for n,start in enumerate(range(0,len(raw),512*1024)):
        chunk=raw[start:start+512*1024];name=stem+f'.part{n:03d}'
        (packet/name).write_bytes(chunk)
        parts.append(dict(file=name,bytes=len(chunk),sha256=hashlib.sha256(chunk).hexdigest()))
    preview='source-comparison-figure11.png'
    preview_raw=files['source-comparison/multi-single-source-vs-reconstructed.png']
    (packet/preview).write_bytes(preview_raw)
    manifest=dict(case_scope='multi-single',exact_original_case_ordinals=list(range(111,183)),
        original_source_figures=[11],languages=['python','matlab'],cases_per_language=72,schemes_per_case=8,
        total_final_states=1152,physical_scalar_fields_per_precision=7680,
        original_reference_ordinates_per_language=144,source_reference_ordinates_are_72_times8=False,
        source_W_versus_normalized_I_over_N_conflict_unresolved=True,
        archive=dict(filename=stem,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest(),parts=parts),
        files={name:dict(bytes=len(payload),sha256=hashlib.sha256(payload).hexdigest()) for name,payload in files.items()},
        preview_files={preview:dict(bytes=len(preview_raw),sha256=hashlib.sha256(preview_raw).hexdigest())},
        packager_SHA256=sha(Path(__file__)),original_private_EPS_redistributed=False,
        full_phase_QT_and_MC_RAW_tapes_publicly_included=False,
        configured1000_moments_are_author_reported_optimized_performance_MC=False,
        all_native_configuration_metadata_transports_preserve_original_values_and_bytes=True,
        figure11_includes_NoRIS_original_reference_values=False,
        original_reference_or_full183_or_full_paper_pass=False)
    write(packet/'archive-manifest.json',manifest)
    for name in ('dual-language-comparison.json','build-receipt.json','multi-single-scene-binding.json'):
        document=read(directory/name);document.pop('records',None)
        write(packet/name.replace('.json','-summary.json'),document)
    summary=dict(physics)
    summary.pop('lanes');summary.pop('source_input_sha256')
    summary.update(full_detail_file_in_archive=math_file,full_detail_SHA256=sha(directory/math_file))
    write(packet/'independent-all1152-final-states-MP80-MP100-summary.json',summary)
    write(packet/'original-reference-summary.json',reference)
    print(dict(archive_bytes=len(raw),archive_SHA256=manifest['archive']['sha256'],
        parts=len(parts),actual_payloads=len(files),original_reference_points_per_language=144),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--directory',type=Path,required=True)
    p.add_argument('--packet',type=Path,required=True)
    a=p.parse_args();package(a.directory,a.packet)
