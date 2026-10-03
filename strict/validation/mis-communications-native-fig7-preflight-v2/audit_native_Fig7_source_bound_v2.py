"""Source-origin adapter around immutable actual Decimal endpoint auditor v1."""
import argparse
import hashlib
import json
from pathlib import Path
import audit_native_Fig7_saved_endpoints_v1 as original

HERE = Path(__file__).resolve().parent
SCIENCE = HERE.parent / 'mis-communications-native-recording-v2/scientific-source'
EXPECTED_FREEZE = '1a643626b2ebde224c160dcf9191ceb99b56338fe189f43d0656437ed8cefd23'
EXPECTED_AUDITOR = '0386d7a02858ac2398040db2c68085e9c49d1ba26b8f8be25c74072601e81342'
EXPECTED_SETTINGS = '5a9107ff6a293b9d32e6a6eb45ae3bec2507e39d10e5cb79fd969f9a7dbc7f71'
EXPECTED_ENGINE = 'c8e50c69bed4cbb1babcfb24210d2c84d538d7ea7cb94066c7fbd2f3ad63115c'

def source_identity(folder):
    folder = Path(folder)
    freeze = folder / 'recording-source-freeze.json'
    original.require(original.digest(freeze) == EXPECTED_FREEZE, 'Actual native source-origin freeze changed')
    manifest = json.loads(freeze.read_text(encoding='utf-8'))
    hashes = {'recording-source-freeze.json': original.digest(freeze)}
    for name, expected in manifest['files_sha256'].items():
        relative = Path(name)
        original.require(not relative.is_absolute() and '..' not in relative.parts, 'Invalid frozen relative source path')
        hashes[name] = original.digest(folder / relative)
        original.require(hashes[name] == expected, 'Actual pre-result native scientific source changed: ' + name)
    original.require(hashes['settings.json'] == EXPECTED_SETTINGS, 'Original full saved-settings origin changed')
    original.require(hashes['mis_communications_strict_engine_recording_v2.m'] == EXPECTED_ENGINE,
                     'Actual native model/solver/observer version changed')
    original.require(original.digest(Path(original.__file__)) == EXPECTED_AUDITOR,
                     'Immutable actually executed Decimal auditor v1 changed')
    return hashes

def audit_source_bound_start(record_folder, scheme, start, scientific_source=SCIENCE):
    before = source_identity(scientific_source)
    settings = json.loads((Path(scientific_source) / 'settings.json').read_text(encoding='utf-8'))
    initial_path = Path(record_folder) / scheme / ('start-%06d-initial.json' % start)
    initial = json.loads(initial_path.read_text(encoding='utf-8'))
    original.require(initial['settings'] == settings,
                     'Saved native complete settings differ from actual frozen source-origin settings')
    numeric = original.audit_start(record_folder, scheme, start)
    after = source_identity(scientific_source)
    original.require(before == after, 'Native frozen source-origin bytes changed during actual audit')
    numeric['source_origin_binding_v2'] = {
        'actual_pre_result_native_source_freeze_SHA256': EXPECTED_FREEZE,
        'entire_saved_settings_matches_frozen_source_settings': True,
        'all_frozen_native_scientific_sources_hashes_before_after_identical': before,
        'immutable_original_actual_Decimal_v1_auditor_sha256': EXPECTED_AUDITOR,
        'actual_source_origin_adapter_sha256': original.digest(Path(__file__)),
        'native_reference_and_actual_recording_preflight_is_not_full12000': True,
        'phase_vector_shapes_parsed_only_by_declared_named_length_not_arbitrary_squeeze': True,
    }
    return numeric

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--record-folder', required=True)
    parser.add_argument('--scheme', required=True, choices=['MIS', 'SMS'])
    parser.add_argument('--start', required=True, type=int)
    parser.add_argument('--scientific-source', type=Path, default=SCIENCE)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError('Retain prior actual source-bound receipt unchanged')
    try:
        receipt = audit_source_bound_start(args.record_folder, args.scheme, args.start, args.scientific_source)
    except Exception as failure:
        receipt = {'scope': 'actual_native_source_bound_v2_audit_failure_retained',
                   'scheme': args.scheme, 'start': args.start, 'all_required_one_start_gates_pass': False,
                   'actual_exception_class': type(failure).__name__, 'actual_exception_message': str(failure),
                   'source_origin_adapter_sha256': original.digest(Path(__file__))}
        args.output.write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf-8')
        raise
    args.output.write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'scope': receipt['scope'], 'scheme': args.scheme, 'start': args.start,
                      'actual_own_mu_endpoints_checked': receipt['actual_endpoints_checked'],
                      'all_required_one_start_gates_pass': receipt['all_required_one_start_gates_pass'],
                      'entire_saved_settings_and_actual_source_origin_frozen_bytes_pass': True,
                      'fresh_full12000_certificate': False}))
    if not receipt['all_required_one_start_gates_pass']:
        raise SystemExit(1)

if __name__ == '__main__':
    main()
