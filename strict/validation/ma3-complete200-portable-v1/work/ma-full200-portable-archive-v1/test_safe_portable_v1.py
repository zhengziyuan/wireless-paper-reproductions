"""Light stdlib negatives only. Never import NumPy/solver or audit numeric loop."""
from pathlib import Path
import copy
import hashlib
import json
import stat
import tempfile
import unittest
import zipfile
import full_archive_v1 as full
import safe_archive_v1 as codec
import portable_numeric_route_v1 as numeric

HERE = Path(__file__).resolve().parent
PILOT = HERE / 'actual-first25-byte-size-pilot-v1/actual-first25-size-byte-roundtrip-receipt.json'


def fixture_index():
    # Metadata fixture only; zeros are NOT real archives/source evidence.
    names = json.loads(PILOT.read_bytes())['all_entire_original_files_sha256_before_after']
    records = {name: {'size': 0, 'sha256': '0' * 64} for name in names}
    parts = []
    for number in range(1, 9):
        slots, own = full.recipe.part_members(records, number)
        parts.append({'number': number, 'slots': slots, 'files': own,
                      'archive_filename': f'ma-full200-part{number:02d}-of08.zip',
                      'archive_sha256': '0' * 64, 'compressed_size': 1})
    return dict(schema=full.SCHEMA, complete_parts=True, files=records, parts=parts,
                original_summary_sha256=full.recipe.SUMMARY_SHA, original_freeze_sha256=full.recipe.FREEZE_SHA)


class Safety(unittest.TestCase):
    def test_complete_metadata_fixture_only(self):
        self.assertEqual(sum(full.validate_index(fixture_index()).values()), 1041)

    def test_traversal_and_windows_names(self):
        for name in ('../x', '/x', 'a/../x', 'a//x', './x', 'C:/x', 'a\\x', 'a:stream', 'NUL.txt', 'a.', 'x '):
            with self.subTest(name=name), self.assertRaises(ValueError): codec.safe_name(name)

    def test_duplicate_case(self):
        with self.assertRaises(ValueError): codec.validate_records({'A': {'size': 0, 'sha256': '0'*64}, 'a': {'size': 0, 'sha256': '0'*64}})

    def test_exact_record_types(self):
        for record in ({'size': True, 'sha256': '0'*64}, {'size': -1, 'sha256': '0'*64}, {'size': 0, 'sha256': '00'}):
            with self.assertRaises(ValueError): codec.validate_records({'x': record})

    def test_partial_pilot_rejected(self):
        with self.assertRaises(ValueError): full.validate_index(json.loads(PILOT.read_bytes()))

    def test_missing_baseline_raw(self):
        value = fixture_index(); value['files'].pop('snapshot/raw/matlab/case-001-mc-099-matlab.json')
        with self.assertRaises(ValueError): full.validate_index(value)

    def test_duplicate_or_swapped_slot(self):
        value = fixture_index(); value['parts'][1]['slots'][0] = value['parts'][0]['slots'][0]
        with self.assertRaises(ValueError): full.validate_index(value)

    def test_missing_sources_or_old88(self):
        for name in ('snapshot/retained-old88/summary.json', 'snapshot/sources/isolated/audit_full200_dual_v1.py'):
            value = fixture_index(); value['files'].pop(name)
            with self.assertRaises(ValueError): full.validate_index(value)

    def test_prefix_collision(self):
        value = fixture_index(); value['files']['snapshot'] = {'size': 0, 'sha256': '0'*64}
        with self.assertRaises(ValueError): full.validate_index(value)

    def test_oversize_part_or_changed_source_contract(self):
        value = fixture_index(); value['parts'][0]['compressed_size'] = 100_000_000
        with self.assertRaises(ValueError): full.validate_index(value)
        value = fixture_index(); value['original_freeze_sha256'] = '0'*64
        with self.assertRaises(ValueError): full.validate_index(value)

    def test_pinned_index_hash(self):
        with tempfile.TemporaryDirectory() as root:
            path = Path(root)/'index.json'; path.write_text(json.dumps(fixture_index()))
            with self.assertRaises(ValueError): full.pinned_index(path, '0'*64)

    def zip_fixture(self, root, name='safe/x', data=b'original bytes', symlink=False):
        path = Path(root)/'part.zip'
        info = zipfile.ZipInfo(name); info.external_attr = ((stat.S_IFLNK if symlink else stat.S_IFREG) | 0o600) << 16
        with zipfile.ZipFile(path, 'x') as stream: stream.writestr(info, data)
        record = {'archive_sha256': codec.sha(path), 'files': {name: {'size': len(data), 'sha256': hashlib.sha256(data).hexdigest()}}}
        return path, record

    def test_symlink_archive_rejected(self):
        with tempfile.TemporaryDirectory() as root:
            path, record = self.zip_fixture(root, symlink=True)
            with self.assertRaises(ValueError): codec.zip_members_verified(path, record)

    def test_size_or_decompressed_sha_rejected(self):
        with tempfile.TemporaryDirectory() as root:
            path, record = self.zip_fixture(root)
            bad = copy.deepcopy(record); bad['files']['safe/x']['size'] += 1
            with self.assertRaises(ValueError): codec.zip_members_verified(path, bad)
            bad = copy.deepcopy(record); bad['files']['safe/x']['sha256'] = '0'*64
            with self.assertRaises(ValueError): codec.zip_members_verified(path, bad)

    def test_no_write_on_failed_validation(self):
        with tempfile.TemporaryDirectory() as root:
            path, record = self.zip_fixture(root); record['archive_sha256'] = '0'*64
            dest = Path(root)/'fresh'
            with self.assertRaises(ValueError): codec.unpack_verified_part(path, record, dest)
            self.assertFalse(dest.exists())

    def test_roundtrip_and_existing_target_rejected(self):
        with tempfile.TemporaryDirectory() as root:
            path, record = self.zip_fixture(root); dest = Path(root)/'fresh'
            self.assertEqual(codec.unpack_verified_part(path, record, dest)['safe/x'], record['files']['safe/x']['sha256'])
            with self.assertRaises(FileExistsError): codec.unpack_verified_part(path, record, dest)

    def test_numeric_suffix_exact_without_execution(self):
        source = full.recipe.ACTUAL/'snapshot/sources/isolated/audit_full200_dual_v1.py'
        self.assertTrue(numeric.prepare(source)['original_numeric_AST_exactly_equal'])
        with tempfile.TemporaryDirectory() as root:
            changed = Path(root)/'mutant.py'; changed.write_text(source.read_text().replace('excess < 1e-9', 'excess < 1e-6'))
            with self.assertRaises(ValueError): numeric.prepare(changed)


if __name__ == '__main__': unittest.main(verbosity=2)
