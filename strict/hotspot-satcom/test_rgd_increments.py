"""Exact increment identities on full-rank full-size independent component inputs."""
import unittest
import numpy as np
from verify_statistical import make_fixture
from statistical import expected_projector_square,criterion_value_gradient,rate_value_gradient
from rgd_numerical_controls import criterion_increment,rate_increment


class ExactIncrementIdentities(unittest.TestCase):
    def test_original_full_rank_objective_increments(self):
        x,_,_=make_fixture();rng=np.random.default_rng(8450);old=np.exp(1j*rng.normal(size=25));P=expected_projector_square(x)
        W=(rng.normal(size=(16,16))+1j*rng.normal(size=(16,16)))*.2
        for scale in (1.,1e-2,1e-4,1e-6):
            new=old*np.exp(1j*scale*rng.normal(size=25))
            exact=criterion_increment(x,old,new,P);difference=criterion_value_gradient(x,new,P)[0]-criterion_value_gradient(x,old,P)[0]
            self.assertLess(abs(exact-difference),1e-11)
            exact=rate_increment(x,old,new,W,.1);difference=rate_value_gradient(x,new,W,.1)[0]-rate_value_gradient(x,old,W,.1)[0]
            self.assertLess(abs(exact-difference),1e-11)
            self.assertLess(abs(criterion_increment(x,old,old,P)),1e-30)
            self.assertLess(abs(rate_increment(x,old,old,W,.1)),1e-30)


if __name__=='__main__':unittest.main()
