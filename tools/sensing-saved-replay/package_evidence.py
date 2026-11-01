"""Publish the actual6000 saved-state audit and nine replayable state witnesses."""
import argparse
import gzip
import hashlib
import io
import json
from pathlib import Path
import tarfile

import audit_population as ref


def signature(data):
    return dict(bytes=len(data), sha256=ref.sha(data))


def package(bank, audit, native_bank, native_audit, packet):
    ref.require(not packet.exists(), 'Preserve previous public evidence')
    report = ref.read(audit/'summary.json')
    ref.require(report['full6000_population_checked'] and report['checked_starts'] == 6000 and
                report['all_checked_saved_fields_KKT_flags_and_stop_decisions_match'], 'Complete actual independent audit required')
    ref.require(report['input_sha256']['auditor'] == ref.sha(Path(ref.__file__).read_bytes()), 'Actual full auditor source changed')
    manifest = ref.read(bank/'manifest.json'); references = {r['start']:r for r in report['records']}
    files = {'actual-all6000-independent-report.json':(audit/'summary.json').read_bytes(),
             'actual-io-wrapper-receipt.json':(audit/'io-wrapper-receipt.json').read_bytes(),
             'original-Python-execution-summary.json':(bank/'execution-summary.json').read_bytes(),
             'original-Python-manifest.json':(bank/'manifest.json').read_bytes(),
             'original-settings.json':(native_bank/'original-settings.json').read_bytes()}
    witnesses = []
    for n in (1, 2, 369, 377, 405, 851):
        raw = (bank/'starts'/f'point-0000-start-{n:04d}.json.gz').read_bytes()
        ref.require(ref.sha(raw) == references[n]['raw_saved_record_sha256'], 'Actual selected raw state differs')
        record = json.loads(gzip.decompress(raw))
        compact = {k:v for k,v in record.items() if k != 'history'}
        compact['history'] = [{k:v for k,v in outer.items() if k != 'inner'} for outer in record['history']]
        witnesses.append(dict(language='python', original_start=n, actual_raw_gzip_sha256=ref.sha(raw),
            view='All actual final numerical fields and all outer stop headers; inner iteration logs stay in the original raw archive', record=compact))
    plan = ref.read(native_bank/'native-population-plan.json')
    native = []
    for n in (1, 2):
        receipt_path = native_bank/'starts'/f'start-{n:04d}-receipt.json'; receipt = ref.read(receipt_path)
        checked = ref.read(native_audit/f'start-{n:04d}-independent.json')
        ref.require(checked['all_saved_state_checks_pass'] and checked['native_receipt_sha256'] == ref.sha(receipt_path.read_bytes()),
                    'Actual closed native state audit differs')
        raw = (native_bank/'starts'/receipt['payload_file']).read_bytes()
        ref.require(ref.sha(raw) == receipt['payload_gzip_sha256'], 'Actual native payload differs')
        files[f'native/start-{n:04d}.json.gz'] = raw
        files[f'native/start-{n:04d}-receipt.json'] = receipt_path.read_bytes()
        files[f'native/start-{n:04d}-independent.json'] = (native_audit/f'start-{n:04d}-independent.json').read_bytes()
        native.append(dict(original_start=n, file=f'native/start-{n:04d}.json.gz',
            raw_json_sha256=receipt['payload_original_json_sha256'], actual_new_optimizer_executed=True,
            actual_settings_seed=plan['cases'][n-1]['initial_rng_before'], raw_dispatcher_start=1))
    reused = plan['reused_case']; raw = Path(reused['file']).read_bytes()
    ref.require(ref.sha(raw) == reused['sha256'], 'Reused actual377 raw receipt differs')
    files['native/start-0377-reused.json.gz'] = gzip.compress(raw, mtime=0)
    files['native/start-0377-actual-binding.json'] = Path(reused['binding_file']).read_bytes()
    native.append(dict(original_start=377, file='native/start-0377-reused.json.gz', raw_json_sha256=ref.sha(raw),
        actual_new_optimizer_executed=False, actual_settings_seed=plan['original_seed'], raw_dispatcher_start=377))
    files['six-Python-state-views.json'] = (json.dumps(witnesses, indent=2)+'\n').encode()
    init = {k:v for k,v in plan.items() if k not in ('repository', 'frozen_binding_base', 'frozen_binding', 'scientific_package', 'reused_case')}
    init['reused_case'] = {k:v for k,v in reused.items() if k not in ('file', 'binding_file')}
    init['native_state_witnesses'] = native
    init['local_full_native_progress_is_not_completion'] = True
    files['exact-original-initialization-index.json'] = (json.dumps(init, indent=2)+'\n').encode()
    summary = {k:v for k,v in report.items() if k != 'records'}
    summary.update(complete_raw6000_numeric_states_publicly_included=False,
        publicly_replayable_Python_final_states=6, publicly_replayable_native_final_states=3,
        native_new_optimizer_witnesses=2, native_actual_prior377_reused_witnesses=1,
        source_normalization_and_historical_reference_recovered=False)
    packet.mkdir(parents=True)
    stream = io.BytesIO()
    with gzip.GzipFile(fileobj=stream, mode='wb', mtime=0, filename='') as compressed:
        with tarfile.open(fileobj=compressed, mode='w') as archive:
            for name,data in sorted(files.items()):
                item = tarfile.TarInfo(name); item.size = len(data); item.mode = 0o644; item.mtime = 0
                archive.addfile(item, io.BytesIO(data))
    payload = stream.getvalue(); stem = 'all6000-audit-and-nine-actual-states.tar.gz'; parts = []
    for n,start in enumerate(range(0, len(payload), 512*1024)):
        chunk = payload[start:start+512*1024]; name = stem+f'.part{n:03d}'; (packet/name).write_bytes(chunk)
        parts.append(dict(file=name, **signature(chunk)))
    transport = dict(archive=dict(filename=stem, **signature(payload), parts=parts),
        files={name:signature(data) for name,data in files.items()}, scope='Actual all6000 audit report plus nine actual final-state witnesses',
        all6000_raw_state_population_included=False, original_complete_convergence_or_reference_pass=False)
    ref.write(packet/'archive-manifest.json', transport); ref.write(packet/'actual-all6000-audit-summary.json', summary)
    print(json.dumps(dict(archive_bytes=len(payload), archive_sha256=ref.sha(payload), parts=len(parts), payload_files=len(files),
        all6000_audited=True, public_state_witnesses=9, all6000_original_convergence_pass=False)))


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('bank', 'audit', 'native-bank', 'native-audit', 'packet'):
        p.add_argument('--'+name, type=Path, required=True)
    a = p.parse_args(); package(a.bank, a.audit, a.native_bank, a.native_audit, a.packet)
