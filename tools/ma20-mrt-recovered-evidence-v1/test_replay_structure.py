"""Small negative tests for the portable saved-frame reader."""
import base64
from copy import deepcopy
import gzip
import json
from pathlib import Path
import unittest
import numpy as np
import replay_bundle as replay

class FakeCore:
 def __init__(self,values):self.values=iter(values)
 def mrt_statistics(self,*_):return (next(self.values),)

class ReplayStructureTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  p=Path(__file__).with_name('recorded_ao_bundle.json.gz');cls.b=json.loads(gzip.decompress(p.read_bytes()))
  start=cls.b['first_start'];raw=base64.b64decode(cls.b['first_frames_base64'],validate=True)
  cls.frame=replay.read_frames(raw,start['epoch_SHA256'],0,start['epoch_SHA256'])[0][0]
  cls.before=start['state'];cls.after=cls.frame['state'];cls.event=cls.frame['event']
  cls.model={'maximum_AO_iterations':10000,'fractional_increase_threshold':5e-5,'verification_tolerance':1e-6}
 def run_check(self,before,after,event,model):
  rec=self.event['record'];replay.check_transition(before,after,event,model,FakeCore([rec['before'],rec['after']]),np)
 def test_first_record(self):self.run_check(self.before,self.after,self.event,self.model)
 def test_invalid_state_type_and_extra_event_rejected(self):
  bad=deepcopy(self.before);bad['sweep']=False
  with self.assertRaises(ValueError):self.run_check(bad,self.after,self.event,self.model)
  bad=deepcopy(self.event);bad['unexpected']=1
  with self.assertRaises(ValueError):self.run_check(self.before,self.after,bad,self.model)
 def test_nonfinite_tolerance_and_surrogate_rejected(self):
  bad=deepcopy(self.model);bad['verification_tolerance']=float('nan')
  with self.assertRaises(ValueError):self.run_check(self.before,self.after,self.event,bad)
  bad=deepcopy(self.event);bad['record']['surrogate']=False
  with self.assertRaises(ValueError):self.run_check(self.before,self.after,bad,self.model)
 def test_frame_corruption_rejected(self):
  raw=bytearray(base64.b64decode(self.b['first_frames_base64']));raw[60]^=1;epoch=self.b['first_start']['epoch_SHA256']
  with self.assertRaises(ValueError):replay.read_frames(bytes(raw),epoch,0,epoch)

if __name__=='__main__':unittest.main()
