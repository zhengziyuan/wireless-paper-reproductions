"""Small structure tests, not scientific or resource-guard validation."""
import json
import unittest
from read_native_events import read_segment


class Data:
    def __init__(self, data): self.data=data
    def read_bytes(self): return self.data


def state(antenna=0):
    return {'schema':'MA20_NATIVE_ZF_SEGMENT_STATE_V1','t':[[0.,i] for i in range(6)],
            'sweep':0,'antenna':antenna,'sweep_start':1.,'updates':antenna,
            'done':False,'original_converged_flag':False,'termination':'pending'}


def line(inp, out):
    return (json.dumps({'schema':'MA20_NATIVE_ZF_COORDINATE_EVENT_V1','input':inp,
        'record':{'sweep':0,'antenna':inp['antenna']},'output':out,
        'sweep_relative_change':[]})+'\n').encode()


class EventReader(unittest.TestCase):
    def test_complete_and_partial_tail(self):
        a,b=state(0),state(1)
        result=read_segment(Data(line(a,b)+b'{partial'),a,5e-5)
        self.assertEqual(result['committed_events'],1)
        self.assertEqual(result['partial_tail_bytes'],8)
        self.assertEqual(result['last_state'],b)

    def test_discontinuous_state_rejected(self):
        a,b=state(0),state(1)
        bad=state(1);bad['t'][0]=[99.,99.]
        with self.assertRaises(ValueError):read_segment(Data(line(a,b)+line(bad,state(2))),a,5e-5)

    def test_other_coordinate_mutation_rejected(self):
        a,b=state(0),state(1);b['t'][2]=[99.,99.]
        with self.assertRaises(ValueError):read_segment(Data(line(a,b)),a,5e-5)

    def test_oversize_rejected(self):
        with self.assertRaises(ValueError):read_segment(Data(b'x'*(64*1024+1)),fractional_threshold=5e-5)

    def test_wrong_boundary_decision_rejected(self):
        a=state(5); b=state(0); b['sweep']=1;b['updates']=6;b['sweep_start']=1.1
        event=json.loads(line(a,b));event['sweep_relative_change']=0.1
        event['output']['done']=True;event['output']['original_converged_flag']=True
        event['output']['termination']='fractional_increase'
        with self.assertRaises(ValueError):
            read_segment(Data((json.dumps(event)+'\n').encode()),a,5e-5)

    def test_unfinished_state_at_budget_rejected(self):
        a=state(0);a['sweep']=10000;a['updates']=60000
        with self.assertRaises(ValueError):read_segment(Data(line(a,state(1))),fractional_threshold=5e-5)


if __name__=='__main__':unittest.main()
