"""Portable RNG identity and full-budget gates; never a reduced paper run."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import numpy as np
import execute_mis_communications as bank

class BankTests(unittest.TestCase):
    def test_transient_receipt_lock_retried_without_changing_value(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'receipt.json'
            original=Path.replace;calls=[]
            def briefly_locked(source,destination):
                calls.append(destination)
                if len(calls)<3:raise PermissionError('temporary reader lock')
                return original(source,destination)
            with patch.object(Path,'replace',briefly_locked),patch.object(bank.time,'sleep'):
                bank.atomic(path,{'finished':123,'failed':7})
            self.assertEqual(json.loads(path.read_text()),{'finished':123,'failed':7})
            self.assertEqual(len(calls),3)
    def test_explicit_runner_only_resume_keeps_original_signature(self):
        old={'signature':'old','runner_sha256':'io-before','settings':{'starts':6000},'source':'frozen'}
        current=dict(old,signature='new',runner_sha256='io-after')
        with self.assertRaises(ValueError):bank.validate_resume(old,current)
        self.assertEqual(bank.validate_resume(old,current,'io-before'),old)
        for key,value in [('source','changed'),('settings',{'starts':1})]:
            with self.assertRaises(ValueError):bank.validate_resume(old,dict(current,**{key:value}),'io-before')
    def test_exact_serial_rng_jump(self):
        settings=json.loads((bank.PACKAGE/'settings.json').read_text())
        figure=json.loads((bank.PACKAGE/'figures.json').read_text())[0]
        for baseline in ('MIS','SMS'):
            model=bank.point_model(figure['points'][0],baseline,settings)
            seed=settings['initialization']['seed']+(0 if baseline=='MIS' else 500000)
            rng=bank.comm.PortableRandom(seed)
            draws=model.targets*model.U+model.M+model.N
            for start in range(12):
                serial=bank.comm.initialize(model,settings,rng)
                jumped=bank.comm.PortableRandom(seed*pow(16807,start*draws,2147483647)%2147483647)
                actual=bank.comm.initialize(model,settings,jumped)
                for block in serial:self.assertTrue(np.array_equal(serial[block],actual[block]))
    def test_reduced_bank_rejected_before_execution(self):
        settings=json.loads((bank.PACKAGE/'settings.json').read_text());settings['number_of_starts']=1
        with tempfile.TemporaryDirectory() as tmp:
            folder=Path(tmp);path=folder/'settings.json';path.write_text(json.dumps(settings))
            with self.assertRaisesRegex(ValueError,'Full original6000'):
                bank.execute('fig7',folder/'bank',1,path)
            self.assertFalse((folder/'bank').exists())

if __name__=='__main__':unittest.main()
