"""Non-numerical orchestration tests; never a full6000 scientific certificate."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import execute_mis_sensing as executor


class ErrorRetention(unittest.TestCase):
    def make_manifest(self, directory):
        path=Path(directory)/'manifest.json'
        path.write_text(json.dumps({'signature':'test-only','implementation_digest':'expected',
            'runner_sha256':'runner','settings':{},'figure':{'points':[{}],'objective':'sinr'}}),encoding='utf-8')
        return path

    def run_error(self, path, error, digest='expected'):
        with patch.object(executor,'_execute_start',side_effect=error), \
             patch.object(executor.sensing,'implementation_digest',return_value=(digest,{'source':{}})), \
             patch.object(executor,'sha',return_value='runner'), \
             patch.object(executor.sensing,'make_model',side_effect=ValueError('test initial unavailable')):
            return executor.execute_start((str(path),0,0))

    def test_exception_retained_and_never_a_completed_or_feasible_sample(self):
        with tempfile.TemporaryDirectory(prefix='sensing-error-test-') as directory:
            path=self.make_manifest(directory)
            result=self.run_error(path,ArithmeticError('test cone failure'))
            self.assertEqual(result['exit_status'],'execution_error')
            self.assertIsNone(result['score'])
            self.assertFalse(result['feasible'])
            saved=executor.read_compressed(path.parent/'starts'/'point-0000-start-0001.json.gz')
            self.assertIsNone(saved['state'])
            self.assertIsNone(saved['history'])
            self.assertFalse(saved['full_per_start_budget_execution_complete'])
            self.assertFalse(saved['convergence_verified'])
            self.assertTrue(saved['source_unchanged_during_run'])
            self.assertIn('ArithmeticError',saved['exception_traceback'])
            self.assertIsNone(executor.best_record(path.parent,[result]))
            self.assertIsNone(executor.best_record(path.parent,[result],True))

    def test_changed_source_is_not_certified(self):
        with tempfile.TemporaryDirectory(prefix='sensing-source-test-') as directory:
            path=self.make_manifest(directory)
            self.run_error(path,ValueError('source mismatch'),'changed')
            saved=executor.read_compressed(path.parent/'starts'/'point-0000-start-0001.json.gz')
            self.assertFalse(saved['source_unchanged_during_run'])
            self.assertEqual(saved['expected_implementation_digest'],'expected')

    def test_existing_receipt_cannot_be_overwritten(self):
        with tempfile.TemporaryDirectory(prefix='sensing-existing-test-') as directory:
            path=self.make_manifest(directory)
            self.run_error(path,ArithmeticError('first failure'))
            saved=path.parent/'starts'/'point-0000-start-0001.json.gz'
            before=saved.read_bytes()
            with self.assertRaisesRegex(RuntimeError,'Never overwrite'):
                self.run_error(path,ArithmeticError('second failure'))
            self.assertEqual(before,saved.read_bytes())

    def test_interrupt_is_not_swallowed(self):
        with patch.object(executor,'_execute_start',side_effect=KeyboardInterrupt):
            with self.assertRaises(KeyboardInterrupt):
                executor.execute_start(('unused-test-path',0,0))


if __name__=='__main__':
    unittest.main()
