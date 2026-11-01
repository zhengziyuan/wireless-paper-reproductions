"""Prepared MC-return transport: new optimization, zero new channel draws.

The completed previous1000 actual draw evidence remains authoritative. Replace
only the entire original post-optimization MC block after exact input binding;
no statistics, channel moments, random draws or independent MP are rerun here.
"""
import copy
import hashlib
import inspect
import json
from pathlib import Path
import types

ORIGINAL_BLOCK = '''            count=scene['tuned_not_reported']['monte_carlo_realizations']; rng=np.random.default_rng(scene['tuned_not_reported']['seed'])
            phi=np.ones(data['r_mean'].shape,complex); _,_,Q,fourth,_=channel_moments(data,phi)
            powers=[]; fourths=[]
            for _ in range(count):
                h=sample_effective(data,phi,rng); p=np.sum(abs(h)**2,axis=2); powers.append(p); fourths.append(p*p)
            empirical2=np.mean(powers,axis=0); empirical4=np.mean(fourths,axis=0); exact2=np.trace(Q,axis1=2,axis2=3).real
            mc={'count':count,'second_moment_max_relative_error':float(np.max(abs(empirical2-exact2)/exact2)),
                'fourth_moment_max_relative_error':float(np.max(abs(empirical4-fourth)/fourth)),
                'purpose':'Independent channel-moment validation, not synthetic hardcoded performance arrays'}
'''
REUSE_BLOCK = "            mc=_CAPTURE_ONLY_SAVED_MC_REUSE(data,scene)\n"


def need(value, message):
    if not value:
        raise ValueError(message)


def fresh(path, value):
    with Path(path).open('x', encoding='utf-8', newline='\n') as handle:
        json.dump(value, handle, indent=2, allow_nan=False)
        handle.write('\n')


class ExactSavedMCReuse:
    def __init__(self, output, prior_directory, expected_config, audit_path):
        import numpy as np
        self.root = Path(output)
        self.prior = Path(prior_directory)
        self.cfg = copy.deepcopy(expected_config)
        self.start = json.loads((self.prior/'actual-moment-start.json').read_bytes())
        complete_bytes = (self.prior/'actual-moment-tape-complete.json').read_bytes()
        self.complete = json.loads(complete_bytes)
        self.audit = json.loads(Path(audit_path).read_bytes())
        need(self.audit.get('all_independent_checks_pass') is True, 'Original actual1000 independent audit must pass')
        need(self.audit['actual_online_tape_complete_SHA256'] == hashlib.sha256(complete_bytes).hexdigest()
             and self.audit['raw_primitive_payload_sha256'] == self.complete['stream_SHA256'],
             'The passing independent audit must bind this exact completion and original stream digest')
        need(self.complete['completed_draws'] == self.complete['count'] == 1000,
             'Exactly completed original1000 draws required')
        need(self.complete['actual_new_observer_RNG_calls'] == 0,
             'Original passive tape must not add draws')
        need(self.start['configuration'] == self.cfg, 'Old MC configuration must equal this exact original configuration')
        old_result_bytes = (self.prior.parent/'numerical-full8/actual-result.json').read_bytes()
        old_result = json.loads(old_result_bytes)
        need(self.audit['source_result_sha256'] == hashlib.sha256(old_result_bytes).hexdigest(),
             'The passing independent audit must bind the original actual full8 return')
        need(old_result['configuration'] == self.cfg and len(old_result['results']) == 1,
             'Original full8 return must bind the same exact single configuration')
        need(old_result['results'][0]['monte_carlo'] == self.complete['original_monte_carlo_return'],
             'Saved actual MC completion must preserve the original full8 MC return exactly')
        raw = (self.prior/'actual-moment-input.npz').read_bytes()
        need(hashlib.sha256(raw).hexdigest() == self.start['input_npz_SHA256'], 'Old actual MC input bytes')
        need(self.audit['actual_online_tape_input_binding']['moment_input_SHA256']
             == self.start['input_npz_SHA256'], 'Independent audit must bind these exact old input bytes')
        import io
        with np.load(io.BytesIO(raw), allow_pickle=False) as arrays:
            self.old_inputs = {key: arrays[key].copy() for key in arrays.files}
        self.calls = 0
        self.returned = False
        self.error = None

    def __call__(self, data, scene):
        import numpy as np
        need(self.calls == 0, 'One exact saved-return reuse, no second scene or MC fallback')
        self.calls += 1
        self.root.mkdir(parents=True, exist_ok=False)
        try:
            need(scene == self.cfg == self.start['configuration'], 'Full current/old scene configuration differs')
            need(scene['tuned_not_reported']['monte_carlo_realizations'] == 1000,
                 'Original configured1000 remains; executed new draws are0')
            need(set(self.old_inputs) == set(data) | {'phi'}, 'Exactly the eleven actual data arrays and MC phi')
            # Original validation phase was all ones, distinct from optimized phases.
            phi = np.ones(data['r_mean'].shape, complex)
            comparisons = []
            for name, current in dict(data, phi=phi).items():
                old = self.old_inputs[name]
                same = (current.shape == old.shape and current.dtype.str == old.dtype.str
                        and current.tobytes(order='F') == old.tobytes(order='F'))
                comparisons.append(dict(field=name, same_dtype_shape_and_all_bits=same))
                need(same, 'Prior actual MC input/ones-phase bytes differ: '+name)
            mc = copy.deepcopy(self.complete['original_monte_carlo_return'])
            need(mc['count'] == 1000, 'Original actual MC-return population')
            self.returned = True
            fresh(self.root/'ACTUAL_EXACT_SAVED_1000_RETURN_REUSED_NO_NEW_RNG_V1.json', dict(
                exact_original_MC_return=mc, all12_data_and_ones_phi_bitwise_comparisons=comparisons,
                configuration_and_original_seed_and_count_identical=True,
                reused_MC_return_equals_original_complete_full8_result=True,
                all11_data_and_original_ones_phi_exact=True,
                reused_completed_actual_draws=1000, actual_new_MC_RNG_draws=0,
                original_actual_MC_stream_SHA256=self.complete['stream_SHA256'],
                no_new_channel_moment_statistics_or_MP_evaluation=True,
                original_independent_MC_gate_reused=True,
                new_optimization_trajectory_requires_new_independent_recording_review=True))
            return mc
        except BaseException as error:
            self.error = dict(type=type(error).__name__, message=str(error))
            raise

    def preserve_partial(self):
        # Called once by the outer runner. Even a pre-MC optimizer failure is
        # explicit: no reuse happened and no new MC is silently substituted.
        self.root.mkdir(parents=True, exist_ok=True)
        fresh(self.root/'ACTUAL_SAVED_MC_REUSE_ATTEMPT_STATUS_V1.json', dict(
            calls=self.calls, exact_saved_return_supplied=self.returned,
            failure=self.error, actual_new_MC_RNG_draws=0,
            previous_actual1000_evidence_unchanged=True))


