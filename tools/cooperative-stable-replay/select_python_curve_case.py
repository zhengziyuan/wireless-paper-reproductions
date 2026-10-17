"""Select saved Python epochs without changing any historical failure receipt.

The two M=45 inputs have separate, completed corrected executions. Selection
requires the exact old inputs, a published independent complete-case receipt,
and an explicit new-epoch provenance record. No numerical solver is called.
"""
from __future__ import annotations

import json
import hashlib
import io
from pathlib import Path
import tarfile

import numpy as np
from scipy.io import loadmat

from audit_native_case import channel_data, sequence, sha


def require(test, message):
    if not test:
        raise ValueError(message)


def read(path):
    return json.loads(path.read_bytes())


def archived_summary(public, bound):
    """Verify the actual LF archive payload and the CRLF presentation copy."""
    manifest = read(public / 'archive.json')
    parts_path = public / (manifest['file'] + '.parts.json')
    bound(parts_path)
    parts = read(parts_path)
    chunks = []
    for index, spec in enumerate(parts['parts']):
        require(spec['file'] == manifest['file'] + f'.part{index:03d}', 'Unexpected original archive part')
        path = public / spec['file']
        bound(path, spec['sha256'])
        raw = path.read_bytes()
        require(len(raw) == spec['bytes'], 'Original archive part size differs')
        chunks.append(raw)
    raw = b''.join(chunks)
    require(len(raw) == manifest['bytes'] and
            hashlib.sha256(raw).hexdigest() == manifest['sha256'] == parts['archive_sha256'],
            'The published complete corrected-epoch archive differs')
    name = 'corrected-two-controls-summary.json'
    with tarfile.open(fileobj=io.BytesIO(raw), mode='r:gz') as archive:
        matches = [m for m in archive.getmembers() if m.name == name]
        require(len(matches) == 1 and matches[0].isfile(), 'Missing/duplicate authoritative summary')
        payload = archive.extractfile(matches[0]).read()
    expected = manifest['files'][name]
    require(len(payload) == expected['bytes'] and hashlib.sha256(payload).hexdigest() == expected['sha256'],
            'The original archived summary bytes differ')
    # The public plain JSON predates * -text and is CRLF; the original archive
    # is LF. Preserve both byte forms and allow only this exact text newline
    # conversion. No numeric value or historical admission flag may differ.
    plain = (public / name).read_bytes()
    require(plain.replace(b'\r\n', b'\n') == payload, 'Plain/archive summary differs beyond text newlines')
    return json.loads(payload), dict(archive_sha256=manifest['sha256'],
        archive_summary_payload_sha256=expected['sha256'], plain_summary_sha256=sha(public / name),
        plain_archive_differ_only_in_CRLF_text_newlines=plain != payload)


def array(value, bank):
    if isinstance(value, dict) and 'recorded_array' in value:
        actual = bank[value['recorded_array']]
        require(list(actual.shape) == value['shape'] and actual.dtype.str == value['dtype'],
                'Stored Python shape/dtype differs from the recorder')
        return actual.copy()
    return np.asarray(value)


