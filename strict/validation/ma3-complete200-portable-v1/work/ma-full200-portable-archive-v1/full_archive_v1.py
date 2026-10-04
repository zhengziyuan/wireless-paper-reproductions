"""Prepared stdlib eight-part archive route. Not a numerical certification."""
from pathlib import Path, PurePosixPath
import argparse
import json
import shutil
import zipfile
import safe_archive_v1 as codec
import size_roundtrip_pilot25_v1 as recipe

SCHEMA = 'MA3-full200-lossless-eight-part-v1'
LIMIT = 100_000_000


def validate_index(index):
    if index.get('schema') != SCHEMA or index.get('complete_parts') is not True:
        raise ValueError('Complete eight-part trusted index required; pilot is not full evidence')
    if index.get('original_summary_sha256') != recipe.SUMMARY_SHA or index.get('original_freeze_sha256') != recipe.FREEZE_SHA:
        raise ValueError('Original full200 actual source/evidence identities required')
    records, parts = index['files'], index['parts']
    codec.validate_records(records)
    names = set(records)
    folded = {name.casefold() for name in names}
    for name in names:
        for parent in PurePosixPath(name).parents:
            if str(parent) != '.' and parent.as_posix().casefold() in folded:
                raise ValueError('File/parent target collision rejected before writes')
    if len(records) != 1044 or len(parts) != 8:
        raise ValueError('All1044 original files and eight parts required')
    union = set()
    for number, part in enumerate(parts, 1):
        slots, expected = recipe.part_members(records, number)
        if part.get('number') != number or part.get('slots') != slots or part.get('files') != expected:
            raise ValueError('Exact fixed25-slot partition required, including all shared evidence in part1')
        filename = f'ma-full200-part{number:02d}-of08.zip'
        if part.get('archive_filename') != filename:
            raise ValueError('Distinct canonical part filename required')
        size = part.get('compressed_size')
        if type(size) is not int or not 0 < size < LIMIT:
            raise ValueError('Every complete part must be below100MB; no trimming workaround')
        codec.validate_records({filename: {'size': size, 'sha256': part.get('archive_sha256')}})
        if union & set(expected):
            raise ValueError('Cross-part duplicate target rejected')
        union.update(expected)
    if union != names:
        raise ValueError('Missing original files rejected')
    required_shared = {
        'actual-full200-dual-summary.json', 'pre-audit-byte-freeze.json',
        'actual-readiness-before-freeze.json', 'snapshot/inputs/run_config.json',
        'snapshot/inputs/manifest.json', 'snapshot/inputs/plan.json',
        'snapshot/retained-old88/summary.json',
        'snapshot/sources/isolated/audit_full200_dual_v1.py',
    }
    if not required_shared <= names:
        raise ValueError('Original sources/configuration/history evidence omitted')
    counts = {prefix: sum(name.startswith(prefix) for name in names) for prefix in (
        'snapshot/sources/', 'snapshot/retained-old88/', 'snapshot/inputs/',
        'snapshot/raw/python/', 'snapshot/raw/matlab/', 'snapshot/metadata/', 'case-audits/', 'progress/')}
    if list(counts.values()) != [23, 7, 203, 200, 200, 8, 200, 200]:
        raise ValueError('No population or source reduction permitted')
    return counts


def pinned_index(path, expected_sha):
    if codec.sha(path) != expected_sha:
        raise ValueError('User-supplied trusted index SHA mismatch')
    index = json.loads(Path(path).read_bytes())
    validate_index(index)
    return index


def verify_parts(folder, index):
    validate_index(index)
    for part in index['parts']:
        path = Path(folder) / part['archive_filename']
        if path.stat().st_size != part['compressed_size']:
            raise ValueError('Pinned compressed byte size mismatch')
        codec.zip_members_verified(path, part)
    return True


