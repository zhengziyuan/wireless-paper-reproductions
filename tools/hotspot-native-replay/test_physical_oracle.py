"""Hand-solvable moment/power controls, not reduced paper experiments."""
import unittest
import hashlib
import io
import json
from pathlib import Path
import tarfile
import tempfile
import numpy as np
from audit_saved_native import decode_context,physical_moments,physical_evaluation
from audit_saved_mc import unpack,physical_draw
from unpack_saved_inputs import unpack as unpack_archive


class PhysicalOracle(unittest.TestCase):
    def test_complete_finite_variance_product_and_no_ris_limit(self):
        x=dict(direct_mean=np.array([[1+1j,0]]),direct_variance=np.array([[.2,.3]]),
               matrix_mean=np.eye(2,dtype=complex),matrix_variance=np.array([[.1,.2],[.3,.4]]),
               ground_mean=np.zeros((1,2),complex),ground_variance=np.array([[.5,.25]]),
               nhu_mean=np.array([[0,1j]]),nhu_variance=np.array([[.4,.6]]))
        q,p=physical_moments(x,np.array([1,1j]),False)
        np.testing.assert_allclose(q[0],np.diag([2.825,.75]),rtol=0,atol=1e-15)
        np.testing.assert_allclose(p[0],np.diag([.4,1.6]),rtol=0,atol=1e-15)
        q,_=physical_moments(x,np.array([1,1j]),True)
        np.testing.assert_allclose(q[0],np.diag([2.2,.3]),rtol=0,atol=1e-15)

    def test_ordinary_complex_row_channel_conjugation(self):
        h=np.array([1,1j]);q=np.array([np.outer(h.conj(),h)]);p=np.array([np.eye(2)])
        W=np.array([[1,1],[1j,-1j]])
        sinr,rate,power=physical_evaluation(q,p,W,1,1)
        np.testing.assert_allclose(sinr,[0,2/3],rtol=0,atol=1e-15)
        self.assertEqual(rate,0);self.assertEqual(power,4)

    def test_expected_power_metric_noise_and_interference(self):
        q=np.array([np.diag([2,0])]);p=np.array([np.diag([0,3])]);W=np.diag([2,np.sqrt(5)])
        sinr,rate,power=physical_evaluation(q,p,W,1,1)
        np.testing.assert_allclose(sinr,[8,15],rtol=0,atol=4e-15)
        self.assertAlmostEqual(rate,np.log2(9));self.assertAlmostEqual(power,9)
        W[0,1]=1
        sinr,_,_=physical_evaluation(q,p,W,1,1)
        self.assertAlmostEqual(sinr[0],8/3)

    def test_native_column_major_transport(self):
        value=dict(shape=[2,3],real=[1,2,3,4,5,6],imag=[0,0,1,1,2,2],order='F')
        expected=np.array([[1,3+1j,5+2j],[2,4+1j,6+2j]])
        np.testing.assert_array_equal(decode_context(value),expected)

    def test_multiprecision_metric_on_hand_solved_powers(self):
        try:
            import mpmath
        except ImportError:
            self.skipTest('Optional mpmath dependency unavailable; NumPy controls still run')
        import independent_statistics_mp as formulas
        for precision in (80,100):
            mp=mpmath.mp.clone();mp.dps=precision
            q=[mp.diag([2,0])];p=[mp.diag([0,3])];W=mp.diag([2,mp.sqrt(5)])
            e=formulas.evaluate(mp,q,p,W,mp.mpf(1))
            self.assertLess(abs(e['sinr'][0]-8),mp.mpf('1e-70'))
            self.assertLess(abs(e['sinr'][1]-15),mp.mpf('1e-70'))
            self.assertLess(abs(e['power']-9),mp.mpf('1e-70'))

    def test_native_draw_transport_and_fixed_phase_power(self):
        values=np.array([1,2j,.5,-.25j,0,1],complex)
        entry=dict(complex_values_per_draw=6,direct_shape=[1,2],cascade_shape=[1,1,2],nhu_shape=[1,2])
        direct,cascade,nhu=unpack(np.r_[values.real,values.imag],entry)
        rate,received=physical_draw(direct,cascade,nhu,np.array([1j]),np.eye(2),False,1.)
        self.assertAlmostEqual(rate,np.log2(1+1.25/5.0625))
        np.testing.assert_allclose(received,[[1.25,4.0625],[0,1]],rtol=0,atol=1e-15)
        rate,_=physical_draw(direct,cascade,nhu,np.array([1j]),np.eye(2),True,1.)
        self.assertAlmostEqual(rate,np.log2(1+1/5))

    def test_archive_cannot_write_outside_fresh_directory(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);archive=root/'unsafe.tar.gz';output=root/'target'
            with tarfile.open(archive,'w:gz') as tar:
                info=tarfile.TarInfo('native18-saved-inputs/../../outside.txt');info.size=3
                tar.addfile(info,io.BytesIO(b'bad'))
            digest=hashlib.sha256(archive.read_bytes()).hexdigest()
            archive.with_suffix('.gz.manifest.json').write_text(json.dumps(dict(sha256=digest)))
            with self.assertRaisesRegex(ValueError,'Unsafe'):
                unpack_archive(archive,output)
            self.assertFalse((root/'outside.txt').exists());self.assertFalse(output.exists())

    def test_archive_never_overwrites_existing_results(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);result=root/'keep.json';result.write_text('saved-result')
            with self.assertRaisesRegex(ValueError,'fresh'):
                unpack_archive(root/'unused.tar.gz',root)
            self.assertEqual(result.read_text(),'saved-result')


if __name__=='__main__':unittest.main()
