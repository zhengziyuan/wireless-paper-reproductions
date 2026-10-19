"""Original MA calls once per exact geometry; source-bound saved FPA aggregates.

No old whole-configuration tape is rewritten. A relevant-input bridge explicitly
reuses the returned component, not its absent historical per-sample internals.
"""
from pathlib import Path
import copy, hashlib, importlib, json, os, pickle, sys
from bounded_exact_statistical_search_v1 import HostError, atomic, encode, sha, same_binding


def components(job, config, plan, directory, original, core, admission):
    sys.path.insert(0, str(Path(plan['component_reuse_helper']).parent))
    reuse = importlib.import_module(Path(plan['component_reuse_helper']).stem)
    prefix = importlib.import_module(Path(plan['closed_MA_prefix_helper']).stem)
    source_ids = {p: expected for p, expected in plan['source_pins'].items()
                  if Path(p).name in ('core.py','run.py','coordinate_exact.py','ma_metadata.py')}
    relevant = reuse.projection(job, config, 'MA')
    fixed = reuse.projection(job, config, 'FPA')
    import numpy as np
    import platform
    from importlib import metadata as runtime_metadata
    runtime = dict(Python=platform.python_version(), NumPy=np.__version__,
                   SciPy=runtime_metadata.version('scipy'),
                   Python_executable=sys.executable, NumPy_module=np.__file__)
    binding = dict(runtime=runtime, schema='statistical-overlay-original-five-component-cache-v1',
        figure=job['figure'], geometry=job['realization'],
        exact_MA_relevant_projection=relevant, exact_FPA_relevant_projection=fixed,
        original_source_ids=source_ids,
        helper_SHA256=plan['source_pins'][plan['component_reuse_helper']],
        prefix_helper_SHA256=plan['source_pins'][plan['closed_MA_prefix_helper']],
        no_old_wholecfg_tape_guard_bypassed=True)
    directory = Path(directory)
    same_binding(directory, binding)
    closed = directory/'closed-components.json'
    actual = directory/'actual-original-five-components.json'
    if closed.exists():
        receipt = json.loads(closed.read_bytes())
        if receipt['binding'] != binding or sha(actual.read_bytes()) != receipt['result_SHA256']:
            raise HostError('Closed cross-D component cache differs')
        return json.loads(actual.read_bytes()), receipt
    lock = directory/'active-components.json'
    with lock.open('xb') as handle:
        handle.write(encode(dict(PID=os.getpid(), exact_projection_SHA256=relevant['SHA256'])))
        handle.flush(); os.fsync(handle.fileno())
    index_raw = Path(plan['component_donor_index']).read_bytes()
    if sha(index_raw) != plan['component_donor_index_SHA256']:
        raise HostError('Bound source/input component donor index changed')
    index = json.loads(index_raw)
    key = '%d:%d' % (job['figure'],job['realization'])
    fpa, fpa_receipt = reuse.load_fpa_components(job, config, index['rows'][key])
    ma = None; ma_receipt = None; original_error = None
    # Only two exactly bound correct-box original MA donors currently exist.
    # Other source geometries are not taken from the differently bounded MA5/8.
    donor = index.get('completed_correct_box_MA_donor')
    if donor is not None and donor.get('figure') == job['figure'] and donor.get('geometry') == job['realization']:
        donor_job = reuse.read_bound_json(donor['job'])
        donor_cfg = reuse.read_bound_json(donor['config'])
        if reuse.compare(donor_job, donor_cfg, job, config, 'MA')['equal']:
            ma, ma_receipt = reuse.load_ma_components(job, config, donor)
    call_donor = index.get('additional_completed_correct_box_MA_original_call_prefix')
    if (ma is None and call_donor is not None and call_donor.get('figure') == job['figure']
        and call_donor.get('geometry') == job['realization']):
        donor_job = reuse.read_bound_json(call_donor['job'])
        donor_cfg = reuse.read_bound_json(call_donor['config'])
        if reuse.compare(donor_job, donor_cfg, job, config, 'MA')['equal']:
            ma, ma_receipt = prefix.load_ma_components_from_return_prefix(job, config, call_donor)
    if ma is None:
        if admission.get('admit_missing_original_MA_once_per_geometry') is not True:
            raise HostError('Missing original MA component; fresh original-budget MA not admitted')
        sys.path.insert(0, str(Path(plan['original_call_tape_host']).parent))
        tape_module = importlib.import_module(Path(plan['original_call_tape_host']).stem)
        tape = tape_module.OriginalCallTape(directory/'original-MA-call-tape', binding)
        import numpy as np
        c, initial = original.scenario(config, job['N'],job['M'],job['kappa'],job['power'],job['A'],job['geometry'])
        c['region_lower'], c['region_upper'] = job['region_lower'],job['region_upper']
        if 'initial_positions' in job: initial = np.asarray(job['initial_positions'])
        nlos = np.asarray(job['nlos_re']) + 1j*np.asarray(job['nlos_im'])
        ma = {}
        try:
            # Original run_job's order: both AO returns, then both full1000
            # evaluators. All arguments/controls and returned objects are original.
            mrt_pos,mrt_hist = tape.call('optimize-MRT', original.optimize, (initial,c,'MRT'), {})
            zf_pos,zf_hist = tape.call('optimize-ZF', original.optimize, (initial,c,'ZF'), {})
            jitter = np.asarray(job.get('antenna_position_error', np.zeros_like(initial)))
            for mode,position,history in [('mrt',mrt_pos,mrt_hist),('zf',zf_pos,zf_hist)]:
                evaluated = tape.call('instantaneous-MA-'+mode, core.instantaneous,
                                      (position+jitter,c,nlos,mode.upper()), {})
                ma[mode] = dict(positions=position, realized_positions=position+jitter,
                    history=history, actual_full1000_performance=evaluated)
            tape.ensure_consumed()
        except tape_module.OriginalScientificFailure as error:
            original_error = error.detail
        ma_receipt = dict(schema='actual-original-MA-calls-once-per-geometry-v1',
            exact_relevant_projection=relevant, actual_original_exception=original_error,
            all_original_controls_unchanged=True,
            original_AO_budget=config['maximum_AO_iterations'],
            original_AO_threshold=config['fractional_increase_threshold'],
            full_saved_NLoS_count=1000, calls_fresh=tape.fresh,calls_reused=tape.reused,
            per_coordinate_operand_tape_not_newly_added=True,
            original_reference_PASS=False)
    payload = dict(schemes=copy.deepcopy(fpa), ma={}, history={},
        receipts=dict(FPA=fpa_receipt, MA=ma_receipt),
        original_MA_exception=original_error, independent_physical_PASS=False,
        original_reference_PASS=False, historical_author_search_criterion_recovered=False)
    import numpy as np
    for mode,row in ma.items():
        positions = np.asarray(row['positions']); realized = np.asarray(row['realized_positions'])
        payload['schemes']['MA-'+mode.upper()] = copy.deepcopy(row['actual_full1000_performance'])
        payload['ma'][mode] = dict(positions=positions.tolist(),realized_positions=realized.tolist())
        payload['history'][mode] = copy.deepcopy(row['history'])
    # Cache JSON is a component result. It is not relabelled as a new original
    # whole-case return or synthetic original per-call FPA history.
    atomic(actual, payload)
    all_components = all(k in payload['schemes'] for k in ('MA-MRT','MA-ZF','FPA-MRT','FPA-ZF','FPA-OPT'))
    stops = all_components and all(payload['history'][mode]['converged'] is True for mode in ('mrt','zf'))
    fpa_stops = all(v['nonconverged_samples'] == 0 for k,v in fpa.items())
    feasibility = {}
    for mode,row in payload['ma'].items():
        positions = np.asarray(row['positions'])
        dist = np.linalg.norm(positions[:,None]-positions[None,:], axis=2)+np.eye(job['N'])*1e9
        feasibility[mode] = dict(
            original_spacing_gate=bool(dist.min() >= .5-config['verification_tolerance']),
            original_box_gate=bool(np.all(positions >= np.asarray(job['region_lower'])-config['verification_tolerance'])
                                  and np.all(positions <= np.asarray(job['region_upper'])+config['verification_tolerance'])))
    complete_samples = all_components and all(len(row['sample_sum_rates']) == 1000
        and np.isfinite(row['sample_sum_rates']).all() for row in payload['schemes'].values())
    feasible = len(feasibility) == 2 and all(all(row.values()) for row in feasibility.values())
    receipt = dict(binding=binding, result_SHA256=sha(actual.read_bytes()),
        all_original_five_components_present=all_components,
        actual_original_MA_stop_pass=bool(stops), actual_original_FPA_all1000_stop_pass=fpa_stops,
        original_MA_exception=original_error,
        original_saved_feasibility_gates=feasibility, complete_all5_saved1000_samples=complete_samples,
        scoped_original_return_checks=bool(stops and fpa_stops and feasible and complete_samples and original_error is None),
        independent_physics_or_FPA_KKT_PASS=False, original_reference_PASS=False,
        all_returned_cap_and_failed_counts_retained=True)
    atomic(closed, receipt)
    lock.unlink()
    return payload, receipt
