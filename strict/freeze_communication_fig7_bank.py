"""Recompute all 12000 final physical/KKT states without importing a solver.

The two-element corrected-axis Eq(3) is evaluated explicitly. Each recorded
continuation stop is checked; intermediate inner states were not stored, so
only the FINAL KKT state is independently recomputed. No historical identity
or all-paper certificate follows from this one figure.
"""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import numpy as np
from compare_communication_full_reference import numeric, phases, require

HERE = Path(__file__).resolve().parent


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def evaluate(state, baseline, mu):
    require(np.isfinite(mu) and mu > 0, 'Positive original continuation mu required')
    phi = phases(state, 'phi', 2)
    theta = phases(state, 'theta', 1 if baseline == 'MIS' else 0)
    X = np.asarray(state['X'], float)
    width = 2 if baseline == 'MIS' else 1
    require(X.shape == (4, width) and np.all(np.isfinite(X))
            and np.min(X) >= -1e-12 and np.max(X) <= 1+1e-12,
            'Four-user original scheduling domain required')
    numeric(X.sum(axis=1), np.ones(4), 'actual row sums')
    weights = (np.array([[phi[0]*theta[0], phi[1]],
                         [phi[0], phi[1]*theta[0]]]) if baseline == 'MIS'
               else phi[None, :])
    azimuth = np.deg2rad([-60., -20., 20., 60.])
    steering = np.column_stack((np.ones(4),
        np.exp(1j*np.pi*np.sin(np.pi/4)*np.sin(azimuth))))
    terms = steering[:, None, :] * weights[None, :, :]
    field = terms.sum(axis=2)
    gamma = .01*abs(field)**2
    relaxed = (X*gamma).sum(axis=1)
    minimum = float(np.min(relaxed))
    exponential = np.exp(-(relaxed-minimum)/mu)
    probability = exponential/exponential.sum()
    coefficient = probability[:, None]*X
    angles = []
    for index in range(2):
        derivative = .02*np.real(np.conj(field)*(1j*terms[:, :, index]))
        angles.append(float(-np.sum(coefficient*derivative)))
    if baseline == 'MIS':
        moving = np.column_stack((terms[:, 0, 0], terms[:, 1, 1]))
        derivative = .02*np.real(np.conj(field)*(1j*moving))
        angles.append(float(-np.sum(coefficient*derivative)))
    # Exact projection onto a 1- or 2-entry row simplex, independent of the
    # production sorting/projection helper. Row centering does not change it.
    euclidean = -probability[:, None]*gamma
    if width == 1:
        projected = np.ones_like(X)
    else:
        trial = X-euclidean
        first = np.clip((trial[:, 0]-trial[:, 1]+1)/2, 0, 1)
        projected = np.column_stack((first, 1-first))
    kkt = float(np.sqrt(np.dot(angles, angles)+np.sum((X-projected)**2)))
    chosen = np.argmax(X, axis=1)
    return dict(kkt=kkt, objective=-(minimum-mu*np.log(exponential.sum())),
        min_relaxed_snr=minimum, min_binary_snr=float(np.min(gamma[np.arange(4), chosen])),
        binary_schedule=np.eye(width)[chosen])


