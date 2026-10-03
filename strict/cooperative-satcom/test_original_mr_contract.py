"""Physical MR power and original-QT identities, independent of figure values."""
import unittest
import numpy as np
from core import statistical_mr_coefficients,tts_mr_coefficients


class OriginalMRContract(unittest.TestCase):
    def setUp(self):
        rng=np.random.default_rng(45490);self.mean=(rng.normal(size=(3,2,16))+1j*rng.normal(size=(3,2,16)))*.2
        self.Q=np.empty((3,2,16,16),complex)
        for j in range(3):
            for u in range(2):self.Q[j,u]=.05*np.eye(16)+np.outer(self.mean[j,u],np.conj(self.mean[j,u]))
        self.gt=np.tile(np.eye(16)[None,None,:,:]*.1,(3,1,1,1));self.p=.4+rng.random((3,2))

    def test_statistical_power_is_precoder_norm_not_self_cross_moment(self):
        s,b,power,leak=statistical_mr_coefficients(self.mean,self.Q,self.gt)
        W=np.sqrt(self.p)[:,:,None]*self.mean
        self.assertTrue(np.allclose(np.sum(abs(W)**2,axis=(1,2)),np.sum(self.p*power,axis=1),rtol=1e-14,atol=1e-14))
        printed=np.asarray([[b[j,u,u] for u in range(2)] for j in range(3)])
        self.assertGreater(np.max(abs(printed-power)),.01)

    def test_original_qt_identity_and_tts_power(self):
        s,b,power,leak=statistical_mr_coefficients(self.mean,self.Q,self.gt);den=1+np.einsum('ji,jui->u',self.p,b)-np.sum(self.p*s,axis=0)
        y=np.sqrt(self.p*s)/den;lower=np.sum(2*y*np.sqrt(self.p*s),axis=0)-np.sum(y*y,axis=0)*den
        self.assertLess(np.max(abs(lower-np.sum(self.p*s,axis=0)/den)),1e-14)
        probe=y+.1;lower=np.sum(2*probe*np.sqrt(self.p*s),axis=0)-np.sum(probe*probe,axis=0)*den
        gap=np.sum(self.p*s,axis=0)/den-lower
        self.assertTrue(np.allclose(gap,den*np.sum((probe-y)**2,axis=0),rtol=1e-13,atol=1e-14))
        fourth=np.trace(self.Q,axis1=2,axis2=3).real**2+np.trace(self.Q@self.Q,axis1=2,axis2=3).real
        _,_,tts_power,_=tts_mr_coefficients(self.Q,fourth,self.gt)
        self.assertTrue(np.allclose(tts_power,np.trace(self.Q,axis1=2,axis2=3).real))


if __name__=='__main__':unittest.main()
