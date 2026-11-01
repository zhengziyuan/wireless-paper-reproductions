"""IO-only taps on the existing full1000 moment loop. Never samples a channel.

The original sample_effective/full_run source statements are retained in order.
Removing the declared tap lines reconstructs each original function exactly.
"""
import ast
import copy
import hashlib
import inspect
import json
from pathlib import Path
import types


def need(value, message):
    if not value:
        raise ValueError(message)


def fresh(path, value):
    with Path(path).open('x', encoding='utf8', newline='\n') as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.write('\n')


def transform(source, kind):
    """Only append standalone observer statements; keep every original byte."""
    edits = ({
        "    for u in range(U):\n": "    _POWER24_MC.sample_begin(data,phi,rng)\n",
        "        r=data['r_mean'][u]+np.sqrt(data['r_var'][u])*cn(data['r_mean'][u].shape)\n": "        _POWER24_MC.r(u,r)\n",
        "            out[j,u]=d+G@(phi[u]*r)\n": "            _POWER24_MC.leaf(u,j,G,d,out[j,u])\n",
        "    return out\n": "    _POWER24_MC.sample_end(rng)\n",
    } if kind == 'sample_effective' else {
        "            powers=[]; fourths=[]\n": "            _POWER24_MC.begin(data,phi,rng,count,scene)\n",
        "                h=sample_effective(data,phi,rng); p=np.sum(abs(h)**2,axis=2); powers.append(p); fourths.append(p*p)\n": "                _POWER24_MC.power(p,powers[-1],fourths[-1])\n",
        "                'purpose':'Independent channel-moment validation, not synthetic hardcoded performance arrays'}\n": "            _POWER24_MC.finish(empirical2,empirical4,exact2,fourth,mc,rng)\n",
    })
    modified = source
    declared = []
    for original, tap in edits.items():
        need(modified.count(original) == 1, 'Exact unique frozen observer anchor: ' + original.strip())
        # The pre-return tap must precede the original return. Other taps follow.
        replacement = tap + original if original in ('    return out\n', '    for u in range(U):\n') else original + tap
        modified = modified.replace(original, replacement, 1)
        declared.append(tap)
    inverse = modified
    for tap in declared:
        need(inverse.count(tap) == 1, 'One declared observer line')
        inverse = inverse.replace(tap, '', 1)
    need(inverse == source, 'Whole source must recover exactly after removing IO taps')
    need(ast.dump(ast.parse(inverse), include_attributes=False) == ast.dump(ast.parse(source), include_attributes=False), 'Original function AST')
    return modified, declared


