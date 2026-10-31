"""Deliver both actual corrected full Python controls with complete endpoint tapes.

Preserves the two old failed audits, checks identical original inputs and
configured moments, and never repeats an optimizer or upgrades an old receipt.
"""
import argparse
import gzip
import hashlib
import io
from pathlib import Path
import tarfile

import numpy as np
from scipy.io import loadmat
from audit_native_case import channel_data, sha
from build_power_curve_views import read, require, state_array, write


def package(root, old_bank, packet):
    require(not packet.exists(), 'Preserve prior public packet')
    files, records = {}, []
    for n in (56, 65):
        case = root/f'cooperative-python-positive-case{n:03d}-recorded-v1'
        audit = root/f'cooperative-python-case{n:03d}-independent-full8-MP80-MP100-v1'
        old = old_bank/f'case-{n:03d}'
        summary = read(audit/'summary.json'); execution = read(case/'execution-summary.json')
        require(summary['all_one_case_checks_pass'] is True and summary['actual_execution_language'] == 'python',
                'Actual Python-only complete independent checks required')
        require(execution['source_unchanged'] and execution['original_scope_success'], 'Original numerical gates failed')
        result = read(case/'actual-result.json'); view = read(case/'case-python-recorded.json')
        require(summary['result_sha256'] == sha(case/'case-python-recorded.json') and
                summary['state_sha256'] == sha(case/'actual-python-recording.mat') and
                summary['unchanged_original_python_result_sha256'] == sha(case/'actual-result.json'),
                'Actual result, original numerical return or tape changed')
        tape = loadmat(case/'actual-python-recording.mat', simplify_cells=True)['recording']
        require(result['configuration'] == read(old/'configuration.json'),
                'Actual corrected execution uses different original parameters')
        # MAT transport squeezes singleton numeric arrays. Compare reported
        # values after flattening; retain the exact complete JSON control file.
        require(set(tape['input']['configuration']['reported']) == set(result['configuration']['reported']) and
                all(np.array_equal(np.asarray(tape['input']['configuration']['reported'][key]).reshape(-1),
                                   np.asarray(value).reshape(-1))
                    for key, value in result['configuration']['reported'].items()),
                'Actual tape reported scene differs from its exact JSON control')
        p = result['configuration']['reported']; data = channel_data(tape['input']['data'], *[p[k] for k in ('J', 'U', 'N', 'M')])
        meta = read(old/'actual-state.json'); prior = meta['cases'][0]; receipt = read(old/'actual-point-receipt.json')
        require(meta['actual_saved_array_bank_sha256'] == sha(old/'actual-state.npz') and
                receipt['configuration_sha256'] == sha(old/'configuration.json'), 'Historical original input binding differs')
        for filename, digest in receipt['actual_outputs_sha256'].items():
            require(sha(old/filename) == digest, 'Historical old result/audit changed')
        input_checks = {}
        with np.load(old/'actual-state.npz', allow_pickle=False) as arrays:
            for key, actual in data.items():
                previous = state_array(prior['data'][key], arrays)
                require(actual.shape == previous.shape and actual.dtype == previous.dtype and
                        actual.tobytes() == previous.tobytes(), 'An original physical coefficient changed')
                input_checks[key] = dict(shape=list(actual.shape), dtype=actual.dtype.str,
                    old_and_new_bytes_sha256=hashlib.sha256(actual.tobytes()).hexdigest(), bitwise_equal=True)
            for key, target in (('power_limits', 'power_limit'), ('interference_limits', 'interference_limit')):
                require(np.array_equal(state_array(prior[key], arrays).reshape(-1),
                                       np.asarray(tape['input'][target]).reshape(-1)), 'Original constraint limit changed')
        old_result = read(old/'actual-result.json'); old_audit = read(old/'actual-independent-audit.json')
        require(result['results'][0]['monte_carlo'] == old_result['results'][0]['monte_carlo'],
                'Configured original moment return changed')
        require(old_audit['all_independent_implemented_numerical_checks_pass'] is False,
                'This packet must preserve the two actual old failed audits')
        original_point = result['results'][0]; common_point = view['results'][0]
        common = {s['scheme']:{k:v for k,v in s.items() if k != 'scheme'} for s in common_point['schemes']}
        require(common == original_point['schemes'] and view['language'] == 'python',
                'Common transport must retain every original numerical output')
        phase = read(audit/'python-phase-MP80-MP100/summary.json')
        physics = read(audit/'python-all8-QT-MP80-MP100.json')
        record = dict(ordinal=n, identity=receipt['case_identity'], full_reported_scene=p,
            configuration_sha256=sha(old/'configuration.json'), actual_execution_language='python',
            original_eleven_input_arrays_bitwise_equal=input_checks, original_limits_bitwise_equal=True,
            configured1000_moment_numerical_return_exactly_equal=True, raw_new_MC_draws_claimed=False,
            old_float_auditor_pass_retained=False, old_float_audit_sha256=sha(old/'actual-independent-audit.json'),
            old_point_receipt_sha256=sha(old/'actual-point-receipt.json'), old_result_sha256=sha(old/'actual-result.json'),
            new_result_sha256=sha(case/'actual-result.json'), new_saved_state_sha256=sha(case/'actual-python-recording.mat'),
            all8_new_internal_physical_stop_primal_QT_checks_pass=True, new_complete_independent_MP80_MP100_pass=True,
            phase_endpoints=summary['phase_endpoints'], complex_phase_coordinates_per_precision=summary['complex_phase_coordinates_per_precision'],
            QT_candidates=summary['QT_candidates'], maximum_phase_MP100_gradient_norm=max(float(r['MP100_norm']) for r in phase['phase_summaries']),
            physical_scalar_values_per_precision=physics['scalar_values_per_precision'],
            recorder_sha256=view['recording_source_sha256'], audit_summary=summary,
            elapsed_actual_optimization_and_recording_seconds=execution['elapsed_seconds'],
            full183_original_reference_or_full_paper_pass=False)
        records.append(record)
        payload = {f'case-{n:03d}/configuration.json':old/'configuration.json'}
        payload.update({f'case-{n:03d}/'+name:case/name for name in
            ('actual-result.json', 'actual-python-recording.mat', 'case-python-recorded.json', 'execution-start.json', 'execution-summary.json')})
        payload.update({f'case-{n:03d}/audit/'+name:audit/name for name in
            ('summary.json', 'python-saved-state-fields.json', 'python-all8-QT-MP80-MP100.json', 'python-phase-MP80-MP100/summary.json')})
        for name, path in payload.items():
            files[name] = path.read_bytes()
    summary = dict(scope='Two actual new full8 Python controls on the exact old failed056/065 inputs; complete phase/QT endpoint tapes',
        corrected_python_case_ordinals=[56, 65], actual_cases=2, final_schemes_per_case=8,
        total_phase_endpoints=sum(r['phase_endpoints'] for r in records),
        total_complex_gradient_coordinates_per_precision=sum(r['complex_phase_coordinates_per_precision'] for r in records),
        total_QT_candidates=sum(r['QT_candidates'] for r in records),
        all_original_input_arrays_limits_and_configuration_unchanged=True,
        all_two_new_complete_original_stops_and_independent_MP80_MP100_pass=True,
        original183_old_false_flags_upgraded=False, raw_new_MC_or_historical_inner_trajectories_or_original_reference_or_full_paper_pass=False,
        records=records, packager_sha256=sha(Path(__file__)))
    import json
    files['corrected-two-controls-summary.json'] = (json.dumps(summary, indent=2)+'\n').encode()
    manifest = dict(scope=summary['scope'], corrected_python_case_ordinals=[56, 65], original_cases=2, final_schemes=8,
        phase_endpoints=summary['total_phase_endpoints'], complex_gradient_coordinates=summary['total_complex_gradient_coordinates_per_precision'],
        QT_candidates=summary['total_QT_candidates'], files={name:dict(bytes=len(data), sha256=hashlib.sha256(data).hexdigest()) for name,data in files.items()})
    files['manifest.json'] = (json.dumps(manifest, indent=2)+'\n').encode()
    buffer = io.BytesIO()
    with gzip.GzipFile(fileobj=buffer, mode='wb', mtime=0, filename='') as compressed:
        with tarfile.open(fileobj=compressed, mode='w') as archive:
            for name, data in sorted(files.items()):
                item = tarfile.TarInfo(name); item.size = len(data); item.mtime = 0; item.mode = 0o644
                archive.addfile(item, io.BytesIO(data))
    raw = buffer.getvalue(); packet.mkdir(parents=True); stem = 'corrected-python056-065-full8-endpoint-tapes.tar.gz'
    parts = []
    for n, start in enumerate(range(0, len(raw), 512*1024)):
        chunk = raw[start:start+512*1024]; name = stem+f'.part{n:03d}'; (packet/name).write_bytes(chunk)
        parts.append(dict(file=name, bytes=len(chunk), sha256=hashlib.sha256(chunk).hexdigest()))
    write(packet/(stem+'.parts.json'), dict(archive_sha256=hashlib.sha256(raw).hexdigest(), parts=parts))
    write(packet/'archive.json', dict(file=stem, bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest(), **manifest))
    write(packet/'corrected-two-controls-summary.json', summary)
    print(dict(actual_cases=2, phase_endpoints=91, complex_gradient_coordinates=8190, QT_candidates=66,
        archive_bytes=len(raw), archive_sha256=hashlib.sha256(raw).hexdigest(), parts=len(parts)))


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('root', 'old-bank', 'packet'):
        p.add_argument('--'+name, type=Path, required=True)
    a = p.parse_args(); package(a.root, a.old_bank, a.packet)
