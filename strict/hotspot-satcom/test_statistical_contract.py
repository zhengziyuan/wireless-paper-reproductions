"""Source contracts beyond finite-difference/component parity evidence."""
import json
from pathlib import Path
import tempfile
import unittest
import numpy as np
from scenario import sample_scenario
from statistical import moments,printed_soc_update
from run_support import checkpoint_contract,save_receipt,load_checkpoint


class StatisticalContracts(unittest.TestCase):
 def test_equal_original_400m_ground_attenuation(self):
    config=json.loads(Path(__file__).with_name('full_config.json').read_text())
    scene=sample_scenario(config,np.random.default_rng(3309957))
    inputs=scene['mean_inputs'];power=abs(inputs['ground_mean'])**2+inputs['ground_variance']
    lam=299792458/config['reported']['frequency_hz'];area=np.prod(config['reported']['subsurface_elements'])*np.prod(config['reported']['element_size_m'])
    gain=4*np.pi*area/lam**2;receive=10**(config['tuned_not_reported']['ground_receive_gain_dbi']/10)
    expected=(lam/(4*np.pi*400))**2*gain*receive
    assert np.max(abs(power/expected-1))<5e-15
    # Equal amplitudes do not replace different HU phase geometries.
    assert not np.allclose(inputs['ground_mean'][0],inputs['ground_mean'][1],rtol=0,atol=1e-12)
    assert scene['noise']==1.0


 def test_statistical_no_los_covariance_replacement(self):
    config=json.loads(Path(__file__).with_name('full_config.json').read_text())
    x=sample_scenario(config,np.random.default_rng(1))
    Q,Psi,_,_=moments(x['mean_inputs'],x['phi0'])
    assert Q.shape==(6,16,16) and Psi.shape==(10,16,16)
    assert min(np.linalg.eigvalsh(q).min() for q in Q)>0
    assert min(np.linalg.eigvalsh(q).min() for q in Psi)>0
    with self.assertRaisesRegex(RuntimeError,'Original printed'):
        printed_soc_update()


 def test_checkpoint_never_reuses_changed_source_or_settings(self):
    with tempfile.TemporaryDirectory() as temporary:
        path=Path(temporary)/'case.json';contract=checkpoint_contract({'U':6},{'engine.py':'actual-sha'})
        save_receipt(path,{'contract':contract,'case':{'valid':False}})
        assert load_checkpoint(path,contract)['case']['valid'] is False
        changed=checkpoint_contract({'U':6},{'engine.py':'changed-sha'})
        with self.assertRaisesRegex(RuntimeError,'mismatch'):
            load_checkpoint(path,changed)


if __name__=='__main__':unittest.main()
