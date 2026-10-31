#!/usr/bin/env python3
"""Recheck published saved first-case values; never reintegrate any kernel.

Supply --package-dir DIR, or all five explicit source/data arguments below.
Only the new --output JSON is written (at most 64 KiB). Dependencies: Python
and mpmath. Published source bytes and four inputs are pinned, read boundedly,
and loaded directly in memory; no private admission, cache API, temp file,
source copy, bytecode, network, or native/MATLAB execution is needed.
Keep sources at least two directories below a filesystem root (the normal
package/sources layout); original unused support-path declarations require it.

This verifies saved matrices, full moment assembly, and original native gates.
It does not establish historical runtime identity, independently reintegrate
the row moments, replay private provenance, or certify a paper reproduction.
An external process/resource guard remains the caller's responsibility.
"""
import sys
sys.dont_write_bytecode = True

import argparse
import gzip
import hashlib
import io
import json
import math
from pathlib import Path
import platform
import re
import struct
import types


OUTPUT_LIMIT = 64 * 1024
PACKAGE_COMMIT = '8e1450ab018f09adb8d7f7c80789585a2db1984c'
# Dependency order is intentional. Entire original modules are compiled without
# transformations; their numerical functions and constants are not rewritten.
SOURCES = (
    ('full18_scientific_scope_contract_stdlib_v1.py', 16308,
     '4d8542cabcbf24f84d1383e7240a6c1f8533413a14c86760f3b24eed74a7b53c'),
    ('bounded_closed_typed_reader_sourceonly_v1.py', 15982,
     '55eaacb3afdad7e812c1f8080638390de248fbb0807e332a0e5d0b79fff4ac43'),
    ('literal_typed_MP_adapter_sourceonly_v1.py', 5753,
     '4ec08af71144d9720267c1ce571aa7a0e42db6cfdb8d6bc1f6ed9ab613940f81'),
    ('exact_CVX_SDPT3_terminal_contract_stdlib_v3.py', 9639,
     'a54726da7f0deb79c753aea3d7c1f5ca731061bf588e5d8e54ab3567273b86da'),
    ('independent_geometry_kernels_sourceonly_v1.py', 6678,
     'ab1bd6f3f45c25d1dbf5d845a45bf7ef95624cf7f4dc7ba1bf0e1ae7f233de6d'),
    ('full_coordinate_comparison_sourceonly_v4.py', 16973,
     'bc6eea60b6a40df011b85b8d0604882b08c6dce8aaa3b548bb394a7815fa61d4'),
)
DATA = {
    'values': ('first-case-projector-values-only.json.gz', 179325,
               'a8a7121773b1453fb78305fd2f78af9a5ecdd9c1aaf3ae2a07b379c786d71d37', 2 * 1024 * 1024),
    'native': ('native-input-words.json', 34283,
               'abeb5ddccb9f8f5b0eb5a3106d281eec610d179b8e59722e92b289d644358d76', 64 * 1024),
    'components': ('all256-native-P-components-original-gates.jsonl.gz', 184700,
                   '7ceb974a6bff652d96d2b71f3e285176b7d2f4dac1afb832a4fd806d590f1f49', 1024 * 1024),
    'implementation_manifest': ('public-implementation-manifest.json', 9128,
                              '0921486fd5551ab424493de200ad8454ca659b9b9871a98c1b079ddd3e63e98b', 16 * 1024),
}


class EvidenceError(ValueError):
    pass


def need(condition, message):
    if not condition:
        raise EvidenceError(message)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'),
                      ensure_ascii=True, allow_nan=False).encode('ascii')


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        need(key not in result, 'Duplicate JSON field')
        result[key] = value
    return result


def reject_constant(value):
    raise EvidenceError('Nonfinite JSON constant')


def parse_json(raw):
    return json.loads(raw, object_pairs_hook=unique_object, parse_constant=reject_constant)


def pinned_read(path, size, digest, limit):
    need(size <= limit, 'Internal input limit')
    with path.open('rb') as stream:
        raw = stream.read(limit + 1)
    need(len(raw) == size and sha(raw) == digest, 'Published input/source bytes differ: ' + path.name)
    return raw


def inflate(raw, limit):
    with gzip.GzipFile(fileobj=io.BytesIO(raw), mode='rb') as stream:
        decoded = stream.read(limit + 1)
    need(len(decoded) <= limit, 'Decompressed input exceeds explicit bound')
    return decoded


