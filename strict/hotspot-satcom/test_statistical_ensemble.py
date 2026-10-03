"""Independent feasibility algebra and all-start certificate tests, not figures."""
import unittest
import numpy as np
from statistical_ensemble import feasible_start,summarize_starts,start_phases,GATES
from statistical import evaluate


class EnsembleTests(unittest.TestCase):
    def test_random_full_rank_moment_feasibility_and_exact_allowance(self):
        rng=np.random.default_rng(100000)
        for U in range(1,7):
            N=16;K=16-U;noise=1.;power=100.;target=np.full(K,0.1)
            # Full-rank positive moments, not scalar/LoS substituted channels.
            Q=[]
            for _ in range(U):
                a=rng.normal(size=(N,N))+1j*rng.normal(size=(N,N));Q.append(a@a.conj().T/100+np.eye(N))
            Psi=[]
            for k in range(K):
                q=0.005*np.eye(N);q[U+k,U+k]+=1.;Psi.append(q)
            Q=np.asarray(Q);Psi=np.asarray(Psi);W0=np.zeros((N,16),complex)
            W0[:U,:U]=.03*np.eye(U);W0[U:,U:]=np.eye(K)
            for start_id in range(U+1):
                W,p=feasible_start(Q,Psi,W0,noise,power,target,start_id)
                e=evaluate(Q,Psi,W,noise)
                self.assertTrue(p['physical_feasibility_pass']);self.assertLessEqual(e['total_power'],power*(1+1e-12))
                self.assertGreaterEqual(np.min(e['sinr'][U:]-target),-1e-12)
                np.testing.assert_array_equal(W[:,U:],W0[:,U:])
                if start_id:
                    user=start_id-1;v=W0[:,user]/np.linalg.norm(W0[:,user]);base=W0.copy();base[:,:U]=0
                    received=np.real(np.einsum('nj,knm,mj->kj',base.conj(),Psi,base));desired=np.diag(received[:,U:]);den=np.sum(received,axis=1)-desired+noise
                    newden=den+p['HU_power']*np.real(np.einsum('n,knm,m->k',v.conj(),Psi,v))
                    np.testing.assert_allclose(e['sinr'][U:],desired/newden,rtol=1e-13,atol=1e-13)

    def test_missing_capped_failed_or_duplicate_start_cannot_pass(self):
        def record(i,rate):return {'start_id':i,'executed':True,'checks':{k:True for k in GATES},'evaluation':{'hu_sum_rate':rate}}
        rows=[record(0,1.),record(1,8.),record(2,3.)]
        s,best=summarize_starts(rows,range(3));self.assertTrue(s['all_required_starts_pass']);self.assertEqual(best['start_id'],1)
        for bad in [rows[:2],[rows[0],rows[1],rows[1]],rows+[record(3,20.)]]:
            self.assertFalse(summarize_starts(bad,range(3))[0]['all_required_starts_pass'])
        rows[2]['checks']['convergence_pass']=False
        s,best=summarize_starts(rows,range(3));self.assertFalse(s['all_required_starts_pass']);self.assertEqual(best['start_id'],1)
        rows[1]['checks']['qt_sdr_bound_pass']=False
        self.assertEqual(summarize_starts(rows,range(3))[1]['start_id'],0)

    def test_predeclared_phase_schedule_and_exact_tie_rule(self):
        phi=np.exp(1j*np.arange(25));a=start_phases(phi,3309957,6);b=start_phases(phi,3309957,6)
        self.assertEqual(len(a),7)
        for p,q in zip(a,b):np.testing.assert_array_equal(p,q);np.testing.assert_allclose(abs(p),1,atol=1e-15)
        np.testing.assert_array_equal(a[0],phi)
        rows=[{'start_id':i,'executed':True,'checks':{k:True for k in GATES},'evaluation':{'hu_sum_rate':4.}} for i in [2,0,1]]
        self.assertEqual(summarize_starts(rows,range(3))[1]['start_id'],0)


if __name__=='__main__':unittest.main()
