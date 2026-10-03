"""Parallel-bank invariants, not a6000-start numerical figure run."""
import copy
import json
import tempfile
import unittest
from pathlib import Path
import numpy as np
import execute_mis_sensing as runner


class SensingBank(unittest.TestCase):
    def setUp(self):
        self.settings=json.loads((runner.PACKAGE/'settings_corrected.json').read_text(encoding='utf-8'))
        self.figure=next(f for f in json.loads((runner.PACKAGE/'figures.json').read_text()) if f['id']=='fig3')

    def test_jump_equals_serial_all_arrays(self):
        model=runner.sensing.make_model(self.figure['points'][0],self.settings)
        rng=runner.sensing.PortableRandom(self.settings['initialization']['seed'])
        for start in range(18):
            serial=runner.sensing.initialize(model,self.settings,rng)
            jumped=runner.jumped_initial_state(model,self.settings,0,start)
            for key in serial:self.assertTrue(np.array_equal(serial[key],jumped[key]))
        rng=runner.sensing.PortableRandom(self.settings['initialization']['seed']+2000)
        for start in range(3):
            serial=runner.sensing.initialize(model,self.settings,rng)
            jumped=runner.jumped_initial_state(model,self.settings,2,start)
            for key in serial:self.assertTrue(np.array_equal(serial[key],jumped[key]))

    def test_reduced_population_rejected_before_bank_created(self):
        for key,value in [('number_of_starts',5999),('outer_iterations',29),('rcg_max_iterations',3999)]:
            settings=copy.deepcopy(self.settings);settings[key]=value
            with self.assertRaises(ValueError):runner.validate_population(settings,self.figure)
        pslr=copy.deepcopy(self.figure);pslr.update(id='fig4',objective='pslr')
        settings=copy.deepcopy(self.settings);settings['pslr_grid']=[59,60]
        with self.assertRaises(ValueError):runner.validate_population(settings,pslr)

    def test_preserve_paper_incumbent_and_independent_verified_ledger(self):
        rows=[dict(point_index=0,start=1,score=3,feasible=True,binary_eta_feasible=True,solver_status={'convergence_verified':True}),
              dict(point_index=0,start=2,score=4,feasible=True,binary_eta_feasible=False,solver_status={'convergence_verified':False}),
              dict(point_index=0,start=3,score=3,feasible=True,binary_eta_feasible=True,solver_status={'convergence_verified':True})]
        with tempfile.TemporaryDirectory() as temporary:
            bank=Path(temporary)
            for row in rows:
                runner.compressed(bank/'starts'/f'point-0000-start-{row["start"]:04d}.json.gz',
                    {'metrics':{},'history':[],'state':{'synthetic_selection_test_only':True}})
            best=runner.best_record(bank,rows);verified=runner.best_record(bank,rows,True)
            self.assertEqual(best['start'],2)
            self.assertFalse(best['solver_status']['convergence_verified'])
            self.assertEqual(verified['start'],1)

    def test_compressed_round_trip_preserves_float_state(self):
        values=runner.serialize({'phi':np.exp(2j*np.pi*np.arange(11)/11),'eta':np.asarray(2.34)})
        with tempfile.TemporaryDirectory() as temporary:
            path=Path(temporary)/'float.json.gz';runner.compressed(path,values)
            self.assertEqual(runner.read_compressed(path),values)


if __name__=='__main__':unittest.main()
