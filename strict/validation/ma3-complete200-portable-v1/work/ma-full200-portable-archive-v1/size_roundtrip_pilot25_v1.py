"""Authorized mechanical first25 ZIP-size/byte-roundtrip pilot ONLY."""
from pathlib import Path
import argparse
import json
import time
import safe_archive_v1 as codec

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
ACTUAL = ROOT / 'work/ma-full200-dual-audit-v1/actual-full200-dual-20261004-v1'
FREEZE_SHA = 'b13b2a56c6a32b3e01232230f49f99576040a3690a33b6427161eeab2213787f'
SUMMARY_SHA = '04bbde38b3e5371d49e0396782cd9024d6b2c5130824447cb444b184c29a1712'
SLOTS = [f'case-{case:03d}-mc-{mc:03d}' for case in range(2) for mc in range(100)]


def fresh(path, value):
    with Path(path).open('x', encoding='utf-8') as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.write('\n')


def inventory():
    freeze_path, summary_path = ACTUAL / 'pre-audit-byte-freeze.json', ACTUAL / 'actual-full200-dual-summary.json'
    if codec.sha(freeze_path) != FREEZE_SHA or codec.sha(summary_path) != SUMMARY_SHA:
        raise ValueError('Actual original full200 freeze/summary identity changed')
    frozen, summary = json.loads(freeze_path.read_bytes()), json.loads(summary_path.read_bytes())
    if summary['attempted_cases'] != 200 or summary['passed_cases'] != 200 or summary['failed_cases'] != 0 or summary['full200_independent_numeric_pass'] is not True:
        raise ValueError('Actual complete original dual200 evidence required')
    paths, records = {}, {}
    for name, expected in frozen['files_sha256'].items():
        path = ACTUAL / 'snapshot' / name
        if codec.sha(path) != expected:
            raise ValueError('Complete original snapshot byte mismatch: ' + name)
        archive_name = 'snapshot/' + name
        paths[archive_name] = path
        records[archive_name] = {'sha256': expected, 'size': path.stat().st_size}
    for group, expected_count in (('case-audits', 200), ('progress', 200)):
        files = sorted((ACTUAL / group).glob('*.json'))
        if len(files) != expected_count:
            raise ValueError('All200 actual audit/progress receipts required')
        for path in files:
            if group == 'case-audits' and codec.sha(path) != summary['all200_case_audit_sha256'][path.name]:
                raise ValueError('Original actual per-case independent audit changed')
            name = group + '/' + path.name
            paths[name] = path
            records[name] = {'sha256': codec.sha(path), 'size': path.stat().st_size}
    for name in ('pre-audit-byte-freeze.json', 'actual-full200-dual-summary.json', 'actual-readiness-before-freeze.json'):
        path = ACTUAL / name
        paths[name] = path
        records[name] = {'sha256': codec.sha(path), 'size': path.stat().st_size}
    if len([name for name in records if name.startswith('snapshot/inputs/jobs/')]) != 200 or len([name for name in records if name.startswith('snapshot/raw/')]) != 400:
        raise ValueError('No omitted/extra original job or language raw record')
    return paths, records


def part_members(all_records, part):
    if type(part) is not int or not 1 <= part <= 8:
        raise ValueError('Exactly eight fixed25-slot parts; no sample reduction')
    selected = SLOTS[(part - 1) * 25: part * 25]
    own = set()
    for index, stem in enumerate(selected, start=(part - 1) * 25 + 1):
        own.update({f'snapshot/inputs/jobs/{stem}.json', f'snapshot/raw/python/{stem}-python.json',
            f'snapshot/raw/matlab/{stem}-matlab.json', f'case-audits/{stem}-independent-dual.json',
            f'progress/progress-{index:03d}.json'})
    if part == 1:
        own.update(name for name in all_records if not name.startswith(('snapshot/inputs/jobs/', 'snapshot/raw/', 'case-audits/', 'progress/')))
    if not own <= set(all_records):
        raise ValueError('Original fixed part recipe references missing evidence')
    return selected, {name: all_records[name] for name in sorted(own)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--fresh-output-directory', type=Path, required=True)
    args = parser.parse_args()
    output = args.fresh_output_directory.resolve()
    output.relative_to(ROOT.resolve())
    if output.exists():
        raise FileExistsError('Fresh mechanical pilot folder required')
    output.mkdir(parents=True)
    started = time.perf_counter()
    paths, all_records = inventory()
    before = {name: codec.sha(path) for name, path in paths.items()}
    own_before = {path.name: codec.sha(path) for path in HERE.iterdir() if path.is_file()}
    fresh(output / 'actual-pilot-start-byte-binding.json', {'scope': 'Mechanical first25 ZIP-size/roundtrip pilot, NOT a new scientific audit',
        'entire_original_snapshot_and_all200_audit_progress_sha256_before': before,
        'pilot_sources_sha256_before': own_before, 'actual_original_full200_summary_sha256': SUMMARY_SHA,
        'actual_original_full200_freeze_sha256': FREEZE_SHA, 'all200_numeric_rerun_or_newMC_MATLAB': False})
    slots, selected = part_members(all_records, 1)
    part = codec.write_part(output / 'ma-full200-part01-of08-SIZE-PILOT.zip', paths, selected)
    if part['compressed_size'] > 50_000_000:
        print(json.dumps({'compressed_pilot_bytes': part['compressed_size'], 'exceeds_50MB': True,
                          'samples_not_reduced': True, 'whole_pack_not_started': True}), flush=True)
    extracted = codec.unpack_verified_part(output / part['archive_filename'], part, output / 'byte-roundtrip-first25')
    roundtrip_pass = extracted == {name: item['sha256'] for name, item in selected.items()}
    after = {name: codec.sha(path) for name, path in paths.items()}
    if before != after or own_before != {name: codec.sha(HERE / name) for name in own_before}:
        raise ValueError('Original completed source/evidence changed during mechanical pilot')
    fresh(output / 'actual-first25-size-byte-roundtrip-receipt.json', {
        'scope': 'Actual ZIP DEFLATE9 and exact byte roundtrip for first25 slots only; no new numeric or full archive publication',
        'fixed_original_first25_slot_names': slots, 'part': part,
        'part_member_count': len(selected), 'part_uncompressed_bytes': sum(item['size'] for item in selected.values()),
        'exact_byte_roundtrip_pass': roundtrip_pass,
        'all_entire_original_snapshot_audits_progress_source_bytes_before_after_unchanged': before == after,
        'all_entire_original_files_sha256_before_after': before,
        'pilot_source_sha256_before_after': own_before,
        'original_full200_independent_pass_preserved_NOT_new_audit': True,
        'compressed_part_exceeds_50MB_report_only': part['compressed_size'] > 50_000_000,
        'full_eight_part_archive_completed_or_public_written': False,
        'new_optimizer_MC_RNG_physics_or_MATLAB_called': False,
        'no_original_curve_agreement_or_global_AO_or_equal_nonconvex_solution_claim': True,
        'elapsed_mechanical_pilot_seconds': time.perf_counter() - started})
    print(json.dumps({'pilot_roundtrip_pass': roundtrip_pass, 'first25_compressed_bytes': part['compressed_size'],
        'exceeds_50MB': part['compressed_size'] > 50_000_000, 'original_snapshot_unchanged': True}), flush=True)
    if not roundtrip_pass: raise SystemExit(1)


if __name__ == '__main__': main()
