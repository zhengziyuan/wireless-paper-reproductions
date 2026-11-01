"""Durable bounded-memory host for the frozen exact Eq13/Eq39 grid solver.

Scientific value/bound arithmetic is inherited byte-for-byte from exact_sources.
No optimiser, Monte Carlo, random generator or historical curve is called here.
An unfinished batch is uncertain; it is never silently evaluated again.
"""
from __future__ import annotations
from pathlib import Path
from fractions import Fraction
import copy, gzip, hashlib, json, os, pickle, shutil, struct, time


class HostError(RuntimeError):
    pass


class ResourcePause(HostError):
    pass


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def encode(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def atomic_bytes(path, raw):
    path = Path(path)
    temporary = path.with_name(path.name + '.pending')
    with temporary.open('wb') as handle:
        handle.write(raw); handle.flush(); os.fsync(handle.fileno())
    os.replace(temporary, path)


def atomic(path, value):
    atomic_bytes(path, encode(value))


def same_binding(directory, binding):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / 'binding.json'
    if path.exists():
        if path.read_bytes() != encode(binding):
            raise HostError('Exact source/input binding differs; retain existing work')
    elif any(directory.iterdir()):
        raise HostError('Unbound nonempty output is not adoptable')
    else:
        with path.open('xb') as handle:
            handle.write(encode(binding)); handle.flush(); os.fsync(handle.fileno())


def fraction_pair(value):
    return None if value is None else [str(value.numerator), str(value.denominator)]


def fraction_value(pair):
    return None if pair is None else Fraction(int(pair[0]), int(pair[1]))


def rational_digest(value):
    return sha(encode(fraction_pair(value)))


def eligible(model, prefix):
    start = prefix[-1] + 1 if prefix else 0
    return tuple(i for i in range(start, model.count)
                 if all(model.compatible[p][i] for p in prefix))


def actual_model_identity(model):
    """Pin the actual frozen binary64/rational operands, not only their recipe."""
    names = ('grid', 'compatible', 'terms', 'diagonal', 'base',
             'numerator', 'coefficient', 'eta')
    groups = {}
    for name in names:
        if hasattr(model, name):
            value = getattr(model, name)
            raw = pickle.dumps(value, protocol=5)
            groups[name] = dict(type=type(value).__name__, typed_SHA256=sha(raw))
    identity = dict(schema='actual-exact-model-typed-operands-v1',
        mode=model.mode, N=model.n, M=model.m, D=model.D,
        groups=groups, typed_serialization='local trusted Python pickle5 digest; no unpickle input')
    return dict(identity, SHA256=sha(encode(identity)))


def initial_state(model):
    return dict(schema='bounded-exact-statistical-DFS-checkpoint-v1',
                stack=[dict(prefix=[], entered=False, cursor=0)], sequence=0,
                nodes=0, leaves=0, infeasible=0, prunes=0,
                best=None, winner=None, decision_digest='0' * 64,
                certificate_bytes=0, certificate_chunks=0, certificate_chain='0' * 64,
                batch_sequence=0, elapsed_seconds=0., complete=False)


def certificate_frame(raw):
    body = gzip.compress(raw, compresslevel=6, mtime=0)
    return struct.pack('>Q', len(body)) + hashlib.sha256(body).digest() + body


def _commit(directory, old, after, events, binding_hash, max_certificate_bytes):
    """At most one durable returned batch can precede the current checkpoint."""
    directory = Path(directory)
    certificate = directory / 'pruned-prefix-certificates.frames'
    closure = dict(schema='exact-returned-search-batch-v1', binding_SHA256=binding_hash,
                   before_checkpoint_SHA256=sha(encode(old)),
                   before_batch_sequence=old['batch_sequence'], after=after,
                   certificate_frame=certificate_frame(encode(dict(
                       schema='exact-prune-prefix-witness-chunk-v1',
                       batch_sequence=old['batch_sequence'],
                       previous_chain=old['certificate_chain'], witnesses=events))) if events else b'')
    # The bounded rolling package is written before either certificate append
    # or checkpoint replacement. Failure after this point can adopt exact bytes.
    atomic_bytes(directory / 'last-returned-batch.pickle', pickle.dumps(closure, protocol=5))
    return _adopt(directory, old, closure, binding_hash, max_certificate_bytes)


def _adopt(directory, state, closure, binding_hash, max_certificate_bytes):
    if (closure['binding_SHA256'] != binding_hash
        or closure['before_checkpoint_SHA256'] != sha(encode(state))
        or closure['before_batch_sequence'] != state['batch_sequence']):
        raise HostError('Returned batch is not the next exact committed prefix')
    path = directory / 'pruned-prefix-certificates.frames'
    frame = closure['certificate_frame']
    old_offset = state['certificate_bytes']
    size = path.stat().st_size if path.exists() else 0
    if old_offset + len(frame) > max_certificate_bytes:
        raise ResourcePause('Certificate budget reached; exact returned batch preserved, no truncation')
    if size == old_offset:
        if frame:
            with path.open('ab') as handle:
                handle.write(frame); handle.flush(); os.fsync(handle.fileno())
    elif size == old_offset + len(frame):
        with path.open('rb') as handle:
            handle.seek(old_offset)
            if handle.read(len(frame)) != frame:
                raise HostError('Existing certificate tail differs from returned batch')
    else:
        raise HostError('Partial or multiple uncommitted certificate frames; retain, never replay')
    after = closure['after']
    if after['certificate_bytes'] != old_offset + len(frame):
        raise HostError('Returned batch certificate offset is inconsistent')
    if after['batch_sequence'] != state['batch_sequence'] + 1:
        raise HostError('Noncontiguous returned search batch')
    atomic(directory / 'checkpoint.json', after)
    (directory / 'inflight-batch.json').unlink()
    return after


def recover(directory, model, binding, max_certificate_bytes):
    directory = Path(directory)
    same_binding(directory, binding)
    path = directory / 'checkpoint.json'
    if not path.exists():
        if any((directory / n).exists() for n in ('inflight-batch.json', 'last-returned-batch.pickle',
                                                 'pruned-prefix-certificates.frames')):
            raise HostError('Unclosed search without initial checkpoint')
        atomic(path, initial_state(model))
    state = json.loads(path.read_bytes())
    inflight = directory / 'inflight-batch.json'
    if inflight.exists():
        pending = json.loads(inflight.read_bytes())
        saved = directory / 'last-returned-batch.pickle'
        if not saved.exists():
            raise HostError('Unreturned arithmetic batch is uncertain; no automatic replay')
        # Local pickle is only accepted under this exact output binding.
        closure = pickle.loads(saved.read_bytes())
        if (pending.get('binding_SHA256') != sha(encode(binding))
            or pending.get('batch_sequence') != closure['before_batch_sequence']
            or pending.get('checkpoint_SHA256') != closure['before_checkpoint_SHA256']):
            raise HostError('No returned package for this inflight batch; retain uncertainty')
        if state['batch_sequence'] == closure['before_batch_sequence']:
            state = _adopt(directory, state, closure, sha(encode(binding)), max_certificate_bytes)
        elif state == closure['after']:
            # Checkpoint committed but the final marker unlink failed.
            expected = state['certificate_bytes']
            actual = (directory / 'pruned-prefix-certificates.frames').stat().st_size if expected else 0
            if actual != expected:
                raise HostError('Committed search checkpoint/certificate length differs')
            frame = closure['certificate_frame']
            if frame:
                with (directory / 'pruned-prefix-certificates.frames').open('rb') as handle:
                    handle.seek(expected-len(frame))
                    if handle.read(len(frame)) != frame:
                        raise HostError('Committed last certificate frame differs from actual returned bytes')
            inflight.unlink()
        else:
            raise HostError('Checkpoint is neither side of the exact returned batch')
    size = (directory / 'pruned-prefix-certificates.frames').stat().st_size if (directory / 'pruned-prefix-certificates.frames').exists() else 0
    if size != state['certificate_bytes']:
        raise HostError('Unbound certificate tail; preserve without automatic recovery')
    return state


def _step(model, state):
    """The original lexicographic recursive DFS expressed as a bounded stack."""
    while state['stack']:
        frame = state['stack'][-1]
        prefix = tuple(frame['prefix']); remaining = eligible(model, prefix)
        r = model.n - len(prefix)
        if not frame['entered']:
            state['nodes'] += 1
            witness = None
            if len(remaining) < r:
                state['infeasible'] += 1; state['stack'].pop()
                event = dict(kind='infeasible', prefix=list(prefix))
            elif r == 0:
                value = model.value(prefix); state['leaves'] += 1
                if model.best is None or value > model.best:
                    model.best, model.winner = value, prefix
                    state['best'], state['winner'] = fraction_pair(value), list(prefix)
                state['stack'].pop()
                event = dict(kind='leaf', prefix=list(prefix), exact_value_SHA256=rational_digest(value))
            else:
                model.last_supporting_witness = None
                upper = model.upper(prefix, remaining)
                if model.best is not None and upper <= model.best:
                    state['prunes'] += 1; state['stack'].pop()
                    witness = dict(prefix=list(prefix), exact_upper_SHA256=rational_digest(upper),
                                   supporting_dyadic_counts=model.last_supporting_witness)
                    event = dict(kind='prune', **witness)
                else:
                    frame['entered'] = True
                    event = dict(kind='branch', prefix=list(prefix), exact_upper_SHA256=rational_digest(upper))
            state['sequence'] += 1
            state['decision_digest'] = sha(bytes.fromhex(state['decision_digest']) + encode(event))
            return witness
        if frame['cursor'] >= len(remaining):
            state['stack'].pop(); continue
        point = remaining[frame['cursor']]
        frame['cursor'] += 1
        state['stack'].append(dict(prefix=list(prefix) + [point], entered=False, cursor=0))
    state['complete'] = True
    return None


def search(model, directory, binding, *, batch_nodes=256, batch_witness_bytes=1024*1024,
           max_certificate_bytes=64*1024*1024, minimum_free_bytes=16*1024**3,
           pause_after_batches=None):
    """No search cap: resource limits pause a retained exact prefix, never pass it."""
    if not (1 <= batch_nodes <= 65536 and 4096 <= batch_witness_bytes <= 8*1024*1024):
        raise HostError('Invalid bounded batch configuration')
    directory = Path(directory)
    state = recover(directory, model, binding, max_certificate_bytes)
    model.best = fraction_value(state['best'])
    model.winner = tuple(state['winner']) if state['winner'] is not None else None
    completed_here = 0
    while not state['complete']:
        if shutil.disk_usage(directory).free < minimum_free_bytes:
            raise ResourcePause('Low free space at committed boundary; original search remains incomplete')
        pending = dict(binding_SHA256=sha(encode(binding)), batch_sequence=state['batch_sequence'],
                       checkpoint_SHA256=sha(encode(state)), first_decision=state['sequence'])
        atomic(directory / 'inflight-batch.json', pending)
        after = copy.deepcopy(state); events = []; witness_bytes = 0
        start = time.perf_counter(); decision_start = after['sequence']
        while after['sequence'] - decision_start < batch_nodes and witness_bytes < batch_witness_bytes:
            witness = _step(model, after)
            if witness is not None:
                events.append(witness); witness_bytes += len(encode(witness))
            if after['complete']:
                break
        after['elapsed_seconds'] += time.perf_counter() - start
        after['batch_sequence'] += 1
        frame = certificate_frame(encode(dict(schema='exact-prune-prefix-witness-chunk-v1',
            batch_sequence=state['batch_sequence'], previous_chain=state['certificate_chain'], witnesses=events))) if events else b''
        after['certificate_bytes'] += len(frame)
        if frame:
            after['certificate_chunks'] += 1
            after['certificate_chain'] = sha(bytes.fromhex(state['certificate_chain']) + frame)
        state = _commit(directory, state, after, events, sha(encode(binding)), max_certificate_bytes)
        completed_here += 1
        if pause_after_batches is not None and completed_here >= pause_after_batches and not state['complete']:
            raise ResourcePause('Requested committed-boundary pause; no scientific completion claimed')
    if state['winner'] is None:
        raise HostError('Full finite grid has no feasible geometry; no substitute is supplied')
    return model.best, tuple(state['winner']), state


def witnessed_model_class(original_class):
    """Passive tangent witness capture; inherited value/upper functions unchanged."""
    class Witnessed(original_class):
        last_supporting_witness = None
        _capture_supporting_weights = False

        def choose_weights(self, indices, remaining, r):
            weights = super().choose_weights(indices, remaining, r)
            if self._capture_supporting_weights:
                # Capture the very object returned to the exact bound, with no
                # second chooser call or change to its numeric return.
                counts = [w * (1 << 32) for w in weights]
                if not all(x.denominator == 1 for x in counts):
                    raise HostError('Supporting point is not the frozen exact dyadic hypersimplex')
                self.last_supporting_witness = [x.numerator for x in counts]
            return weights

        def supporting_upper(self, indices, remaining):
            self._capture_supporting_weights = True
            try:
                return super().supporting_upper(indices, remaining)
            finally:
                self._capture_supporting_weights = False
    return Witnessed
