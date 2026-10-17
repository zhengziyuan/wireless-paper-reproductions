"""Restore every actual24-case final-state/curve payload after all hash checks."""
import argparse
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import tarfile


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def safe(name):
    p = PurePosixPath(name)
    return bool(name and not p.is_absolute() and '..' not in p.parts and ':' not in name and '\\' not in name)


def unpack(packet, output):
    if output.exists():
        raise FileExistsError('Preserve prior numerical output; select a fresh directory')
    manifest = json.loads((packet/'archive-manifest.json').read_bytes())
    if (manifest['languages'], manifest['power_cases_per_language'], manifest['schemes_per_case'], manifest['total_final_states']) != (['python', 'matlab'], 24, 8, 384):
        raise ValueError('All24 source slots, two languages and eight schemes are required')
    spec = manifest['archive']; chunks = []
    for index, part in enumerate(spec['parts']):
        if not safe(part['file']) or part['file'] != spec['filename']+f'.part{index:03d}':
            raise ValueError('Unexpected/unsafe archive part')
        raw = (packet/part['file']).read_bytes()
        if len(raw) != part['bytes'] or digest(raw) != part['sha256']:
            raise ValueError('Archive part changed')
        chunks.append(raw)
    raw = b''.join(chunks)
    if len(raw) != spec['bytes'] or digest(raw) != spec['sha256']:
        raise ValueError('Whole original numerical archive changed')
    files = {}
    with tarfile.open(fileobj=io.BytesIO(raw), mode='r:gz') as archive:
        for member in archive:
            name = member.name
            if not safe(name) or not member.isfile() or name in files or name not in manifest['files']:
                raise ValueError('Unexpected, duplicated or unsafe archive member')
            payload = archive.extractfile(member).read(); expected = manifest['files'][name]
            if len(payload) != expected['bytes'] or digest(payload) != expected['sha256']:
                raise ValueError('Actual numerical payload changed')
            files[name] = payload
    if set(files) != set(manifest['files']):
        raise ValueError('Missing actual numerical payload')
    index = json.loads(files['final-state-index.json'])
    if index['array_bank_sha256'] != digest(files['final-states.npz']):
        raise ValueError('Actual final-state array binding differs')
    for language in ('python', 'matlab'):
        cases = [c for c in index['cases'] if c['language'] == language]
        if sorted(c['ordinal'] for c in cases) != list(range(24)) or any(len(c['final_states']) != 8 for c in cases):
            raise ValueError('Missing/duplicated original slot or scheme')
    output.mkdir(parents=True)
    for name, payload in files.items():
        target = output/name; target.parent.mkdir(parents=True, exist_ok=True); target.write_bytes(payload)
    print(json.dumps(dict(verified_payloads=len(files), cases_per_language=24, actual_final_states=384,
        archive_sha256=spec['sha256'], optimizer_or_random_draw_calls=0,
        full183_original_reference_or_paper_pass=False)))


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--packet', type=Path, required=True); p.add_argument('--output-dir', type=Path, required=True)
    a = p.parse_args(); unpack(a.packet, a.output_dir)