def audit(bank):
    bank = Path(bank)
    manifest_path = bank/'manifest.json'
    manifest_sha = digest(manifest_path)
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    require(manifest['paper_id'] == 'mis-communications' and manifest['figure']['id'] == 'fig7'
        and manifest['expected_jobs'] == 12000, 'One complete immutable Fig7 bank required')
    signature_input = {k:v for k,v in manifest.items() if k != 'signature'}
    require(hashlib.sha256(json.dumps(signature_input, sort_keys=True).encode()).hexdigest()
        == manifest['signature'], 'Original immutable manifest signature failed')
    settings = manifest['settings']
    require(settings['number_of_starts'] == 6000 and settings['rcg_max_iterations'] == 4000
        and settings['rcg_gradient_tolerance'] == 1e-6, 'Full disclosed budgets and fixed gate required')
    configuration = manifest['figure']['points']
    require(len(configuration) == 1 and configuration[0]['ms1'] == [1,2]
        and configuration[0]['source_ms1_shape'] == [2,1]
        and configuration[0]['source_correction_id'] == 'COMM-GEOMETRY-FIG7',
        'Explicit original same-two-element axis erratum required')
    source = manifest['source_manifest']['source']
    package = HERE/'mis-communications'
    require(all(digest(package/name) == value for name,value in source.items())
        and digest(package/'figures.json') == manifest['figures_sha256'], 'Actual production source differs from bank')
    paths = sorted((bank/'starts').glob('*.json.gz'))
    require(len(paths) == 12000, 'All12000 actual raw states required; no survivor selection')
    records=[];maximum_kkt=0.;maximum_error=0.;stages=0
    for baseline in ('MIS','SMS'):
        for start in range(1,6001):
            path = bank/'starts'/f'point-0000-{baseline}-{start:04d}.json.gz'
            before = digest(path)
            with gzip.open(path, 'rt', encoding='utf-8') as stream:
                raw=json.load(stream)
            summary=raw['summary'];history=raw['history']
            require(raw['bank_signature'] == manifest['signature'] and summary['point_index'] == 0
                and summary['baseline'] == baseline and summary['start'] == start,
                'Missing, duplicate or changed individual execution identity')
            require(summary['domain_feasible'] is True and summary['solver_status']['convergence_verified'] is True,
                'Recorded failed or unverified start retained; no full success')
            expected=[];mu=settings['initial_mu_values'][(start-1)%5]
            while mu >= settings['terminal_mu']:
                expected.append(mu);mu *= .5
            numeric([h['mu'] for h in history], expected, 'all original continuation stages')
            for stage in history:
                stop=stage['stop'];inner=stage['inner']
                require(stop['reason'] == 'gradient_tolerance' and len(inner) <= 4000
                    and len(inner) > 0 and [h['iteration'] for h in inner] == list(range(len(inner)))
                    and stop['projected_kkt_norm'] <= 1e-6,
                    'Original actual stage did not attain its fixed gate')
                numeric(stop['projected_kkt_norm'], inner[-1]['projected_kkt_norm'], 'last recorded stage stop')
            actual=evaluate(raw['state'],baseline,history[-1]['mu'])
            # Fixed roundoff envelope for the independent expression, not a
            # production stopping tolerance change. Maximum is reported raw.
            require(actual['kkt'] <= 1e-6+1e-14, 'Fresh actual final KKT fails original gate')
            error=numeric(actual['kkt'],history[-1]['stop']['projected_kkt_norm'], 'fresh final KKT')
            numeric(actual['objective'],history[-1]['stop']['objective'], 'fresh final objective')
            for name in ('min_relaxed_snr','min_binary_snr','binary_schedule'):
                numeric(actual[name],raw['metrics'][name], 'fresh final '+name)
            numeric(actual['min_binary_snr'],summary['score'],'fresh actual summary score')
            require(digest(path) == before, 'Raw input changed during independent evaluation')
            maximum_kkt=max(maximum_kkt,actual['kkt']);maximum_error=max(maximum_error,error)
            stages+=len(history)
            records.append(dict(baseline=baseline,start=start,raw_sha256=before,
                final_KKT=actual['kkt'],final_KKT_independent_error=error,
                actual_continuation_stages=len(history),fresh_binary_snr=actual['min_binary_snr']))
        print(json.dumps({'independently_checked':len(records),'maximum_actual_final_KKT':maximum_kkt}),flush=True)
    require(digest(manifest_path) == manifest_sha and all(digest(package/name) == value for name,value in source.items()),
        'Manifest or production source changed during complete independent audit')
    return dict(scope='all12000_actual_final_states_and_recorded_continuation_stops_NOT_intermediate_state_replay',
        bank_signature=manifest['signature'],manifest_sha256=manifest_sha,
        full_result_sha256=digest(bank/'full-result-python.json'),original_source_identity=source,
        actual_raw_files=12000,recorded_original_stops_verified=stages,
        all_final_domains_scores_and_KKT_independently_recomputed=True,
        maximum_actual_final_KKT=maximum_kkt,original_gradient_gate=1e-6,
        independent_roundoff_envelope=1e-14,maximum_independent_KKT_error=maximum_error,
        intermediate_inner_state_gradients_independently_recomputed=False,
        production_solver_imported=False,all12000_inputs_and_source_unchanged=True,
        original_figure_reproduction_certified=False,all_papers_complete=False,records=records)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bank',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();before=digest(__file__);receipt=audit(args.bank)
    require(before == digest(__file__), 'Actual independent evaluator changed')
    receipt['independent_evaluator_sha256']=before
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(receipt,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in receipt.items() if k not in ('records','original_source_identity')}))


if __name__=='__main__':main()