def load_sources(source_dir):
    need(len(source_dir.parents) >= 2,
         'Original support modules require a source directory at least two levels below filesystem root')
    modules, commitments = {}, []
    for filename, size, digest in SOURCES:
        path = source_dir / filename
        raw = pinned_read(path, size, digest, 64 * 1024)
        name = Path(filename).stem
        need(name not in sys.modules, 'Original source module already loaded: ' + name)
        module = types.ModuleType(name)
        module.__file__ = str(path)
        module.__package__ = ''
        sys.modules[name] = module  # Required by dataclasses in the original reader.
        exec(compile(raw, str(path), 'exec', dont_inherit=True), module.__dict__)
        modules[name] = module
        commitments.append(dict(filename=filename, bytes=size, SHA256=digest))
    return (modules['independent_geometry_kernels_sourceonly_v1'],
            modules['full_coordinate_comparison_sourceonly_v4'], commitments)


def read_inputs(paths):
    objects, commitments = {}, []
    for key, (filename, size, digest, decoded_limit) in DATA.items():
        compressed = filename.endswith('.gz')
        raw = pinned_read(paths[key], size, digest, 256 * 1024 if compressed else decoded_limit)
        decoded = inflate(raw, decoded_limit) if compressed else raw
        if key == 'components':
            lines = decoded.splitlines()
            need(len(lines) == 256 and all(0 < len(line) <= 16 * 1024 for line in lines),
                 'Exactly 256 bounded historical component records')
            objects[key] = [parse_json(line) for line in lines]
        else:
            objects[key] = parse_json(decoded)
        commitments.append(dict(role=key, filename=filename, bytes=size, SHA256=digest,
                                decoded_bytes=len(decoded)))
    return objects, commitments


