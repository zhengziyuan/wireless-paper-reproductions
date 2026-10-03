"""Software retry/gate tests only: mock statuses are NEVER paper evidence."""
import unittest
from unittest.mock import patch
import numpy as np
import qt_numerical_guard as guard


class SameQTGuardContract(unittest.TestCase):
    def info(self,bound=0.,before=1.,after=1.1,primal=0.):
        return {'before':{'sinr':np.array([before,before])},'after':{'sinr':np.array([after,after])},
                'solver_status':'unit_test_mock_NOT_numerical_evidence',
                'solver_diagnostics':{'constraint_max_relative_violation':primal},'qt_bound_max_violation':bound}

    def test_retries_identical_original_input_without_relaxing_bound(self):
        inputs=tuple(np.ones((3,2))*i for i in range(8));seen=[]
        def mock(*args):
            seen.append(args);return inputs[0],self.info(bound=2e-5 if len(seen)==1 else 2e-6)
        with patch.object(guard.core,'mr_qt_update',side_effect=mock),patch.object(guard,'save_fixture',return_value={'scope':'unit_test_mock'}):
            value,receipt=guard.solve_guard('mr',inputs)
        self.assertEqual(len(seen),2)
        for args in seen:
            for i,x in enumerate(inputs):self.assertIs(args[i],x)
        attempts=receipt['solver_diagnostics']['same_original_QT_numerical_attempts']
        self.assertFalse(attempts[0]['accepted']);self.assertTrue(attempts[1]['accepted']);self.assertEqual(attempts[1]['qt_bound_violation'],2e-6)

    def test_monotonicity_and_nonfinite_primal_rejected(self):
        inputs=tuple(np.ones((3,2)) for _ in range(8));replies=[self.info(after=.9),self.info(primal=float('nan')),self.info()]
        with patch.object(guard.core,'mr_qt_update',side_effect=[(inputs[0],r) for r in replies]),patch.object(guard,'save_fixture',return_value={'scope':'unit_test_mock'}):
            _,receipt=guard.solve_guard('mr',inputs)
        attempts=receipt['solver_diagnostics']['same_original_QT_numerical_attempts'];self.assertEqual([a['accepted'] for a in attempts],[False,False,True])


if __name__=='__main__':unittest.main()
