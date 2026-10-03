"""Synthetic SCHEMA tests only; no invented scientific result or publication."""
import copy
import unittest
import numpy as np
from render_satellite_figures import aggregate,ecdf,terminal_hold_mean,GATES,COOP_GATES

def statistical_fixture():
    cases=[]
    for b in (0,10,20):
        for u in range(1,7):
            schemes={name:{'evaluation':{'hu_sum_rate':float(u)},
                'independent_MC':{'count':1000,'hu_rate_samples':[1.]*1000}}
                for name in ('AO','TwoStage','NoRIS')}
            cases.append(dict(U=u,kappa_satellite_db=b,status='executed',
                schemes=schemes,checks={k:True for k in GATES}))
    return dict(paper_id='hotspot-satcom',scope='SYNTHETIC_schema_fixture_NOT_experimental_evidence',
        algorithm='corrected_QT_erratum_NOT_original_printed_invalid_SOC',
        source_unchanged_during_run=True,cases=cases,
        configuration={'tuned_not_reported':{'monte_carlo_realizations':1000}})

def instantaneous_fixture():
    samples=[]
    for i in range(1000):
        sample=dict(index=i,valid_sample=True,**{k:True for k in GATES})
        for name in ('NoRIS','RandRIS','AO','AO20','AO100','TwoStage'):
            sample[name]={'hu_sum_rate':6.,'sinr':[1.]*16}
        sample['reported_budget_endpoints']={name:{'valid_budget_endpoint':True,
            'convergence_not_required_for_reported_fixed_budget':True} for name in ('AO20','AO100')}
        sample['history']={name:[1.,2.] for name in ('NoRIS','RandRIS','AO')}
        samples.append(sample)
    return dict(paper_id='hotspot-satcom',scope='SYNTHETIC_schema_fixture_NOT_experimental_evidence',
        source_unchanged_during_run=True,results=[dict(sweep='cdf_kS20',value=20,samples=samples,valid_figure_point=True)])

class SatelliteFigureTests(unittest.TestCase):
    def test_full_statistical_mapping_keeps_all9_curves_and18_cases(self):
        data=aggregate('hotspot-satcom',10,[statistical_fixture()])
        self.assertEqual(len(data['panels'][0]['curves']),9)
        self.assertFalse(data['published_figure_reproduction_certified'])
        self.assertIn('corrected',data['panels'][0]['algorithm'])
    def test_declared_pair_geometry_is_not_complete_source_conformance(self):
        d=statistical_fixture()
        d['configuration']['tuned_not_reported']['hu_cluster_radius_m']=10
        d['geometry_contract']='All HU pair distances are checked by declared radius10 generator'
        data=aggregate('hotspot-satcom',10,[d])
        self.assertTrue(data['hotspot_HU_pair_distance_contract_declared'])
        self.assertFalse(data['scenario_source_constraints_verified'])
        self.assertFalse(data['source_conforming_full_execution_verified'])
    def test_missing_duplicate_failed_or_reduced_statistical_data_rejected(self):
        d=statistical_fixture();variants=[]
        missing=copy.deepcopy(d);missing['cases'].pop();variants.append(missing)
        duplicate=copy.deepcopy(d);duplicate['cases'][0]=copy.deepcopy(duplicate['cases'][1]);variants.append(duplicate)
        failed=copy.deepcopy(d);failed['cases'][0]['checks']['convergence_pass']=False;variants.append(failed)
        small=copy.deepcopy(d);small['cases'][0]['schemes']['AO']['independent_MC']['count']=999;variants.append(small)
        changed=copy.deepcopy(d);changed['source_unchanged_during_run']=False;variants.append(changed)
        for v in variants:
            with self.assertRaises(ValueError):aggregate('hotspot-satcom',10,[v])
    def test_complete_user_means_are_recomputed_from_physical_sinr(self):
        data=aggregate('hotspot-satcom',6,[instantaneous_fixture()])
        self.assertEqual(len(data['panels'][0]['curves']),5)
        for c in data['panels'][0]['curves']:self.assertEqual(c['y'],[1.]*6)
    def test_one_bad_realization_and_absent_budget_endpoints_rejected(self):
        d=instantaneous_fixture();d['results'][0]['samples'][15]['solver_primal_pass']=False
        with self.assertRaises(ValueError):aggregate('hotspot-satcom',6,[d])
        d=instantaneous_fixture();d['results'][0]['samples'][15]['reported_budget_endpoints']['AO100']['valid_budget_endpoint']=False
        with self.assertRaises(ValueError):aggregate('hotspot-satcom',6,[d])
    def test_ecdf_ties_are_exact_not_interpolated(self):
        x,y=ecdf([1.,1.,2.,3.]);self.assertEqual(x,[1.,2.,3.]);self.assertEqual(y,[.5,.75,1.])
    def test_terminal_hold_requires_full1000_without_invented_updates(self):
        values=[[1.,2.]]*999+[[1.,2.,4.]]
        self.assertTrue(np.allclose(terminal_hold_mean(values),[1.,2.,2.002]))
        with self.assertRaises(ValueError):terminal_hold_mean(values[:-1])
    def test_multi_panel_missing_population_rejected(self):
        with self.assertRaises(ValueError):aggregate('hotspot-satcom',4,[instantaneous_fixture()])
    def test_original_element_geometry_not_replaced_by_old_candidate(self):
        with self.assertRaisesRegex(ValueError,'count-only aperture'):aggregate('hotspot-satcom',9,[instantaneous_fixture()])
    def test_all7_counts_keep_full1000_populations(self):
        d=instantaneous_fixture();samples=d['results'][0]['samples']
        d['source_element_count_contract']={'count_changes_centers_or_phase':False,'factorization_needed':False,
                                             'original_author_geometry_recovered':False}
        d['results']=[dict(sweep='element_count',value=count,samples=samples,valid_figure_point=True)
                      for count in range(4000,28001,4000)]
        result=aggregate('hotspot-satcom',9,[d])
        self.assertEqual(len(result['panels'][0]['curves']),5)
        for c in result['panels'][0]['curves']:self.assertEqual(c['x'],list(range(4000,28001,4000)))
        d['results'].pop()
        with self.assertRaises(ValueError):aggregate('hotspot-satcom',9,[d])
    def test_cooperative_source_binding_and_all_schemes_required(self):
        names=['AP-NoRIS','MR-S-NoRIS','MR-TTS-NoRIS','AP-AO','MR-S-PA','MR-TTS-PA','MR-S-TS','MR-TTS-TS']
        points=[dict(sweep='power_kL20',value=float(x),valid_figure_point=True,**{k:True for k in COOP_GATES},
            monte_carlo={'count':1000},schemes={n:{'evaluation':{'sinr':[1.,2.]}} for n in names})
            for x in 2**np.arange(0,5.01,.5)]
        d=dict(paper_id='cooperative-satcom',scope='SYNTHETIC_schema_fixture_NOT_experimental_evidence',
            source_unchanged_during_run=True,results=points)
        data=aggregate('cooperative-satcom',2,[d]);self.assertEqual(len(data['panels'][0]['curves']),8)
        d['results'][0]['schemes'].pop('AP-AO')
        with self.assertRaises(ValueError):aggregate('cooperative-satcom',2,[d])

if __name__=='__main__':unittest.main(verbosity=2)