def new_cell(value):
    return (lambda: value).__closure__[0]


def install(installation, directory, prior_directory, expected_config, audit_path):
    original = installation['entry'].original
    hook = original.full_run
    cells = dict(zip(hook.__code__.co_freevars, hook.__closure__ or ()))
    need('original_full_run' in cells, 'Frozen portable last-hook closure required')
    function = cells['original_full_run'].cell_contents
    source = inspect.getsource(function)
    need(source.count(ORIGINAL_BLOCK) == 1, 'One exact original complete MC block required')
    modified = source.replace(ORIGINAL_BLOCK, REUSE_BLOCK, 1)
    need(modified.replace(REUSE_BLOCK, ORIGINAL_BLOCK, 1) == source,
         'All original full8 optimization/control statements outside MC block unchanged')
    reuse = ExactSavedMCReuse(directory, prior_directory, expected_config, audit_path)
    namespace = dict(function.__globals__, _CAPTURE_ONLY_SAVED_MC_REUSE=reuse)
    exec(compile(modified, function.__code__.co_filename+':new-optimization-saved-MC-reuse', 'exec'), namespace)
    replacement = namespace['full_run']
    def synchronized_full_run(*args, **kwargs):
        # Recorder binds its own make_scenario/source_hashes/unchanged after install.
        namespace.update(function.__globals__)
        namespace['_CAPTURE_ONLY_SAVED_MC_REUSE'] = reuse
        return replacement(*args, **kwargs)
    closure = tuple(new_cell(synchronized_full_run) if name == 'original_full_run' else cell
                    for name, cell in zip(hook.__code__.co_freevars, hook.__closure__))
    original.full_run = types.FunctionType(hook.__code__, hook.__globals__, hook.__name__, hook.__defaults__, closure)
    original.full_run.__kwdefaults__ = hook.__kwdefaults__
    binding = dict(original_full_run_source_SHA256=hashlib.sha256(source.encode()).hexdigest(),
                   new_optimization_only_MC_block_replacement_SHA256=hashlib.sha256(modified.encode()).hexdigest(),
                   exact_inverse_reconstructs_whole_original_function=True,
                   every_full8_optimization_statement_and_original_return_unchanged=True,
                   original_recorder_installer_and_preamble_P7_capture_retained=True,
                   actual_new_MC_RNG_draws=0, original_actual1000_return_reused_only_after_exact_input_match=True,
                   first_lost_tape_not_recovered=True, action_is_new_optimization_recording_recapture=True)
    return reuse, binding