def validate_documents(documents):
    values, native = documents['values'], documents['native']
    need(values['schema'] == 'SAVED_FIRST_CASE_COMPLETE_PROJECTOR_MPWORDS_VALUE_ONLY_V1', 'Saved-value schema')
    need(native['schema'] == 'SAVED_ORIGINAL_FIRST_NATIVE_CASE_RAW_WORDS_PUBLIC_V1', 'Native-word schema')
    need(values['original_full_native_input_SHA256'] == native['original_input_SHA256'],
         'Saved values and native words identify the same original input')
    need(native['reported_dimensions'] == dict(N=16, J=16, U=1, K=15, M=25)
         and native['original_context']['case_id'] == 1, 'Exact first-case scope')
    need(values['scope'] == dict(K=15, N=16, U=1, complete_matrix_cells=7680,
         complete_row_precision_pairs=30, original_case=1, original_column_major_order=True,
         precisions=[80, 100]), 'All saved row/precision pairs and cells')
    need(values['original_cache_keys_recomputable_from_export'] is False
         and values['original_three_file_cache_API_replay_compatible'] is False,
         'Value-only export provenance boundary')
    expected = dict(class_='double', size=[16, 16], ndims=2, numel=256,
                    order='MATLAB_column_major', isreal=False)
    expected['class'] = expected.pop('class_')
    array = native['native_composite_P']
    need(array['header'] == expected, 'Original complete complex native header')
    for name in ('real_hex_column_major', 'imag_hex_column_major'):
        words = array[name]
        need(type(words) is list and len(words) == 256 and
             all(type(word) is str and re.fullmatch('[0-9a-f]{16}', word) for word in words),
             'Every native binary64 word, including imaginary zero')
    records = values['records']
    need(type(records) is list and len(records) == 30 and
         [(r['row_zero_based'], r['precision']) for r in records] ==
         [(row, precision) for row in range(15) for precision in (80, 100)],
         'Exactly 30 saved matrices in original row order')
    for index, record in enumerate(documents['components']):
        need(record['component'] == index and
             record['MATLAB_zero_based_logical_index'] == [index % 16, index // 16] and
             record['original_native_header'] == expected and
             record['native_binary64_real_hex'] == array['real_hex_column_major'][index] and
             record['native_binary64_imag_hex'] == array['imag_hex_column_major'][index],
             'Historical component identity and literal native words')
    need(documents['implementation_manifest']['schema'] ==
         'PARTIAL_FIRST_NATIVE_CASE_EXECUTED_IMPLEMENTATION_AND_DATA_MANIFEST_V1',
         'Published implementation manifest schema')


def mp_tuple(words):
    need(type(words) is list and len(words) == 4 and
         all(type(x) is str and len(x) <= 160 and re.fullmatch(r'0|-?[1-9][0-9]*', x)
             for x in words), 'Four canonical bounded integer strings')
    sign, man, exponent, bits = raw = tuple(map(int, words))
    need(sign in (0, 1) and man >= 0 and bits == man.bit_length() and bits <= 512
         and abs(exponent) <= 16384 and
         ((man == 0 and raw == (0, 0, 0, 0)) or (man > 0 and man % 2 == 1)),
         'Finite canonical exact MP tuple')
    return raw


def decode_matrix(mp, value):
    need(type(value) is list and len(value) == 4 and value[:3] == ['matrix', 16, 16]
         and type(value[3]) is list and len(value[3]) == 256, 'Whole 16-by-16 matrix')
    matrix = mp.matrix(16, 16)
    for index, cell in enumerate(value[3]):
        need(type(cell) is list and len(cell) in (2, 3), 'Tagged MP scalar')
        if cell[0] == 'mpc' and len(cell) == 3:
            raw = (mp_tuple(cell[1]), mp_tuple(cell[2]))
            scalar = mp.make_mpc(raw)
            need(scalar._mpc_ == raw, 'Exact complex tuple decoding')
        elif cell[0] == 'mpf' and len(cell) == 2:
            raw = mp_tuple(cell[1])
            scalar = mp.make_mpf(raw)
            need(scalar._mpf_ == raw, 'Exact real tuple decoding')
        else:
            raise EvidenceError('Unsupported saved scalar tag')
        matrix[index % 16, index // 16] = scalar
        stored = matrix[index % 16, index // 16]
        need(getattr(stored, '_mpc_', getattr(stored, '_mpf_', None)) == raw,
             'Matrix assignment must preserve exact scalar MP words')
    return matrix


def row_checks(mp, pairs):
    """Original row-gate arithmetic and row/column/real/imag operation order.

    This loop is a portable transcription of compute_first_case_rows.py's
    saved-row gate; the private host itself is neither loaded nor certified.
    All failure coordinates are retained by bitmaps, never sampled.
    """
    results = []
    for row in range(15):
        epsilon = mp.mpf('1e-40')
        ordered = hashlib.sha256()
        failed, checked, maximum, largest_abs = 0, 0, None, None
        for i in range(16):
            for j in range(16):
                a, b = pairs[80][row][i, j], pairs[100][row][i, j]
                for component in ('real', 'imag'):
                    aa = mp.make_mpf(getattr(a, component)._mpf_)
                    bb = mp.make_mpf(getattr(b, component)._mpf_)
                    error = abs(aa - bb)
                    threshold = epsilon + epsilon * max(abs(aa), abs(bb))
                    finite = bool(mp.isfinite(error) and mp.isfinite(threshold) and threshold > 0)
                    passed = finite and bool(error <= threshold)
                    ratio = error / threshold if finite else mp.inf
                    item = dict(row=i, column=j, component=component,
                                abs_error_words=list(error._mpf_), threshold_words=list(threshold._mpf_), passed=passed)
                    ordered.update(canonical(item) + b'\n')
                    witness = dict(**item, scaled_error_words=list(ratio._mpf_))
                    if maximum is None or ratio > maximum[0]:
                        maximum = (ratio, witness)
                    if largest_abs is None or error > largest_abs[0]:
                        largest_abs = (error, witness)
                    if not passed:
                        failed |= 1 << checked
                    checked += 1
        need(checked == 512, 'Every saved row real/imaginary component')
        results.append(dict(row_zero_based=row, checked_count=checked,
            all_components_pass=(failed == 0), failure_count=failed.bit_count(),
            failure_bitmap_hex=format(failed, '0128x'),
            maximum_scaled_error=maximum[1], maximum_absolute_error=largest_abs[1],
            ordered_all512_comparison_SHA256=ordered.hexdigest()))
    return dict(checked_count=sum(row['checked_count'] for row in results),
        all_components_pass=all(row['all_components_pass'] for row in results),
        gate='abs(a-b)<=epsilon+epsilon*max(abs(a),abs(b)); epsilon=MP100(1e-40)',
        bitmap_bit_order='bit 2*(16*row+column)+component; component real=0,imag=1', rows=results)


def compare_composites(mp, comparison, matrices, documents):
    native = documents['native']['native_composite_P']
    field_failed = cross_failed = exact_failed = record_failed = 0
    checked = cross_checked = 0
    maximum_ratio = None
    worst = None
    proof = hashlib.sha256()
    for column in range(16):
        for row in range(16):
            index = row + 16 * column
            real = struct.unpack('<d', bytes.fromhex(native['real_hex_column_major'][index]))[0]
            imag = struct.unpack('<d', bytes.fromhex(native['imag_hex_column_major'][index]))[0]
            need(math.isfinite(real) and math.isfinite(imag), 'Finite native complex field')
            actual = complex(real, imag)  # Preserve isreal=False even for zero imaginary words.
            result, ratio = comparison.compare_value(mp, actual, matrices[80][row, column],
                                                       matrices[100][row, column])
            historical = documents['components'][index]
            if not result['original_field_pass']:
                field_failed |= 1 << index
            for component, record in enumerate(result['both_real_imag_crossprecision']):
                if not record['pass_']:
                    cross_failed |= 1 << (2 * index + component)
                cross_checked += 1
            tuple_match = all(result[key][word] == historical[key][word]
                for key in ('native', 'reference_MP80', 'reference_MP100')
                for word in ('exact_real_mpf', 'exact_imag_mpf'))
            if not tuple_match:
                exact_failed |= 1 << index
            if any(value != historical[key] for key, value in result.items()):
                record_failed |= 1 << index
            proof.update(canonical(dict(component=index, comparison=result)) + b'\n')
            if mp.isfinite(ratio) and (maximum_ratio is None or ratio > maximum_ratio):
                maximum_ratio, worst = ratio, index
            checked += 1
    need(checked == 256 and cross_checked == 512, 'Every native and crossprecision field')
    return (dict(native_complex_checks=checked, crossprecision_real_imag_checks=cross_checked,
        native_all_pass=(field_failed == 0), crossprecision_all_pass=(cross_failed == 0),
        native_failure_count=field_failed.bit_count(), crossprecision_failure_count=cross_failed.bit_count(),
        native_failure_bitmap_hex=format(field_failed, '064x'),
        crossprecision_failure_bitmap_hex=format(cross_failed, '0128x'),
        native_bit_order='bit index; index=row+16*column',
        crossprecision_bit_order='bit 2*index+component; real=0,imag=1',
        maximum_native_scaled_error=None if maximum_ratio is None else mp.nstr(maximum_ratio, 105),
        worst_native_index=worst, ordered_all256_current_comparison_SHA256=proof.hexdigest(),
        gate_function='unchanged full_coordinate_comparison_sourceonly_v4.compare_value',
        field_absolute=comparison.FIELD_ABSOLUTE, field_relative=comparison.FIELD_RELATIVE,
        crossprecision_epsilon=comparison.CROSS_PRECISION),
        dict(component_records_checked=checked, exact_native_and_reference_MP_tuples_match=(exact_failed == 0),
             exact_tuple_mismatch_count=exact_failed.bit_count(),
             exact_tuple_mismatch_bitmap_hex=format(exact_failed, '064x'),
             entire_original_comparison_records_match=(record_failed == 0),
             comparison_record_mismatch_count=record_failed.bit_count(),
             comparison_record_mismatch_bitmap_hex=format(record_failed, '064x'),
             byte_equivalence_of_historical_runtime_proven=False))


def execute(paths, source_dir, report):
    report['stage'] = 'bounded_public_input_and_source_validation'
    documents, input_commitments = read_inputs(paths)
    validate_documents(documents)
    geometry, comparison, source_commitments = load_sources(source_dir)
    import mpmath
    report['provenance'] = dict(public_snapshot_commit=PACKAGE_COMMIT,
        inputs=input_commitments, original_source_bytes=source_commitments,
        input_and_original_source_byte_identity_pass=True,
        current_runtime=dict(python=sys.version, implementation=platform.python_implementation(),
                             mpmath_version=mpmath.__version__, mpmath_module_path=str(Path(mpmath.__file__).resolve())),
        runtime_version_is_not_historical_source_byte_equivalence=True,
        historical_runtime_byte_equivalence_proven=False, private_cache_admission_replayed=False,
        original_kernel_epoch_SHA256_provenance_only=documents['values']['original_kernel_epoch_SHA256_recorded_provenance_only'])
    contexts = {precision: mpmath.mp.clone() for precision in (80, 100)}
    for precision, mp in contexts.items():
        mp.dps = precision
    pairs = {80: [], 100: []}
    report['stage'] = 'exact_saved_MP_tuple_decoding'
    for record in documents['values']['records']:
        precision = record['precision']
        pairs[precision].append(decode_matrix(contexts[precision], record['value']))
    report['stage'] = 'all15_saved_row_crossprecision_checks'
    report['scientific_checks']['saved_rows'] = row_checks(contexts[100], pairs)
    report['stage'] = 'full_original_complete_projector_square_at_both_precisions'
    matrices = {}
    for precision in (80, 100):
        matrices[precision] = geometry.complete_projector_square(contexts[precision], pairs[precision])
    report['scientific_checks']['aggregation'] = dict(precisions=[80, 100], row_terms_per_precision=15,
        ordered_cross_products_per_precision=210,
        formula='I-sum(M_k)+sum_{k!=j}(M_k*M_j), followed by original Hermitian symmetrization',
        function='unchanged independent_geometry_kernels_sourceonly_v1.complete_projector_square',
        integration_calls=0, optimizer_calls=0, new_independent_row_kernel_calls=0)
    report['stage'] = 'original_native_gates_and_saved_reference_replay'
    checks, replay = compare_composites(contexts[100], comparison, matrices, documents)
    report['scientific_checks']['native_composite'] = checks
    report['saved_reference_replay'] = replay
    # Source/data interval checks are integrity evidence, separate from math.
    report['stage'] = 'source_and_input_interval_closure'
    for filename, size, digest in SOURCES:
        pinned_read(source_dir / filename, size, digest, 64 * 1024)
    for key, (filename, size, digest, decoded_limit) in DATA.items():
        pinned_read(paths[key], size, digest, 256 * 1024 if filename.endswith('.gz') else decoded_limit)
    report['provenance']['source_and_input_interval_unchanged'] = True
    numerical = report['scientific_checks']['saved_rows']['all_components_pass'] and \
                checks['native_all_pass'] and checks['crossprecision_all_pass']
    replay_pass = replay['exact_native_and_reference_MP_tuples_match'] and \
                  replay['entire_original_comparison_records_match']
    report['scientific_checks']['all_scoped_numerical_gates_pass'] = numerical
    report['saved_evidence_verification_pass'] = numerical and replay_pass
    report['status'] = 'SAVED_EVIDENCE_VERIFIED' if numerical and replay_pass else 'SAVED_EVIDENCE_CHECK_FAILED'
    report['stage'] = 'completed'
    return 0 if numerical and replay_pass else 1


def write_report(stream, report):
    raw = json.dumps(report, ensure_ascii=True, indent=2, allow_nan=False).encode('ascii') + b'\n'
    need(len(raw) <= OUTPUT_LIMIT, 'Report exceeds 64 KiB bound')
    stream.seek(0)
    stream.write(raw)
    stream.truncate()
    stream.flush()


def arguments():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--package-dir', type=Path)
    parser.add_argument('--source-dir', type=Path)
    for name in DATA:
        parser.add_argument('--' + name.replace('_', '-'), type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    explicit = [args.source_dir] + [getattr(args, name) for name in DATA]
    if args.package_dir is not None:
        if any(value is not None for value in explicit):
            parser.error('--package-dir cannot be combined with explicit source/data paths')
        source_dir = args.package_dir / 'sources'
        paths = {name: args.package_dir / item[0] for name, item in DATA.items()}
    else:
        if not all(value is not None for value in explicit):
            parser.error('supply --package-dir or all five explicit source/data arguments')
        source_dir = args.source_dir
        paths = {name: getattr(args, name) for name in DATA}
    source_dir = source_dir.resolve(strict=True)
    paths = {name: path.resolve(strict=True) for name, path in paths.items()}
    output = args.output.resolve()
    need(output.suffix.lower() == '.json' and output.parent.is_dir() and not output.exists(),
         'Output must be a NEW JSON in an existing directory')
    need(output not in paths.values() and output != Path(__file__).resolve(), 'Output cannot overwrite input or verifier')
    return source_dir, paths, output


def main():
    source_dir, paths, output = arguments()
    report = dict(schema='PORTABLE_SAVED_FIRST_CASE_VERIFICATION_V1', status='RUNNING', stage='not_started',
        scope=dict(original_case=1, N=16, K=15, U=1, saved_row_precision_pairs=30,
                   full_paper_or_all_six_PASS=False), scientific_checks={},
        saved_evidence_verification_pass=False,
        limitations=[
            'Saved-row self-consistency and full composite checks only; no new integration from NHU operands.',
            'MP80/MP100 agreement is not a rigorous quadrature error certificate.',
            'No proof of private cache admission or historical runtime byte equivalence.',
            'No optimizer convergence, physical feasibility, full published scenario, figure, or paper PASS.',
            'The complete second-moment formula is retained; it is not a claim of a joint-nullspace projector.',
            'The size bound is for this output file; CPU, memory, and OS storage protection are external.'])
    with output.open('xb') as stream:
        write_report(stream, report)
        try:
            exit_code = execute(paths, source_dir, report)
        except Exception as error:
            report['status'] = 'ERROR_NOT_PASS'
            report['saved_evidence_verification_pass'] = False
            report['error'] = dict(type=type(error).__name__, message=str(error)[:2048])
            exit_code = 2
        write_report(stream, report)
    print(json.dumps(dict(status=report['status'], saved_evidence_verification_pass=
                          report['saved_evidence_verification_pass']), separators=(',', ':')))
    return exit_code


if __name__ == '__main__':
    raise SystemExit(main())
