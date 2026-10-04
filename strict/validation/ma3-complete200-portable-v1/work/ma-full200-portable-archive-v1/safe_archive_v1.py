"""Stdlib pinned ZIP codec. No numerical libraries or automatic extractall."""
from pathlib import Path, PurePosixPath
import hashlib
import re
import shutil
import stat
import zipfile

RESERVED = {'CON', 'PRN', 'AUX', 'NUL', *(f'COM{i}' for i in range(1, 10)), *(f'LPT{i}' for i in range(1, 10))}


def sha(path):
    value = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            value.update(block)
    return value.hexdigest()


def safe_name(name):
    if not isinstance(name, str) or not name or '\\' in name or ':' in name or '\x00' in name:
        raise ValueError('Portable relative POSIX filename required; no Windows drive/ADS')
    path = PurePosixPath(name)
    if path.is_absolute() or path.as_posix() != name or any(part in ('.', '..') for part in path.parts):
        raise ValueError('Absolute/noncanonical/traversing archive path rejected')
    for part in path.parts:
        if part.endswith(('.', ' ')) or part.split('.')[0].upper() in RESERVED:
            raise ValueError('Windows ambiguous/reserved filename rejected')
    return name


def validate_records(records):
    seen = set()
    for name, record in records.items():
        safe_name(name)
        key = name.casefold()
        if key in seen:
            raise ValueError('Case-insensitive duplicate archive target rejected')
        seen.add(key)
        if type(record.get('size')) is not int or record['size'] < 0:
            raise ValueError('Expected exact nonnegative byte size required')
        if not isinstance(record.get('sha256'), str) or not re.fullmatch('[0-9a-f]{64}', record['sha256']):
            raise ValueError('Expected full SHA256 required')


def zip_members_verified(path, record):
    validate_records(record['files'])
    if sha(path) != record['archive_sha256']:
        raise ValueError('Pinned archive byte SHA mismatch')
    with zipfile.ZipFile(path, 'r') as archive:
        names = [info.filename for info in archive.infolist()]
        if len(names) != len(set(name.casefold() for name in names)) or set(names) != set(record['files']):
            raise ValueError('Missing/extra/duplicate archive members rejected')
        for info in archive.infolist():
            safe_name(info.filename)
            kind = stat.S_IFMT(info.external_attr >> 16)
            if info.is_dir() or kind not in (0, stat.S_IFREG) or info.flag_bits & 1:
                raise ValueError('Directory/symlink/device/encrypted archive member rejected')
            expected = record['files'][info.filename]
            if info.file_size != expected['size']:
                raise ValueError('Uncompressed byte limit mismatch before reading member')
            h, count = hashlib.sha256(), 0
            with archive.open(info, 'r') as source:
                for block in iter(lambda: source.read(1024 * 1024), b''):
                    count += len(block)
                    if count > expected['size']:
                        raise ValueError('Uncompressed member exceeds pinned limit')
                    h.update(block)
            if count != expected['size'] or h.hexdigest() != expected['sha256']:
                raise ValueError('Pinned decompressed member SHA/size mismatch')
    return True


def unpack_verified_part(archive_path, record, destination):
    """Validate entire part BEFORE writes. Fresh root; no symlink extraction."""
    zip_members_verified(archive_path, record)
    destination = Path(destination)
    if destination.exists():
        raise FileExistsError('Fresh extraction root required; never overwrite user files')
    destination.mkdir(parents=True)
    root = destination.resolve()
    with zipfile.ZipFile(archive_path, 'r') as archive:
        for info in archive.infolist():
            target = root.joinpath(*PurePosixPath(info.filename).parts)
            target.resolve().relative_to(root)
            target.parent.mkdir(parents=True, exist_ok=True)
            with archive.open(info, 'r') as source, target.open('xb') as sink:
                shutil.copyfileobj(source, sink, 1024 * 1024)
            if sha(target) != record['files'][info.filename]['sha256']:
                raise ValueError('Fresh extracted byte identity mismatch')
    return {name: sha(root / name) for name in record['files']}


def write_part(path, source_paths, records):
    """Mechanical lossless DEFLATE9. Each member original bytes unchanged."""
    validate_records(records)
    path = Path(path)
    if path.exists():
        raise FileExistsError('Immutable fresh archive required')
    with zipfile.ZipFile(path, 'x', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name in sorted(records):
            source_path = Path(source_paths[name])
            if source_path.stat().st_size != records[name]['size'] or sha(source_path) != records[name]['sha256']:
                raise ValueError('Original frozen member changed before compression')
            info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = (stat.S_IFREG | 0o600) << 16
            info._compresslevel = 9
            with source_path.open('rb') as source, archive.open(info, 'w', force_zip64=True) as sink:
                shutil.copyfileobj(source, sink, 1024 * 1024)
    return {'archive_filename': path.name, 'archive_sha256': sha(path),
            'compressed_size': path.stat().st_size, 'files': records}
