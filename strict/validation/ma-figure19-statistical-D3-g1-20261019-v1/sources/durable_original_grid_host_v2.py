"""Host-only durable original ordered-grid evaluation; no alternate objective.

The injected evaluator is the unchanged original core.instantaneous function.
An uncertain invocation is never automatically replayed. Typed local returns
are trusted artifacts of this source-bound runner, not arbitrary pickle inputs.
"""
from pathlib import Path
import hashlib, json, os, pickle, struct, time
import numpy as np


class HostFailure(RuntimeError):
    pass


class OriginalScientificFailure(RuntimeError):
    def __init__(self, detail):
        self.detail = detail
        super().__init__(json.dumps(detail, sort_keys=True))


class SafePause(RuntimeError):
    """A completed-candidate boundary; only used by finite host controls."""


def digest(data):
    return hashlib.sha256(data).hexdigest()


def encoded(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def atomic(path, value):
    path = Path(path)
    data = encoded(value)
    temporary = path.with_name(path.name + '.pending')
    with temporary.open('wb') as handle:
        handle.write(data)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


def same_binding(directory, binding):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / 'binding.json'
    if path.exists():
        if json.loads(path.read_bytes()) != binding:
            raise HostFailure('Existing work has a different exact source/input binding')
    else:
        if any(directory.iterdir()):
            raise HostFailure('Unbound nonempty work directory is not adoptable')
        with path.open('xb') as handle:
            handle.write(encoded(binding)); handle.flush(); os.fsync(handle.fileno())


def pack_return(value):
    return pickle.dumps(value, protocol=5)


def failure(error):
    return dict(type=type(error).__name__, module=type(error).__module__, message=str(error))


class OriginalCallTape:
    """Append typed original return objects; replay them without reoptimization.

    Called functions themselves are unchanged. On a resumed run the original
    run_job executes its own deterministic bookkeeping, taking prior function
    returns from this tape. A full durable frame closes a call. A partial frame
    or unclosed inflight call stops recovery instead of invoking it again.
    """
    def __init__(self, directory, binding):
        self.directory = Path(directory)
        same_binding(self.directory, binding)
        self.path = self.directory / 'original-returns.bin'
        self.inflight = self.directory / 'inflight.json'
        self.offset = 0
        self.ordinal = 0
        self.reused = 0
        self.fresh = 0

    def call(self, name, function, args, kwargs):
        identity = dict(ordinal=self.ordinal, name=name,
                        exact_argument_pickle_SHA256=digest(pack_return((args, kwargs))))
        self.ordinal += 1
        size = self.path.stat().st_size if self.path.exists() else 0
        if self.offset < size:
            with self.path.open('rb') as handle:
                handle.seek(self.offset); header = handle.read(40)
                if len(header) != 40:
                    raise HostFailure('Partial return frame retained; no automatic reinvocation')
                length = struct.unpack('>Q', header[:8])[0]
                if length > 256 * 1024 * 1024:
                    raise HostFailure('Return frame exceeds declared bounded-frame size')
                body = handle.read(length)
            if len(body) != length or hashlib.sha256(body).digest() != header[8:]:
                raise HostFailure('Unclosed/corrupt return frame retained; no reinvocation')
            frame = pickle.loads(body)
            if frame['identity'] != identity:
                raise HostFailure('Original call order/operands changed at recorded return')
            self.offset += 40 + length
            self.reused += 1
            if self.inflight.exists() and json.loads(self.inflight.read_bytes()) == identity:
                self.inflight.unlink()  # Complete frame is the actual closure evidence.
            if frame['kind'] == 'original_exception':
                raise OriginalScientificFailure(frame['exception'])
            return frame['return']
        if self.inflight.exists():
            raise HostFailure('Unclosed original call remains uncertain; never automatically rerun')
        atomic(self.inflight, identity)
        try:
            returned = function(*args, **kwargs)
        except Exception as error:
            frame = dict(identity=identity, kind='original_exception', exception=failure(error))
            self._append(frame)
            self.fresh += 1
            raise OriginalScientificFailure(frame['exception']) from error
        frame = dict(identity=identity, kind='original_return', **{'return': returned})
        self._append(frame)
        self.fresh += 1
        return returned  # The actual original object, not a reconstructed first-use copy.

    def _append(self, frame):
        body = pack_return(frame)
        with self.path.open('ab') as handle:
            handle.write(struct.pack('>Q', len(body)) + hashlib.sha256(body).digest() + body)
            handle.flush(); os.fsync(handle.fileno())
        self.offset += 40 + len(body)
        self.inflight.unlink()

    def ensure_consumed(self):
        if self.offset != (self.path.stat().st_size if self.path.exists() else 0):
            raise HostFailure('Original execution returned with unused prior scientific calls')
        if self.inflight.exists():
            raise HostFailure('Original execution returned with an unclosed call')


def _float_bits(value):
    if not isinstance(value, (float, np.floating)) or np.asarray(value).dtype.itemsize != 8:
        raise HostFailure('Original objective must return its binary64 scalar mean')
    return struct.pack('>d', value).hex()


def _float(bits):
    return struct.unpack('>d', bytes.fromhex(bits))[0]


def exhaustive_saved(c, n, D, mode, nlos, directory, binding, original_instantaneous,
                     pause_after_commits=None):
    """Original finite-MC DFS order/spacing/strict ties, with durable continuation.

    This only implements the explicitly selected instantaneous_MC protocol.
    The statistical protocol is rejected, never silently replaced or pruned.
    """
    if c['brute_force_objective'] != 'instantaneous_MC':
        raise HostFailure('Only explicitly declared fixed-draw instantaneous_MC is supported')
    if len(nlos) != 1000 or mode not in ('MRT', 'ZF'):
        raise HostFailure('Complete1000 fixed draws and original MRT/ZF are mandatory')
    directory = Path(directory)
    args_digest = digest(pack_return((c, n, D, mode, nlos)))
    selected_binding = dict(binding, exact_original_search_arguments_SHA256=args_digest,
                            objective='instantaneous_MC', D=int(D), N=int(n), mode=mode)
    same_binding(directory, selected_binding)
    checkpoint = directory / 'checkpoint.json'
    log = directory / 'candidate-closures.jsonl'
    inflight = directory / 'inflight.json'
    grid = np.array([[x, y] for x in np.linspace(c['region_lower'][0], c['region_upper'][0], D)
                     for y in np.linspace(c['region_lower'][1], c['region_upper'][1], D)])
    if checkpoint.exists():
        state = json.loads(checkpoint.read_bytes())
    else:
        if log.exists() or inflight.exists():
            raise HostFailure('Missing initial checkpoint: cannot adopt unbound prefix')
        state = dict(stack=[dict(indices=[], next_point=0)], tested=0, pruned=0,
                     best_bits=_float_bits(float('-inf')), winner_indices=None,
                     nonfinite_objectives=0, closed_failure=None,
                     log_offset=0, last_closure_SHA256=None, elapsed_seconds=0.0, complete=False)
        atomic(checkpoint, state)
    # At most one returned closure can precede a failed checkpoint replacement.
    size = log.stat().st_size if log.exists() else 0
    if size < state['log_offset']:
        raise HostFailure('Candidate log shorter than committed checkpoint')
    if size > state['log_offset']:
        with log.open('rb') as handle:
            handle.seek(state['log_offset']); tail = handle.read(2 * 1024 * 1024 + 1)
        if len(tail) > 2 * 1024 * 1024 or not tail.endswith(b'\n') or tail.count(b'\n') != 1:
            raise HostFailure('Unclosed candidate tail retained; no candidate automatically replayed')
        closure = json.loads(tail)
        payload = closure['payload']
        if digest(encoded(payload)) != closure['SHA256']:
            raise HostFailure('Candidate closure digest mismatch')
        if payload['previous_closure_SHA256'] != state['last_closure_SHA256']:
            raise HostFailure('Candidate prefix chain differs')
        recovered = payload['after']
        if recovered['tested'] != state['tested'] + 1:
            raise HostFailure('Noncontiguous candidate prefix')
        recovered['log_offset'] = size
        recovered['last_closure_SHA256'] = closure['SHA256']
        state = recovered
        atomic(checkpoint, state)
    if inflight.exists():
        pending = json.loads(inflight.read_bytes())
        if pending['ordinal'] == state['tested'] - 1 and pending['ordinal'] >= 0:
            inflight.unlink()  # Recovered or committed actual returned closure.
        else:
            raise HostFailure('Original candidate invocation uncertain: retained, never rerun')
    if state['closed_failure'] is not None:
        raise OriginalScientificFailure(state['closed_failure'])
    was_complete_at_entry = state['complete']
    start = time.perf_counter()
    committed_here = 0
    while state['stack']:
        frame = state['stack'][-1]
        indices = frame['indices']
        if len(indices) == n:
            identity = dict(ordinal=state['tested'], indices=indices)
            atomic(inflight, identity)
            error = None
            # The only candidate scientific evaluation; exact original function and arguments.
            try:
                value = original_instantaneous(grid[indices], c, nlos, mode)['mean_sum_rate']
            except Exception as original_error:
                error = failure(original_error)
                value = None
            state['stack'].pop()
            state['tested'] += 1
            if error is None:
                bits = _float_bits(value)
                state['nonfinite_objectives'] += int(not np.isfinite(value))
                if value > _float(state['best_bits']):  # Exactly original strict first-tie rule.
                    state['best_bits'] = bits
                    state['winner_indices'] = indices
            else:
                bits = None
                state['closed_failure'] = error
            state['elapsed_seconds'] += time.perf_counter() - start
            payload = dict(previous_closure_SHA256=state['last_closure_SHA256'], identity=identity,
                           objective_binary64_bits=bits, original_exception=error,
                           after=dict(state))
            body = dict(payload=payload, SHA256=digest(encoded(payload)))
            line = encoded(body) + b'\n'
            with log.open('ab') as handle:
                handle.write(line); handle.flush(); os.fsync(handle.fileno()); offset = handle.tell()
            state['log_offset'] = offset
            state['last_closure_SHA256'] = body['SHA256']
            atomic(checkpoint, state)
            inflight.unlink()
            committed_here += 1
            if error is not None:
                raise OriginalScientificFailure(error)
            if pause_after_commits is not None and committed_here >= pause_after_commits:
                raise SafePause('Finite host-control completed-boundary pause')
            start = time.perf_counter()
            continue
        if frame['next_point'] >= len(grid):
            state['stack'].pop()
            continue
        point = frame['next_point']
        frame['next_point'] += 1
        if indices and np.any(np.linalg.norm(grid[indices] - grid[point], axis=1) < c['minimum_distance']):
            state['pruned'] += 1
            continue
        state['stack'].append(dict(indices=indices + [point], next_point=0))
    if not was_complete_at_entry:
        state['complete'] = True
        state['elapsed_seconds'] += time.perf_counter() - start
        atomic(checkpoint, state)
    if state['winner_indices'] is None:
        raise OriginalScientificFailure(dict(type='RuntimeError', module='builtins',
                                              message='No feasible complete grid geometry.'))
    record = dict(D=D, N=n, mode=mode, evaluated_feasible_geometries=state['tested'],
                  pruned_partial_branches=state['pruned'], objective=_float(state['best_bits']),
                  elapsed_seconds=state['elapsed_seconds'], complete=True,
                  permutation_symmetry_reduction=False, objective_protocol=c['brute_force_objective'])
    return grid[state['winner_indices']].copy(), record