class PassiveTape:
    def __init__(self, directory):
        self.root = Path(directory)
        self.stream = None
        self.digest = hashlib.sha256()
        self.bytes = 0
        self.draws = self.r_rows = self.leaves = self.p_rows = 0
        self.rng = None
        self.rng_before = self.rng_after = None
        self.closed = False
        self.call_open = False
        self.current_user = self.current_satellite = None

    def begin(self, data, phi, rng, count, scene):
        import numpy as np
        need(self.stream is None and self.draws == 0 and not self.root.exists(), 'Exactly one new full1000 stream')
        need(count == 1000, 'Retain every original1000 draw')
        self.root.mkdir()
        self.J, self.U, self.N = data['d_mean'].shape
        self.M = data['r_mean'].shape[1]
        need(phi.shape == (self.U, self.M), 'Complete original fixed phase')
        self.rng = rng
        self.rng_before = copy.deepcopy(rng.bit_generator.state)
        self.scene = copy.deepcopy(scene)
        self.stream = (self.root / 'actual-primitive-vector-stream.bin').open('xb')
        self.input_path = self.root / 'actual-moment-input.npz'
        # Save actual inputs only. No scenario generation, RNG or moments call.
        with self.input_path.open('xb') as handle:
            np.savez_compressed(handle, phi=phi, **data)
        fresh(self.root / 'actual-moment-start.json', dict(
            count=count, J=self.J, U=self.U, N=self.N, M=self.M,
            configuration=self.scene, RNG_before=self.rng_before,
            input_npz=self.input_path.name,
            input_npz_SHA256=hashlib.sha256(self.input_path.read_bytes()).hexdigest(),
            tape_is_actual_original_calls_not_regeneration=True,
            first_true_use_independent_math_pending=True))

    def write(self, array):
        import numpy as np
        raw = np.asarray(array, dtype='<f8').ravel(order='F').tobytes()
        need(self.stream.write(raw) == len(raw), 'Complete passive stream write')
        self.digest.update(raw)
        self.bytes += len(raw)

    def complex(self, array):
        self.write(array.real)
        self.write(array.imag)

    def sample_begin(self, data, phi, rng):
        need(self.stream is not None and not self.call_open and self.draws < 1000, 'One original sample call per draw')
        need(rng is self.rng, 'Keep the exact original RNG object')
        need(data['d_mean'].shape == (self.J, self.U, self.N) and phi.shape == (self.U, self.M), 'Unchanged full sample dimensions')
        self.call_open = True
        self.current_user = self.current_satellite = -1

    def r(self, u, r):
        need(self.call_open and u == self.current_user + 1 and r.shape == (self.M,), 'Shared user r in original user order')
        if u:
            need(self.current_satellite == self.J - 1, 'Every previous satellite captured')
        self.current_user = u
        self.current_satellite = -1
        self.complex(r)
        self.r_rows += 1

    def leaf(self, u, j, G, d, h):
        need(self.call_open and u == self.current_user and j == self.current_satellite + 1, 'Original satellite order')
        need(G.shape == (self.N, self.M) and d.shape == h.shape == (self.N,), 'Full physical primitive/vector shapes')
        self.complex(G)
        self.complex(d)
        self.complex(h)
        self.current_satellite = j
        self.leaves += 1

    def sample_end(self, rng):
        need(self.call_open and rng is self.rng and self.current_user == self.U - 1 and self.current_satellite == self.J - 1, 'One complete actual sample')
        self.draws += 1
        self.call_open = False

    def power(self, p, actual_p, actual_p_squared):
        need(not self.call_open and self.draws == self.p_rows + 1 and p is actual_p, 'Capture original caller p and stored p*p')
        need(p.shape == actual_p_squared.shape == (self.J, self.U), 'Complete returned caller powers')
        self.write(actual_p)
        self.write(actual_p_squared)
        self.p_rows += 1

    def finish(self, empirical2, empirical4, exact2, exact4, mc, rng):
        need(rng is self.rng and self.draws == self.p_rows == 1000, 'Every original1000 caller result recorded')
        need(self.r_rows == 1000 * self.U and self.leaves == 1000 * self.U * self.J, 'All physical primitive rows')
        self.rng_after = copy.deepcopy(rng.bit_generator.state)
        need(mc['count'] == 1000, 'Original MC return count')
        expected = 1000 * (self.U * 2 * self.M + self.U * self.J * 2 * (self.N * self.M + 2 * self.N) + 2 * self.J * self.U) * 8
        need(self.bytes == expected, 'No missing or extra primitive/vector bytes')
        self.stream.flush()
        self.stream.close()
        self.closed = True
        fresh(self.root / 'actual-moment-tape-complete.json', dict(
            schema='actual-online-original1000-physical-primitive-vector-tape-python-v1',
            count=1000, completed_draws=self.draws, caller_power_rows=self.p_rows,
            physical_r_rows=self.r_rows, physical_G_d_h_rows=self.leaves,
            J=self.J, U=self.U, N=self.N, M=self.M,
            stream='actual-primitive-vector-stream.bin', stream_bytes=self.bytes,
            stream_SHA256=self.digest.hexdigest(),
            layout='little-endian float64; each draw: user r(real,imag), each satellite G(real,imag,F),d(real,imag),h(real,imag); then caller p(J,U,F),original stored p*p(J,U,F)',
            RNG_before=self.rng_before, RNG_after=self.rng_after,
            empirical_second=empirical2.tolist(), empirical_fourth=empirical4.tolist(),
            exact_second=exact2.tolist(), exact_fourth=exact4.tolist(),
            original_monte_carlo_return=mc, actual_new_observer_RNG_calls=0,
            actual_original_moment_draws=1000, optimized_performance_MC=False,
            scientific_physical_dual_reference_PASS=False,
            full_vectors_and_inputs_saved_but_independent_first_use_pending=True))

    def preserve_partial(self):
        if self.stream is None or self.closed:
            return
        self.stream.flush()
        self.stream.close()
        self.closed = True
        fresh(self.root / 'actual-moment-tape-partial.json', dict(
            complete=False, completed_sample_returns=self.draws,
            caller_power_rows=self.p_rows, physical_r_rows=self.r_rows,
            physical_G_d_h_rows=self.leaves, stream_bytes=self.bytes,
            stream_SHA256=self.digest.hexdigest(), call_open=self.call_open,
            original_failed_or_partial_output_retained=True, independent_PASS=False))


