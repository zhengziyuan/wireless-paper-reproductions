"""In-memory regression checks for the scoped read-only reviewer."""
import copy
from legacy_evidence_review import CHECKS, SCHEMES, inspect

job = dict(N=6, M=5, kappa=100, power=1, A=2, figure=5, point=30, realization=0)
config = dict(nlos_realizations_per_geometry=2)
manifest = dict(files=[dict(filename='job.json', input_fingerprint='saved-id', realization=0)])
schemes = {name: dict(sample_sum_rates=[1., 3.], mean_sum_rate=2.) for name in SCHEMES}
for name in SCHEMES:
    if name.startswith('FPA-'):
        schemes[name]['nonconverged_samples'] = 0
result = dict(paper_id='two-timescale-ma', mode='full_scenario', job_metadata=job,
              input_fingerprint='saved-id', implementation_fingerprint='historical',
              metrics=dict(schemes=schemes), checks={k: True for k in CHECKS})

review = inspect(result, job, config, manifest, 'job.json')
assert review['stored_numerical_fields_consistent']
assert not review['historical_source_identity_verified']
assert not review['original_figure_complete']
bad = copy.deepcopy(result)
bad['metrics']['schemes']['FPA-MRT'].pop('nonconverged_samples')
assert not inspect(bad, job, config, manifest, 'job.json')['stored_numerical_fields_consistent']
bad = copy.deepcopy(result)
bad['metrics']['schemes']['MA-MRT']['sample_sum_rates'][0] = -1
assert not inspect(bad, job, config, manifest, 'job.json')['stored_numerical_fields_consistent']
bad = copy.deepcopy(result)
bad['metrics']['schemes']['MA-MRT']['mean_sum_rate'] = 2.1
assert not inspect(bad, job, config, manifest, 'job.json')['stored_numerical_fields_consistent']
bad = copy.deepcopy(result)
bad['checks']['mrt_converged'] = False
assert not inspect(bad, job, config, manifest, 'job.json')['stored_numerical_fields_consistent']
bad = copy.deepcopy(result)
bad['job_metadata']['N'] = 7
assert not inspect(bad, job, config, manifest, 'job.json')['metadata_fields_consistent']
print('PASS: scoped review rejects negative rates, missing FPA convergence, wrong mean/flags/identity')
