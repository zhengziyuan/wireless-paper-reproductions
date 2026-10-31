"""Host-only recovery controls; no scientific solver or reduced paper run."""
import json
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest
from unittest import mock

import recover_missing_bank as recovery


class Recovery(unittest.TestCase):
    def fixture(self, root):
        bank = root / 'original'
        (bank / 'jobs').mkdir(parents=True)
        (bank / 'run_config.json').write_text('{}')
        files = [dict(filename=f'case-000-mc-{i:03d}.json', input_fingerprint=str(i)) for i in range(3)]
        (bank / 'manifest.json').write_text(json.dumps(dict(realizations_per_case=100, expected_jobs=3, files=files)))
        for entry in files:
            (bank / 'jobs' / entry['filename']).write_text('{}')
        (bank / 'case-000-mc-000-python.json').write_text('{"good":true}')
        (bank / 'case-000-mc-001-python.json').write_text('{"good":false,"actual_old_failure":true}')
        metadata = SimpleNamespace(bank_complete=lambda *args: True, implementation_fingerprint=lambda: 'same-source',
                                   reusable=lambda path, expected: json.loads(path.read_text()).get('good') is True)
        return bank, metadata

    def test_only_missing_is_dispatched_and_old_failed_bytes_are_preserved(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder);bank, metadata = self.fixture(root)
            originals = {path.name: path.read_bytes() for path in bank.glob('*-python.json')}
            commands = []
            def launch(command, **kwargs):
                commands.append(command)
                Path(command[command.index('--output') + 1]).write_text('{"good":true}')
                return SimpleNamespace(pid=123, wait=lambda: 0)
            with mock.patch.object(recovery.importlib, 'import_module', return_value=metadata), \
                    mock.patch.object(recovery.subprocess, 'Popen', side_effect=launch), \
                    mock.patch.object(recovery.shutil, 'disk_usage', return_value=SimpleNamespace(free=32*1024**3)):
                self.assertEqual(recovery.execute('rotatable-isac', bank, root/'recovery', 1), 1)
            self.assertEqual(len(commands), 1)
            self.assertEqual(Path(commands[0][commands[0].index('--scenario') + 1]).name, 'case-000-mc-002.json')
            for name, data in originals.items():
                self.assertEqual((bank/name).read_bytes(), data)
            summary = recovery.load(root/'recovery'/'summary.json')
            self.assertEqual(summary['recorded_jobs'], 3)
            self.assertEqual(summary['successful_jobs'], 2)
            self.assertEqual(summary['retained_failed_or_unverified_jobs'], 1)
            self.assertFalse(summary['independent_physics_or_dual_language_or_reference_pass'])

    def test_disk_shortage_defers_without_launch_or_fake_result(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder);bank, metadata = self.fixture(root)
            with mock.patch.object(recovery.importlib, 'import_module', return_value=metadata), \
                    mock.patch.object(recovery.subprocess, 'Popen') as launch, \
                    mock.patch.object(recovery.shutil, 'disk_usage', return_value=SimpleNamespace(free=1024)):
                self.assertEqual(recovery.execute('rotatable-isac', bank, root/'recovery', 1), 1)
                launch.assert_not_called()
            self.assertFalse(any((root/'recovery'/'results').iterdir()))

    def test_incomplete_bank_is_rejected_before_creating_output(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);bank,metadata=self.fixture(root)
            metadata.bank_complete=lambda *args: False
            with mock.patch.object(recovery.importlib, 'import_module', return_value=metadata):
                with self.assertRaisesRegex(ValueError, 'Complete original'):
                    recovery.execute('rotatable-isac', bank, root/'recovery', 1)
            self.assertFalse((root/'recovery').exists())


if __name__ == '__main__':
    unittest.main()
