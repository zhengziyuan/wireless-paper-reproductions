"""Count-only source model identities; not7000 complete optimizer executions."""
import copy
import json
from pathlib import Path
import unittest
import numpy as np
from hotspot_element_count import PACKAGE,SOURCE_COUNTS,full_count_configuration,sample_count_scenario,scale_reference,sample_scenario


class CountContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config=json.loads((PACKAGE/'instantaneous_geometry_config.json').read_text(encoding='utf-8-sig'))
        cls.reference=sample_scenario(cls.config,np.random.default_rng(9009))

    def test_all7_counts_keep_geometry_direct_NHU_and_RNG(self):
        config=full_count_configuration(self.config)
        for count in SOURCE_COUNTS:
            config['reported']['subsurface_element_count']=count
            rng=np.random.default_rng(9009);sample=sample_count_scenario(config,rng)
            original_config=copy.deepcopy(config);original_config['reported']['subsurface_elements']=[200,140]
            oldrng=np.random.default_rng(9009);original=sample_scenario(original_config,oldrng)
            for key in ('direct','nhu','phi0','nhu_target'):self.assertTrue(np.array_equal(sample[key],original[key]))
            self.assertEqual(rng.bit_generator.state,oldrng.bit_generator.state)
            for key in original['geometry']:self.assertTrue(np.array_equal(sample['geometry'][key],original['geometry'][key]))
            xy=sample['geometry']['hu_xy_m'];dist=np.linalg.norm(xy[:,None,:]-xy[None,:,:],axis=2)[np.triu_indices(6,1)]
            self.assertGreaterEqual(float(np.min(dist)),10-1e-12);self.assertLessEqual(float(np.max(dist)),20+1e-12)
            ratio=count/28000;field=np.sqrt(ratio)
            self.assertTrue(np.array_equal(sample['cascade'],original['cascade']*ratio))
            for key in ('matrix_mean','ground_mean'):
                self.assertTrue(np.array_equal(sample['mean_inputs'][key],original['mean_inputs'][key]*field))
            for key in ('matrix_variance','ground_variance'):
                self.assertTrue(np.array_equal(sample['mean_inputs'][key],original['mean_inputs'][key]*ratio))

    def test_reference_count_preserves_all_numeric_fields(self):
        sample=scale_reference(self.reference,28000)
        for key in ('direct','cascade','nhu','phi0'):self.assertTrue(np.array_equal(sample[key],self.reference[key]))
        for key in self.reference['mean_inputs']:self.assertTrue(np.array_equal(sample['mean_inputs'][key],self.reference['mean_inputs'][key]))

    def test_rician_ratios_and_shared_cascade_fourth_scaling(self):
        for count in SOURCE_COUNTS:
            sample=scale_reference(self.reference,count);a=count/28000
            for m,v in [('matrix_mean','matrix_variance'),('ground_mean','ground_variance')]:
                before=abs(self.reference['mean_inputs'][m])**2/self.reference['mean_inputs'][v]
                after=abs(sample['mean_inputs'][m])**2/sample['mean_inputs'][v]
                np.testing.assert_allclose(after,before,rtol=1e-14,atol=1e-14)
            np.testing.assert_allclose(abs(sample['cascade'])**4,abs(self.reference['cascade'])**4*a**4,rtol=2e-14,atol=0)

    def test_full_population_and_original_grid_are_required(self):
        config=full_count_configuration(self.config)
        self.assertEqual(config['sweeps'][0]['values'],SOURCE_COUNTS)
        self.assertEqual(config['tuned_not_reported']['monte_carlo_realizations'],1000)
        self.assertFalse(config['element_count_contract']['reference_ordinates_used'])
        reduced=copy.deepcopy(self.config);reduced['tuned_not_reported']['monte_carlo_realizations']=999
        with self.assertRaises(ValueError):full_count_configuration(reduced)
        for count in (3999,7000,28001):
            with self.assertRaises(ValueError):scale_reference(self.reference,count)

    def test_MATLAB_original_QT_SDR_RGD_body_is_unchanged(self):
        base=PACKAGE.parent
        original=(PACKAGE/'run_strict_hotspot_satcom.m').read_text(encoding='utf-8').split('function sample=full_sample(scene)',1)[1]
        adapted=(base/'run_hotspot_element_count_matlab.m').read_text(encoding='utf-8').split('function sample=full_sample(scene)',1)[1]
        adapted=adapted.replace('f=strict_hotspot_element_count(strict_hotspot_geometry(scene),scene.reported.subsurface_element_count);','f=strict_hotspot_scenario(scene);')
        self.assertEqual(adapted.strip(),original.strip())


if __name__=='__main__':unittest.main()
