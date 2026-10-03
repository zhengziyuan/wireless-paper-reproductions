"""Algebra/configuration checks only; never produces paper performance data."""
import json
from pathlib import Path
import unittest
import numpy as np


class SourceContractChecks(unittest.TestCase):
    def test_weighted_qt_epigraph_identity_including_zero_auxiliary(self):
        rng=np.random.default_rng(9937)
        for noise in (1.0,0.07):
            power=100.0
            channel=rng.normal(size=16)+1j*rng.normal(size=16)
            W=rng.normal(size=(16,16))+1j*rng.normal(size=(16,16))
            for auxiliary in (0j,0.03+0.08j,-2.0j):
                received=channel@W;den=np.sum(abs(received[1:])**2)+noise
                physical=2*np.real(np.conj(auxiliary)*received[0])-abs(auxiliary)**2*den
                hs=channel*np.sqrt(power/noise);V=W/np.sqrt(power);az=auxiliary*np.sqrt(noise)
                weighted=np.sum(abs(np.conj(az)*(hs@V[:,1:]))**2)+abs(az)**2
                transformed=2*np.real(np.conj(az)*(hs@V[:,0]))-weighted
                self.assertAlmostEqual(physical,transformed,places=9)

    def test_full_rank_statistical_qos_is_nonconvex_after_los_phase_fix(self):
        Psi=np.diag([2.0,1.0]);epsilon=.1
        for target in (1.0,10**(-3/10)):
            second=np.sqrt(target-2*epsilon**2)
            plus=np.array([epsilon,second]);minus=np.array([epsilon,-second])
            self.assertAlmostEqual(float(plus@Psi@plus),target,places=14)
            self.assertAlmostEqual(float(minus@Psi@minus),target,places=14)
            self.assertGreater(plus[0],0);self.assertEqual(plus[0],minus[0])
            midpoint=(plus+minus)/2
            self.assertLess(float(midpoint@Psi@midpoint),target)
            self.assertAlmostEqual(float(np.vdot(1j*plus,1j*plus).real),float(np.vdot(plus,plus).real))

    def test_author_eps_rician_grid_not_tick_guess(self):
        cfg=json.loads(Path(__file__).with_name('full_config.json').read_text())
        sweeps={s['id']:s for s in cfg['sweeps']}
        self.assertEqual(sweeps['rician_u6']['values'],list(range(0,25,3)))
        self.assertEqual(sweeps['rician_u1']['values'],list(range(0,22,3)))
        self.assertEqual(cfg['tuned_not_reported']['monte_carlo_realizations'],1000)
        self.assertEqual(cfg['tuned_not_reported']['randomization_count'],1000)


if __name__=='__main__':unittest.main()
