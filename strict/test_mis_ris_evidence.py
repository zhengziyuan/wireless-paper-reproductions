"""RIS evidence transport and full-population rejection, with no optimization."""
import copy
import importlib.util
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
from unittest import mock

import numpy as np

from mis_population_evidence import _run
from test_mis_population_evidence import documents


class RisEvidence(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        package = Path(__file__).resolve().parent / 'mis-sensing'
        sys.path.insert(0, str(package))
        spec = importlib.util.spec_from_file_location('sensing_ris_transport_test', package / 'run.py')
        cls.runner = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.runner)

    def test_every_target_retains_all_starts_and_a_failed_last_start_is_rejected(self):
        data, _ = documents()
        complete = data['points'][0]['result']
        complete['best_feasible']['state'] = {'phi': {'real': [1.], 'imag': [0.]}}
        runs = [copy.deepcopy(complete), copy.deepcopy(complete)]
        runs[1]['all_start_summaries'][-1]['solver_status']['inner_iteration_cap_exits'] = 1
        model = SimpleNamespace(targets=2, config={
            'azimuth_deg': [0., 45.], 'elevation_deg': [45., 45.],
            'echo_beta_squared': [1., 1.]})
        target_model = SimpleNamespace(metric=lambda state, objective: np.ones((1, 1)))
        with mock.patch.object(self.runner, 'Model', return_value=target_model), \
                mock.patch.object(self.runner, 'optimize', side_effect=runs) as optimizer:
            result = self.runner.ris_baselines(model, {}, Path('unchanged-checkpoint'))
        self.assertEqual(optimizer.call_count, 2)
        self.assertIs(result['target_start_banks'][0], runs[0])
        self.assertIs(result['target_start_banks'][1], runs[1])
        self.assertEqual(result['continuous'], [1., 1.])
        self.assertEqual(_run(runs[0], 'target0', 6000, [1e-6], True)['checked_start_summaries'], 6000)
        with self.assertRaisesRegex(ValueError, 'start6000'):
            _run(runs[1], 'target1', 6000, [1e-6], True)
        offsets = [call.kwargs['seed_offset'] for call in optimizer.call_args_list]
        self.assertEqual(offsets, [100000, 100001])


if __name__ == '__main__':
    unittest.main()