def new_cell(value):
    return (lambda: value).__closure__[0]


def install(installation, directory):
    """Replace only the retained full_run closure and its sampler global copy."""
    original = installation['entry'].original
    hook = original.full_run
    cells = dict(zip(hook.__code__.co_freevars, hook.__closure__ or ()))
    need('original_full_run' in cells, 'Exact reviewed portable full8 hook closure')
    full_run = cells['original_full_run'].cell_contents
    sample = full_run.__globals__['sample_effective']
    tape = PassiveTape(directory)
    sampler_source = inspect.getsource(sample)
    full_source = inspect.getsource(full_run)
    sampler_modified, sample_taps = transform(sampler_source, 'sample_effective')
    full_modified, full_taps = transform(full_source, 'full_run')
    sampler_globals = dict(sample.__globals__, _POWER24_MC=tape)
    exec(compile(sampler_modified, sample.__code__.co_filename + ':power24-passive-IO', 'exec'), sampler_globals)
    full_globals = dict(full_run.__globals__, _POWER24_MC=tape, sample_effective=sampler_globals['sample_effective'])
    exec(compile(full_modified, full_run.__code__.co_filename + ':power24-passive-IO', 'exec'), full_globals)
    replacement = full_globals['full_run']
    # The recorder changes original.make_scenario/source_hashes/unchanged later.
    # Keep those dynamic globals aligned at the last_hook call boundary.
    def synchronized_full_run(*args, **kwargs):
        for name in full_run.__code__.co_names:
            if name in full_run.__globals__ and name not in ('sample_effective',):
                full_globals[name] = full_run.__globals__[name]
        return replacement(*args, **kwargs)
    closure = tuple(new_cell(synchronized_full_run) if name == 'original_full_run' else cell
                    for name, cell in zip(hook.__code__.co_freevars, hook.__closure__))
    original.full_run = types.FunctionType(hook.__code__, hook.__globals__, hook.__name__, hook.__defaults__, closure)
    original.full_run.__kwdefaults__ = hook.__kwdefaults__
    binding = dict(original_full_run_source_SHA256=hashlib.sha256(full_source.encode()).hexdigest(),
                   original_sampler_source_SHA256=hashlib.sha256(sampler_source.encode()).hexdigest(),
                   modified_full_run_source_SHA256=hashlib.sha256(full_modified.encode()).hexdigest(),
                   modified_sampler_source_SHA256=hashlib.sha256(sampler_modified.encode()).hexdigest(),
                   full_run_tap_lines=full_taps, sample_tap_lines=sample_taps,
                   inverse_recovers_entire_original_function_bytes=True,
                   original_recorder_installer_last_hook_preserved=True,
                   replacement_closure_cells=['original_full_run'], no_new_RNG_or_optimizer_calls_by_observer=True)
    return tape, binding
