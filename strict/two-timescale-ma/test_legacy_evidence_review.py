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
    else:
        schemes[name]['powers'] = [1., 1.]
        schemes[name]['off_diagonal_amplitude'] = [0., 1e-16]
result = dict(paper_id='two-timescale-ma', mode='full_scenario', job_metadata=job,
              input_fingerprint='saved-id', implementation_fingerprint='historical',
              metrics=dict(schemes=schemes), checks={k: True for k in CHECKS})

review = inspect(result, job, config, manifest, 'job.json')
assert review['stored_numerical_fields_consistent']
assert not review['historical_source_identity_verified']
assert not review['original_figure_complete']
assert review['stored_MA_power_and_raw_leakage']['MA-ZF']['stored_power_within_budget']
assert review['stored_MA_power_and_raw_leakage']['MA-ZF']['max_raw_off_diagonal_amplitude'] == 1e-16
bad = copy.deepcopy(result)
bad['metrics']['schemes']['MA-ZF']['powers'][0] = 1.1
assert not inspect(bad, job, config, manifest, 'job.json')['stored_MA_power_and_raw_leakage']['MA-ZF']['stored_power_within_budget']
assert not inspect(bad, job, config, manifest, 'job.json')['stored_numerical_fields_consistent']
bad = copy.deepcopy(result)
bad['metrics']['schemes']['MA-ZF']['powers'].pop()
assert not inspect(bad, job, config, manifest, 'job.json')['stored_MA_power_and_raw_leakage']['MA-ZF']['power_samples_finite_nonnegative']
assert not inspect(bad, job, config, manifest, 'job.json')['stored_numerical_fields_consistent']
small_job = dict(job, power=1e-12)
small_result = copy.deepcopy(result)
small_result['job_metadata'] = dict(small_job)
for name in ('MA-MRT', 'MA-ZF'):
    small_result['metrics']['schemes'][name]['powers'] = [1e-12, 1e-12]
small_result['metrics']['schemes']['MA-ZF']['powers'][0] = 1.1e-12
assert not inspect(small_result, small_job, config, manifest, 'job.json')['stored_numerical_fields_consistent']
zero_job = dict(job, power=0.0)
zero_result = copy.deepcopy(result)
zero_result['job_metadata'] = dict(zero_job)
for name in ('MA-MRT', 'MA-ZF'):
    zero_result['metrics']['schemes'][name]['powers'] = [0.0, 0.0]
zero_result['metrics']['schemes']['MA-ZF']['powers'][0] = 5e-324
assert not inspect(zero_result, zero_job, config, manifest, 'job.json')['stored_numerical_fields_consistent']
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
