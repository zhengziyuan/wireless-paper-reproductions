"""Package complete paired final states, curves and unfitted diagnostics."""
import argparse
import gzip
import hashlib
import io
from pathlib import Path
import tarfile

from audit_native_case import sha
from build_power_curve_views import SCOPES, read, require, write


def package(directory, packet):
    require(not packet.exists(), 'Preserve prior public packet')
    index=read(directory/'final-state-index.json');scope=index.get('case_scope','power')
    require(scope in SCOPES, 'Only exact complete source cohorts are supported')
    _, ordinals, _, figures = SCOPES[scope]
    count = len(ordinals); states = count*16
    require(index['expected_cases_per_language'] == count and index['expected_schemes_per_case'] == 8 and
            index['expected_case_ordinals'] == ordinals and index['original_source_figures'] == figures,
            'The exact source cohort differs')
    math_file = f'independent-all{states}-final-states-MP80-MP100.json'
    math_report = read(directory/math_file)
    require(math_report.get('all_final_states_physics_and_precision_pass',
                           math_report.get('all384_final_states_physics_and_precision_pass')) and
            math_report['cases_per_language'] == count and math_report['actual_final_states_per_precision'] == states,
            'Every actual final state must pass independent physics')
    require(read(directory/'independent-NoRIS-input-bound-MP80-MP100.json')['all_bound_evaluations_and_source_bindings_pass'],
            'Independent fixed-input bound must pass')
    build = read(directory/'build-receipt.json')
    require(build.get('all_original_slots_and_all_eight_schemes', build.get('all24_original_slots_and_all_eight_schemes')),
            'All original slots required')
    if scope == 'subsurfaces':
        require(build['explicitly_selected_repaired_Python_case_ordinals'] == [56,65],
                'Both separately audited corrected epochs must be explicit')
    if scope=='interference':
        require(read(directory/'case047-phase-witness/independent-cross-evaluation-MP80-MP100.json')['all_saved_phase_and_precision_checks_pass'],
                'Preserve and independently check the divergent actual endpoints')
        require(read(directory/'case047-same-native-data-phase-controls/independent-controls-MP80-MP100.json')['all_fields_strict_original_stops_and_precision_pass'],
                'Both prospective isolated same-data controls must retain the original stops')
    files = {}
    for path in sorted(directory.rglob('*')):
        if not path.is_file():
            continue
        require(path.suffix in ('.json', '.npz', '.mat', '.png', '.svg'), 'No private EPS, manuscripts or logs in public packet')
        name = path.relative_to(directory).as_posix()
        files[name] = path.read_bytes()
    require(all(name in files for name in ('final-states.npz', 'final-state-index.json',
        'python-curve-view.json', 'matlab-curve-view.json', 'reference-comparison/original-reference-summary.json')),
        'Incomplete real numerical packet')
    packet.mkdir(parents=True)
    buffer = io.BytesIO()
    with gzip.GzipFile(fileobj=buffer, mode='wb', mtime=0, filename='') as compressed:
        with tarfile.open(fileobj=compressed, mode='w') as archive:
            for name, data in files.items():
                item = tarfile.TarInfo(name); item.size = len(data); item.mtime = 0; item.mode = 0o644
                archive.addfile(item, io.BytesIO(data))
    raw = buffer.getvalue(); stem = scope+str(count)+'-dual-final-states-and-curves.tar.gz'
    parts = []
    for n, start in enumerate(range(0, len(raw), 512*1024)):
        chunk = raw[start:start+512*1024]; name = stem+f'.part{n:03d}'
        (packet/name).write_bytes(chunk)
        parts.append(dict(file=name, bytes=len(chunk), sha256=hashlib.sha256(chunk).hexdigest()))
    manifest = dict(scope=f'Actual{count} paired full {scope}-sweep cases, all{states} final states and independent reference diagnostics',
        case_scope=scope, exact_original_case_ordinals=ordinals, original_source_figures=figures,
        languages=['python', 'matlab'], cases_per_language=count, schemes_per_case=8, total_final_states=states,
        archive=dict(filename=stem, bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest(), parts=parts),
        files={name:dict(bytes=len(data), sha256=hashlib.sha256(data).hexdigest()) for name, data in files.items()},
        packager_sha256=sha(Path(__file__)), full_phase_QT_tapes_publicly_included=False,
        original_private_EPS_redistributed=False, original_curve_or_full_paper_pass=False)
    if scope=='power':manifest['power_cases_per_language']=24
    write(packet/'archive-manifest.json', manifest)
    for source in ('dual-language-comparison.json', 'build-receipt.json'):
        doc = read(directory/source)
        if 'records' in doc:
            doc.pop('records')
        write(packet/source.replace('.json', '-summary.json'), doc)
    write(packet/'original-reference-summary.json', read(directory/'reference-comparison/original-reference-summary.json'))
    for source, wanted in (
        (math_file, ('lanes', 'source_input_sha256')),
        ('independent-NoRIS-input-bound-MP80-MP100.json', ('lanes', 'comparisons', 'source_input_sha256'))):
        doc = read(directory/source)
        for key in wanted:
            doc.pop(key)
        doc['full_detail_file_in_archive'] = source
        doc['full_detail_sha256'] = sha(directory/source)
        write(packet/source.replace('.json', '-summary.json'), doc)
    print(dict(archive_bytes=len(raw), archive_sha256=manifest['archive']['sha256'], parts=len(parts), files=len(files)))


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--directory', type=Path, required=True); p.add_argument('--packet', type=Path, required=True)
    a = p.parse_args(); package(a.directory, a.packet)