def select(identity, old, repaired_root, bound):
    """Return an exact saved case and separate old/new-epoch admission evidence."""
    configuration = old / 'configuration.json'
    bound(configuration, identity['configuration_sha256'])
    config = read(configuration)
    require(config['reported'] == identity['full_reported_scene'], 'Original scene differs')
    bound(old / 'actual-point-receipt.json')
    receipt = read(old / 'actual-point-receipt.json')
    require(receipt['case_identity'] == {k: identity[k] for k in ('ordinal', 'sweep', 'parameter', 'value')},
            'Original case identity differs')
    require(receipt['source_interval_pass'] and receipt['actual_complete_result_returned'],
            'No actual unchanged-source Python return exists')
    for filename, digest in receipt['actual_outputs_sha256'].items():
        bound(old / filename, digest)
    prior_result = read(old / 'actual-result.json')
    prior_meta = read(old / 'actual-state.json')
    prior_audit = read(old / 'actual-independent-audit.json')
    require(prior_result['configuration'] == config and prior_result['source_unchanged_during_run'],
            'Original Python source/configuration interval differs')
    bound(old / 'actual-state.npz', prior_meta['actual_saved_array_bank_sha256'])
    with np.load(old / 'actual-state.npz', allow_pickle=False) as bank:
        prior = prior_meta['cases'][0]
        data = {k: array(v, bank) for k, v in prior['data'].items()}
        power = array(prior['power_limits'], bank)
        limit = array(prior['interference_limits'], bank)
        final = []
        for state in prior['scheme_final_states']:
            item = dict(scheme=state['scheme'], no_ris=state['noRIS'], phi=array(state['phi'], bank))
            for source, dest in (('AP_W', 'W'), ('MR_p', 'p')):
                if state.get(source) is not None:
                    item[dest] = array(state[source], bank)
            final.append(item)
    old_origin = {f: sha(old / f) for f in ('configuration.json', 'actual-result.json', 'actual-state.json',
        'actual-state.npz', 'actual-independent-audit.json', 'actual-point-receipt.json')}
    n = identity['ordinal']
    if n not in (56, 65):
        require(receipt['actual_all_original_gates_pass'] and receipt['actual_independent_state_audit_pass'] and
                prior_audit['all_independent_implemented_numerical_checks_pass'],
                'A failed historical slot requires an explicitly audited separate execution')
        return config, prior_result, data, final, power, limit, old_origin, dict(
            selected_epoch='historical_original_complete_return', historical_failure_flags_modified=False)

    require(repaired_root is not None, 'M=45 slots require the explicit completed repaired-Python root')
    require(identity['sweep'] in ('subsurfaces_kL20', 'subsurfaces_kL0') and
            identity['parameter'] == 'M' and identity['value'] == 45,
            'Corrected selection applies only to the exact two original M=45 slots')
    require(prior_audit['all_independent_implemented_numerical_checks_pass'] is False,
            'Keep the actual historical failed auditor flag')
    case = repaired_root / f'cooperative-python-positive-case{n:03d}-recorded-v1'
    audit = repaired_root / f'cooperative-python-case{n:03d}-independent-full8-MP80-MP100-v1'
    public = Path(__file__).resolve().parents[2] / 'strict/validation/cooperative-corrected-python056-065-20261017'
    for p in (public / 'archive.json', public / 'corrected-two-controls-summary.json',
              case / 'actual-result.json', case / 'actual-python-recording.mat',
              case / 'case-python-recorded.json', case / 'execution-start.json',
              case / 'execution-summary.json', audit / 'summary.json'):
        bound(p)
    published, summary_binding = archived_summary(public, bound)
    row = next(r for r in published['records'] if r['ordinal'] == n)
    summary = read(audit / 'summary.json')
    execution = read(case / 'execution-summary.json')
    result = read(case / 'actual-result.json')
    common = read(case / 'case-python-recorded.json')
    require(row['audit_summary'] == summary and summary['all_one_case_checks_pass'] and
            summary['actual_execution_language'] == 'python' and execution['source_unchanged'] and
            execution['original_scope_success'], 'Completed corrected Python epoch did not pass')
    require(row['identity'] == receipt['case_identity'] and row['configuration_sha256'] == sha(configuration) and
            result['configuration'] == config and result['source_unchanged_during_run'],
            'Corrected numerical execution differs from its original configuration')
    for key, filename in (('result_sha256', 'case-python-recorded.json'),
                          ('state_sha256', 'actual-python-recording.mat'),
                          ('unchanged_original_python_result_sha256', 'actual-result.json')):
        require(summary[key] == sha(case / filename), 'A completed corrected output changed')
    require(row['new_result_sha256'] == sha(case / 'actual-result.json') and
            row['new_saved_state_sha256'] == sha(case / 'actual-python-recording.mat') and
            row['old_float_audit_sha256'] == sha(old / 'actual-independent-audit.json') and
            row['old_result_sha256'] == sha(old / 'actual-result.json') and
            row['old_point_receipt_sha256'] == sha(old / 'actual-point-receipt.json'),
            'Published old/new execution association differs')
    require(result['results'][0]['monte_carlo'] == prior_result['results'][0]['monte_carlo'],
            'Configured original moment return differs')
    require(common['language'] == 'python' and {s['scheme']: {k: v for k, v in s.items() if k != 'scheme'}
            for s in common['results'][0]['schemes']} == result['results'][0]['schemes'],
            'Common transport changed the actual Python numerical return')
    recording = loadmat(case / 'actual-python-recording.mat', simplify_cells=True)['recording']
    p = config['reported']
    actual_data = channel_data(recording['input']['data'], *[p[k] for k in ('J', 'U', 'N', 'M')])
    require(set(data) == set(actual_data) and len(data) == 11 and all(
        x.shape == actual_data[k].shape and x.dtype == actual_data[k].dtype and
        x.tobytes() == actual_data[k].tobytes() for k, x in data.items()),
        'Corrected execution changed an original physical coefficient')
    require(np.array_equal(power.reshape(-1), np.asarray(recording['input']['power_limit']).reshape(-1)) and
            np.array_equal(limit.reshape(-1), np.asarray(recording['input']['interference_limit']).reshape(-1)),
            'Corrected execution changed an original numerical bound')
    origin = dict(configuration=sha(configuration), result=sha(case / 'actual-result.json'),
        states=sha(case / 'actual-python-recording.mat'), common_container=sha(case / 'case-python-recorded.json'),
        execution=sha(case / 'execution-summary.json'), independent_complete_MP=sha(audit / 'summary.json'),
        published_selection_summary=sha(public / 'corrected-two-controls-summary.json'), historical_original=old_origin)
    selection = dict(selected_epoch='separate_completed_positive_Wick_original_full8_Python_execution',
        original_case_ordinal=n, original_all11_input_arrays_and_bounds_bitwise_equal=True,
        configured_original1000_moment_return_equal=True, all_complete_saved_phase_QT_MP80_MP100_checks_pass=True,
        historical_independent_float_audit_pass=False, historical_failure_flags_modified=False,
        published_summary_byte_binding=summary_binding,
        exact_published_new_epoch_summary_sha256=sha(audit / 'summary.json'))
    return config, result, actual_data, sequence(recording['final_states']), power, limit, origin, selection