def verify_tree(root, index):
    root = Path(root).resolve()
    names = set()
    for path in root.rglob('*'):
        if path.is_symlink():
            raise ValueError('Symlink in portable source tree rejected')
        if path.is_file(): names.add(path.relative_to(root).as_posix())
    if names != set(index['files']):
        raise ValueError('Extracted whole tree missing/extra files')
    for name, item in index['files'].items():
        path = root / name
        if path.stat().st_size != item['size'] or codec.sha(path) != item['sha256']:
            raise ValueError('Extracted original byte identity mismatch: ' + name)
    return True


def unpack(folder, index, destination):
    """All parts fully verified first; no extractall/overwrite/symlink support."""
    destination = Path(destination)
    if destination.exists(): raise FileExistsError('Fresh whole extraction directory required')
    verify_parts(folder, index)
    destination.mkdir(parents=True)
    root = destination.resolve()
    for part in index['parts']:
        with zipfile.ZipFile(Path(folder) / part['archive_filename'], 'r') as archive:
            for info in archive.infolist():
                target = root.joinpath(*PurePosixPath(info.filename).parts)
                target.resolve().relative_to(root)
                target.parent.mkdir(parents=True, exist_ok=True)
                with archive.open(info) as source, target.open('xb') as sink:
                    shutil.copyfileobj(source, sink, 1024 * 1024)
    verify_tree(root, index)
    return {'scope': 'Lossless original source/raw/input/archive byte reconstruction ONLY',
            'files': len(index['files']), 'all200_slots_present': True,
            'new_physics_optimizer_MATLAB_or_historical_figure_certificate': False}


def build(destination):
    """Prepared mechanical route: root must authorize actual full8 creation."""
    destination = Path(destination)
    if destination.exists(): raise FileExistsError('Fresh archive output required')
    paths, records = recipe.inventory()
    destination.mkdir(parents=True)
    parts = []
    for number in range(1, 9):
        slots, selected = recipe.part_members(records, number)
        part = codec.write_part(destination / f'ma-full200-part{number:02d}-of08.zip', paths, selected)
        part.update(number=number, slots=slots)
        parts.append(part)
        print(json.dumps({'part': number, 'compressed_bytes': part['compressed_size'],
                          'no_sample_reduction': True}), flush=True)
        if part['compressed_size'] >= LIMIT:
            raise ValueError('Actual part exceeds publishing limit: preserve it and report, never shrink source samples')
    index = {'schema': SCHEMA, 'complete_parts': True,
             'original_summary_sha256': recipe.SUMMARY_SHA, 'original_freeze_sha256': recipe.FREEZE_SHA,
             'files': records, 'parts': parts, 'historical_original_curve_agreement_claimed': False,
             'new_numeric_audit_or_optimizer_called': False}
    validate_index(index)
    if {name: codec.sha(path) for name, path in paths.items()} != {name: item['sha256'] for name, item in records.items()}:
        raise ValueError('Original complete evidence changed during compression')
    verify_parts(destination, index)
    recipe.fresh(destination / 'full200-archive-index.json', index)
    return {'complete_mechanical_archive': True, 'index_sha256': codec.sha(destination / 'full200-archive-index.json')}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=['build', 'verify', 'unpack'])
    parser.add_argument('--archive-dir', type=Path, required=True)
    parser.add_argument('--index', type=Path)
    parser.add_argument('--index-sha256')
    parser.add_argument('--fresh-destination', type=Path)
    args = parser.parse_args()
    if args.mode == 'build':
        if args.index or args.index_sha256 or args.fresh_destination: parser.error('Build requires only a fresh archive-dir')
        result = build(args.archive_dir)
    else:
        if not args.index or not args.index_sha256: parser.error('A separately trusted whole-index SHA is mandatory')
        index = pinned_index(args.index, args.index_sha256)
        if args.mode == 'verify': result = {'archive_bytes_verified': verify_parts(args.archive_dir, index), 'new_numeric_audit': False}
        else:
            if args.fresh_destination is None: parser.error('Unpack requires a fresh destination')
            result = unpack(args.archive_dir, index, args.fresh_destination)
    print(json.dumps(result, indent=2))


if __name__ == '__main__': main()
