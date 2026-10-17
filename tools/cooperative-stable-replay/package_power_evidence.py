"""Package the verified24-case paired final states, curves and unfitted diagnostics."""
import argparse
import gzip
import hashlib
import io
from pathlib import Path
import tarfile

from audit_native_case import sha
from build_power_curve_views import read, require, write


def package(directory, packet):
    require(not packet.exists(), 'Preserve prior public packet')
    require(read(directory/'independent-all384-final-states-MP80-MP100.json')['all384_final_states_physics_and_precision_pass'],
            'All384 actual final states must pass independent physics')
    require(read(directory/'independent-NoRIS-input-bound-MP80-MP100.json')['all_bound_evaluations_and_source_bindings_pass'],
            'Independent fixed-input bound must pass')
    require(read(directory/'build-receipt.json')['all24_original_slots_and_all_eight_schemes'], 'All original slots required')
    files = {}
    for path in sorted(directory.rglob('*')):
        if not path.is_file():
            continue
        require(path.suffix in ('.json', '.npz', '.png', '.svg'), 'No private EPS, manuscripts or logs in public packet')
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
    raw = buffer.getvalue(); stem = 'power24-dual-final-states-and-curves.tar.gz'
    parts = []
    for n, start in enumerate(range(0, len(raw), 512*1024)):
        chunk = raw[start:start+512*1024]; name = stem+f'.part{n:03d}'
        (packet/name).write_bytes(chunk)
        parts.append(dict(file=name, bytes=len(chunk), sha256=hashlib.sha256(chunk).hexdigest()))
    manifest = dict(scope='Actual24 paired full power-sweep cases, all384 final states and independent reference diagnostics',
        languages=['python', 'matlab'], power_cases_per_language=24, schemes_per_case=8, total_final_states=384,
        archive=dict(filename=stem, bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest(), parts=parts),
        files={name:dict(bytes=len(data), sha256=hashlib.sha256(data).hexdigest()) for name, data in files.items()},
        packager_sha256=sha(Path(__file__)), full_phase_QT_tapes_publicly_included=False,
        original_private_EPS_redistributed=False, original_curve_or_full_paper_pass=False)
    write(packet/'archive-manifest.json', manifest)
    for source in ('dual-language-comparison.json', 'build-receipt.json'):
        doc = read(directory/source)
        if 'records' in doc:
            doc.pop('records')
        write(packet/source.replace('.json', '-summary.json'), doc)
    write(packet/'original-reference-summary.json', read(directory/'reference-comparison/original-reference-summary.json'))
    for source, wanted in (
        ('independent-all384-final-states-MP80-MP100.json', ('lanes', 'source_input_sha256')),
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
