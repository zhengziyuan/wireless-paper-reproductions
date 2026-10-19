"""Restore all evidence bytes and independently replay the nine public witnesses.

The complete6000 audit report is checked for full source-slot coverage. Only
the nine included actual final states are numerically replayed by this command;
the external full6000 raw bank remains required for that complete replay.
"""
import argparse
import gzip
import io
import json
from pathlib import Path, PurePosixPath
import tarfile

import audit_population as ref


def safe(name):
    return name and not PurePosixPath(name).is_absolute() and '..' not in PurePosixPath(name).parts and ':' not in name and '\\' not in name


def replay(packet, output):
    ref.require(not output.exists(), 'Preserve previous public replay')
    manifest = ref.read(packet/'archive-manifest.json'); spec = manifest['archive']; chunks = []
    for n,part in enumerate(spec['parts']):
        ref.require(safe(part['file']) and part['file'] == spec['filename']+f'.part{n:03d}', 'Unsafe/unordered archive part')
        raw = (packet/part['file']).read_bytes()
        ref.require(len(raw) == part['bytes'] and ref.sha(raw) == part['sha256'], 'Archive part differs')
        chunks.append(raw)
    raw = b''.join(chunks); ref.require(len(raw) == spec['bytes'] and ref.sha(raw) == spec['sha256'], 'Whole archive differs')
    files = {}
    with tarfile.open(fileobj=io.BytesIO(raw), mode='r:gz') as archive:
        for member in archive:
            ref.require(safe(member.name) and member.isfile() and member.name not in files and member.name in manifest['files'], 'Unsafe/duplicated/unexpected payload')
            data = archive.extractfile(member).read(); wanted = manifest['files'][member.name]
            ref.require(len(data) == wanted['bytes'] and ref.sha(data) == wanted['sha256'], 'Evidence payload differs')
            files[member.name] = data
    ref.require(set(files) == set(manifest['files']), 'Missing public evidence payload')
    output.mkdir(parents=True)
    for name,data in files.items():
        path = output/'restored'/name; path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes(data)
    complete = json.loads(files['actual-all6000-independent-report.json']); rows = complete['records']
    ref.require([r['start'] for r in rows] == list(range(1, 6001)) and
        all(r['all_saved_record_checks_pass'] for r in rows) and complete['checked_starts'] == 6000,
        'Complete actual6000 audit report missing or failed')
    ref.require(sum(r['original_convergence_pass_retained'] for r in rows) == complete['original_convergence_pass_starts'] == 5251 and
        sum(r['independent_final_KKT']['original_problem_kkt_verified'] for r in rows) == complete['independent_final_KKT_pass_starts'] == 5959,
        'Actual original failed slots were omitted or upgraded')
    settings = json.loads(files['original-settings.json']); response, indices, beta, noise, gap = ref.basis(settings, dict(ms1=[20,20], ms2=[16,16], Kphi=3, Ktheta=3))
    witnesses = json.loads(files['six-Python-state-views.json']); cases = []
    ref.require([r['original_start'] for r in witnesses] == [1,2,369,377,405,851], 'All six original Python witnesses required')
    for item in witnesses:
        record = item['record']; n = item['original_start']
        ref.require(item['actual_raw_gzip_sha256'] == rows[n-1]['raw_saved_record_sha256'], 'Actual Python witness bound to another original state')
        result = ref.physical(record, response, indices, beta, noise, settings)
        cases.append(dict(language='python', original_start=n, **result))
    plan = json.loads(files['exact-original-initialization-index.json']); prime=2147483647
    ref.require([r['original_start'] for r in plan['cases']] == list(range(1,6001)), 'Complete original initialization stream required')
    for case in plan['cases']:
        n = case['original_start']; before = plan['original_seed']*pow(16807, (n-1)*881, prime) % prime
        after = before*pow(16807, 881, prime) % prime
        ref.require((before, after) == (case['initial_rng_before'], case['initial_rng_after']), 'An original serial RNG jump differs')
    for item in plan['native_state_witnesses']:
        decoded = gzip.decompress(files[item['file']]); ref.require(ref.sha(decoded) == item['raw_json_sha256'], 'Actual native JSON bytes differ')
        doc = json.loads(decoded); current = json.loads(json.dumps(doc['settings']))
        ref.require(current['initialization']['seed'] == item['actual_settings_seed'] and doc['start'] == item['raw_dispatcher_start'], 'Native original initialization mapping differs')
        current['initialization']['seed'] = settings['initialization']['seed']; ref.require(current == settings, 'Native physical/solver control changed')
        common = dict(state=doc['state'], metrics=doc['metrics'], summary=dict(solver_status=doc['solver_status']))
        result = ref.physical(common, response, indices, beta, noise, settings)
        cases.append(dict(language='matlab', original_start=item['original_start'], actual_new_optimizer_executed=item['actual_new_optimizer_executed'], **result))
    require_keys = ('saved_physical_fields_match', 'saved_KKT_residual_fields_match', 'saved_KKT_boolean_reconfirmed')
    passed = len(cases) == 9 and all(all(c[k] for k in require_keys) for c in cases)
    report = dict(scope='Complete6000 report integrity plus nine actual saved-state physical/KKT replays; no optimizer',
        all6000_report_slots_and_original_flags_present=True, publicly_replayed_actual_states=9, all_nine_state_replays_pass=passed,
        all6000_original_serial_initialization_jumps_checked=True, original_pass5251_and_failed749_counts_unchanged=True,
        response_MP80_MP100_maximum_difference=gap, cases=cases, optimizer_or_random_generator_calls=0,
        complete6000_raw_state_numeric_replay_performed=False, full6000_convergence_or_reference_or_paper_pass=False,
        archive_sha256=spec['sha256'], actual_replayer_sha256=ref.sha(Path(__file__).read_bytes()),
        physical_reference_sha256=ref.sha(Path(ref.__file__).read_bytes()))
    ref.write(output/'actual-public-replay.json', report); print(json.dumps({k:v for k,v in report.items() if k != 'cases'}))
    if not passed:
        raise SystemExit(1)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__); p.add_argument('--packet', type=Path, required=True)
    p.add_argument('--output-dir', type=Path, required=True); a=p.parse_args(); replay(a.packet, a.output_dir)
