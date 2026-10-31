import copy
import unittest
from verify_native_evidence import check_record


def record():
    return {'before':1.0,'after':1.2,'surrogate':1.1,'lower_bound_gap':0.1,
        'solver_status':'certified_global_2d','original_subproblem_unchanged':True,
        'certificate':{'maximum_normalized_constraint_violation':0.,'normalized_constraint_tolerance':1e-9,
                       'global_objective_gap_upper_bound':0.,'global_objective_gap_tolerance':1e-9}}


class NumericRecord(unittest.TestCase):
    def test_valid_boundary(self):
        check_record(record(),{'sweep_start':1.0},{'sweep_start':1.2},None,True,1e-6,True)

    def test_bad_sweep_objective_rejected(self):
        with self.assertRaises(ValueError):
            check_record(record(),{'sweep_start':1.0},{'sweep_start':5.},None,True,1e-6,True)

    def test_initial_or_previous_objective_rejected(self):
        with self.assertRaises(ValueError):
            check_record(record(),{'sweep_start':3.},{'sweep_start':1.2},None,True,1e-6,True)
        with self.assertRaises(ValueError):
            check_record(record(),{'sweep_start':1.0},{'sweep_start':1.2},3.,False,1e-6,True)

    def test_nonfinite_or_negative_certificate_rejected(self):
        for value in (float('nan'),float('inf'),-1.0,True):
            rec=copy.deepcopy(record());rec['certificate']['global_objective_gap_upper_bound']=value
            with self.assertRaises(ValueError):
                check_record(rec,{'sweep_start':1.0},{'sweep_start':1.2},None,True,1e-6,True)

    def test_forged_lower_bound_gap_rejected(self):
        rec=record();rec['lower_bound_gap']=0.5
        with self.assertRaises(ValueError):
            check_record(rec,{'sweep_start':1.0},{'sweep_start':1.2},None,True,1e-6,True)

if __name__=='__main__':unittest.main()
