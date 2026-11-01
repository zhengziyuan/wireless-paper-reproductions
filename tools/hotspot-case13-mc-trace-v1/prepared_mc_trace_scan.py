"""Disabled saved-MC metadata scan; no standalone access to historical data.

An external reviewed guard must bind the old indexed source identities and
provide an exact bounded reader. Aggregate checks are about saved records,
not authentication of the historical producer or a proof of independence.
"""
import collections
import math
import struct

ENABLED = False
START = 23368140824
END = 23495079841
FIRST = 1328008
AFTER = 1336010
SCHEMES = ('NoRIS', 'TwoStage', 'AO')
MAX_RNG_BYTES = 16384
MAX_READ_BYTES = 64 * 1024 * 1024
ALLOWED = frozenset(('MC_begin', 'MC_draw', 'geometry_begin', 'geometry_G',
                     'geometry_ground', 'geometry_end', 'MC_evaluation', 'MC_end'))


def need(value, message):
    if value is not True:
        raise ValueError(message)


def scalar_double(source, descriptor):
    h = descriptor['header']
    need(descriptor['tag'] == 'N' and h.get('class') == 'double' and
         h.get('size') == [1, 1] and h.get('isreal') is True, 'scalar double ABI')
    span, = descriptor['raw_spans']
    need(span['length'] == 8, 'scalar byte count')
    value, = struct.unpack('<d', source.read(span['offset'], 8))
    need(math.isfinite(value), 'finite saved scalar')
    return value


def text_char(source, descriptor):
    h = descriptor['header']
    need(descriptor['tag'] == 'H' and h.get('class') == 'char', 'char ABI')
    span, = descriptor['raw_spans']
    need(span['length'] <= 256, 'bounded text')
    return source.read(span['offset'], span['length']).decode('utf-16le', 'strict')


def rng_node_bytes(source, descriptor):
    """Capture a single serialized RNG struct transiently; never emit it."""
    need(descriptor['tag'] == 'S' and descriptor['header'].get('size') == [1, 1], 'rng struct ABI')
    size = descriptor['end'] - descriptor['start']
    need(0 < size <= MAX_RNG_BYTES, 'rng bytes cap')
    return source.read(descriptor['start'], size)


def nhu_bytes(source, descriptor):
    """Read one saved direct-NHU matrix exactly, for transient comparison."""
    h = descriptor['header']
    need(descriptor['tag'] == 'N' and h.get('class') == 'double' and
         h.get('size') == [15, 16] and h.get('isreal') is False, 'NHU matrix ABI')
    spans = descriptor['raw_spans']
    need(len(spans) == 2 and all(x['length'] == 15 * 16 * 8 for x in spans), 'NHU bytes')
    return tuple(source.read(x['offset'], x['length']) for x in spans)


class Audit:
    def __init__(self, references, draws=1000):
        need(type(draws) is int and 1 <= draws <= 1000, 'draw cap')
        need(set(references) == set(SCHEMES), 'reference schemes')
        need(all(len(references[s]) == draws and all(type(v) in (int, float) and
                  math.isfinite(v) for v in references[s]) for s in SCHEMES), 'reference sample inputs')
        self.draws = draws
        self.references = {s: tuple(struct.pack('<d', float(v)) for v in references[s]) for s in SCHEMES}
        self.actions = collections.Counter()
        self.draw_events = set()
        self.geometry_begins = set()
        self.geometry_ends = set()
        self.geometry_g = set()
        self.geometry_ground = set()
        self.evaluations = set()
        self.rate_mismatch = []
        self.negative_rates = []
        self.sample_array_mismatch = []
        self.nhu_mismatch = []
        self.current_nhu = None
        self.current_nhu_draw = None
        self.last_nhu = None
        self.adjacent_nhu_equal = 0
        self.adjacent_nhu_changed = 0
        self.value_context_mismatch = 0
        self.rng_before = None
        self.open_geometry_draw = None
        self.rng_after = None
        self.rng_changed = 0
        self.rng_equal = 0
        self.rng_chain_mismatch = 0
        self.rng_pairs = 0
        self.mc_rng_before = None
        self.mc_rng_after = None
        self.initial_rng_matches_first_geometry = None
        self.last_geometry_matches_mc_end = None
        self.events_seen = 0
        self.boundary_position_mismatch = 0
        self.draw_order_mismatch = 0
        self.draws_started = 0

    def accept(self, action, context, values):
        need(action in ALLOWED, 'unexpected event in MC region')
        need(all(context.get(k) == v for k, v in {'case_id': 13, 'U': 1, 'beta': 20}.items()), 'case context')
        if action == 'MC_begin' and self.events_seen != 0:
            self.boundary_position_mismatch += 1
        if action == 'MC_end' and self.events_seen != self.draws * 8 + 1:
            self.boundary_position_mismatch += 1
        self.events_seen += 1
        self.actions[action] += 1
        draw = context['MC_draw']
        if action == 'MC_begin':
            need(self.actions[action] == 1, 'duplicate MC begin')
            need(tuple(values['names']) == SCHEMES, 'saved MC scheme order')
            self.mc_rng_before = values['rng']
            self.original_draw_count = values['count']
        elif action == 'MC_end':
            need(self.actions[action] == 1, 'duplicate MC end')
            self.mc_rng_after = values['rng']
            self.actual_draw_count = values['count']
            raw = values['samples']
            need(len(raw) == self.draws * len(SCHEMES) * 8, 'saved MC sample matrix length')
            for k, scheme in enumerate(SCHEMES):
                for i in range(self.draws):
                    pos = (k * self.draws + i) * 8
                    if raw[pos:pos+8] != self.references[scheme][i]:
                        self.sample_array_mismatch.append([i+1, scheme])
            if self.rng_after is not None:
                self.last_geometry_matches_mc_end = self.rng_after == self.mc_rng_after
        elif action in ('MC_draw', 'geometry_begin', 'geometry_G', 'geometry_ground', 'geometry_end', 'MC_evaluation'):
            need(type(draw) is int and 1 <= draw <= self.draws, 'draw context range')
            if action == 'MC_draw':
                need(draw not in self.draw_events, 'duplicate draw event')
                self.draws_started += 1
                if (draw != self.draws_started or self.open_geometry_draw is not None or
                    len(self.geometry_ends) != self.draws_started - 1 or
                    len(self.evaluations) != 3 * (self.draws_started - 1)):
                    self.draw_order_mismatch += 1
                self.draw_events.add(draw)
                self.value_context_mismatch += values['draw'] != draw
            elif action == 'geometry_begin':
                need(draw not in self.geometry_begins and self.rng_before is None, 'duplicate or overlapping geometry')
                self.geometry_begins.add(draw)
                self.rng_before = values['rng']
                self.open_geometry_draw = draw
                if self.rng_after is None and self.mc_rng_before is not None:
                    self.initial_rng_matches_first_geometry = self.mc_rng_before == self.rng_before
                elif self.rng_after is not None and self.rng_after != self.rng_before:
                    self.rng_chain_mismatch += 1
            elif action == 'geometry_end':
                need(draw not in self.geometry_ends and self.rng_before is not None and
                     self.open_geometry_draw == draw, 'unpaired geometry end')
                self.geometry_ends.add(draw)
                after = values['rng']
                self.rng_changed += self.rng_before != after
                self.rng_equal += self.rng_before == after
                self.rng_pairs += 1
                self.rng_before = None
                self.open_geometry_draw = None
                self.rng_after = after
                if self.last_nhu is not None:
                    self.adjacent_nhu_equal += self.last_nhu == values['nhu']
                    self.adjacent_nhu_changed += self.last_nhu != values['nhu']
                self.current_nhu = values['nhu']
                self.last_nhu = values['nhu']
                self.current_nhu_draw = draw
            elif action in ('geometry_G', 'geometry_ground'):
                seen = self.geometry_g if action == 'geometry_G' else self.geometry_ground
                need(self.open_geometry_draw == draw and draw not in seen, 'duplicate or unpaired geometry component')
                seen.add(draw)
            else:
                scheme = values['scheme']
                need(scheme in SCHEMES and (draw, scheme) not in self.evaluations, 'scheme/draw duplicate')
                need(self.current_nhu_draw == draw and self.current_nhu is not None, 'evaluation before matching geometry')
                self.evaluations.add((draw, scheme))
                self.value_context_mismatch += values['draw'] != draw
                if context.get('scheme') not in ('', scheme):
                    self.value_context_mismatch += 1
                if struct.pack('<d', values['rate']) != self.references[scheme][draw-1]:
                    self.rate_mismatch.append([draw, scheme])
                if values['rate'] < 0:
                    self.negative_rates.append([draw, scheme])
                if values['nhu'] != self.current_nhu:
                    self.nhu_mismatch.append([draw, scheme])

    def result(self):
        expected = set(range(1, self.draws + 1))
        coverage = self.draw_events == self.geometry_begins == self.geometry_ends == expected
        components = self.geometry_g == self.geometry_ground == expected
        pairs = self.evaluations == {(d, s) for d in expected for s in SCHEMES}
        return {'draws_expected': self.draws, 'action_counts': dict(sorted(self.actions.items())),
                'original_draw_count': getattr(self, 'original_draw_count', None),
                'actual_draw_count': getattr(self, 'actual_draw_count', None),
                'reported_draw_counts_match_expected': getattr(self, 'original_draw_count', None) == self.draws == getattr(self, 'actual_draw_count', None),
                'draw_and_geometry_id_coverage': coverage,
                'geometry_G_and_ground_record_coverage': components,
                'scheme_draw_record_coverage': pairs,
                'value_context_mismatch_count': self.value_context_mismatch,
                'MC_boundary_position_mismatch_count': self.boundary_position_mismatch,
                'draw_group_order_mismatch_count': self.draw_order_mismatch,
                'rate_mismatch_count': len(self.rate_mismatch),
                'rate_mismatch_first_20': self.rate_mismatch[:20],
                'negative_saved_rate_count': len(self.negative_rates),
                'negative_saved_rate_first_20': self.negative_rates[:20],
                'MC_end_array_mismatch_count': len(self.sample_array_mismatch),
                'MC_end_array_mismatch_first_20': self.sample_array_mismatch[:20],
                'saved_direct_NHU_mismatch_count': len(self.nhu_mismatch),
                'saved_direct_NHU_mismatch_first_20': self.nhu_mismatch[:20],
                'adjacent_saved_NHU_identical_pairs': self.adjacent_nhu_equal,
                'adjacent_saved_NHU_different_pairs': self.adjacent_nhu_changed,
                'geometry_rng_pairs_compared': self.rng_pairs,
                'geometry_rng_changed_pairs': self.rng_changed,
                'geometry_rng_equal_pairs': self.rng_equal,
                'adjacent_rng_chain_mismatch_count': self.rng_chain_mismatch,
                'MC_rng_before_matches_first_geometry': self.initial_rng_matches_first_geometry,
                'last_geometry_rng_matches_MC_end': self.last_geometry_matches_mc_end,
                'serialized_rng_equality_only': True,
                'common_underlying_channel_across_schemes_proven': False,
                'statistical_independence_proven': False,
                'historical_source_authenticated': False,
                'whole_event_atomic_snapshot_proven': False,
                'full_paper_pass': False}


def scan(base, source, fields, budget, references, observe):
    """One bounded forward scan of indexed MC interval; disabled by default."""
    need(ENABLED is True, 'disabled: independent guard admission required')
    need(source.identity_locked_during_each_read is True, 'held identity source required')
    need(callable(observe), 'failure-location callback required')
    need(source.budget is budget, 'shared read budget required')
    class BoundedSource:
        identity_locked_during_each_read = True
        total = END
        def __init__(self, original):
            self.original = original
            self.budget = original.budget
        def read(self, offset, length):
            need(type(offset) is int and type(length) is int and length >= 0 and
                 START <= offset <= offset + length <= END, 'read outside MC interval')
            need(self.budget.read_bytes + length <= MAX_READ_BYTES, 'metadata read byte limit')
            return self.original.read(offset, length)
    source = BoundedSource(source)
    base.MAX_HEADER = min(base.MAX_HEADER, 64 * 1024)
    base.MAX_EVENT_NODES = min(base.MAX_EVENT_NODES, 25000)
    base.MAX_EVENT_FIELDS = min(base.MAX_EVENT_FIELDS, 512)
    audit = Audit(references)
    offset = START
    ordinal = FIRST
    while offset < END:
        observe({'stage': 'read_event', 'ordinal': ordinal, 'offset': offset,
                 'events_completed': ordinal - FIRST})
        budget.check()
        need(budget.read_bytes <= MAX_READ_BYTES, 'metadata read byte limit')
        cursor = base.Cursor(source, offset)
        need(cursor.read(1) == b'E', 'event marker')
        got = cursor.u64()
        need(got == ordinal and got < AFTER, 'event ordinal')
        action = cursor.blob(256).decode('utf-8')
        need(action in ALLOWED and action in fields, 'unexpected original event')
        wanted = {('context',), ('value',)} | {('context', key) for key in base.CONTEXT}
        wanted |= {('value', key) for key in fields[action]}
        if action == 'MC_begin':
            wanted |= {('value', 'names', '{%d}' % i) for i in range(len(SCHEMES))}
        if action == 'geometry_end':
            wanted.add(('value', 'original_return', 'nhu'))
        cursor.kept = {}
        cursor.node_count = 0
        cursor.node(wanted=wanted)
        need(cursor.read(1) == b'Z' and cursor.u64() == ordinal and cursor.offset <= END, 'event footer')
        ctx = base.context(source, cursor.kept)
        parent = cursor.kept[('value',)]
        base.scalar_parent(parent)
        need(set(parent['header']['fields']) == set(fields[action]), 'event field ABI')
        val = {}
        if action in ('MC_begin', 'MC_end'):
            val['rng'] = rng_node_bytes(source, cursor.kept[('value', 'native_rng_before' if action == 'MC_begin' else 'native_rng_after')])
            val['count'] = scalar_double(source, cursor.kept[('value', 'original_draw_count' if action == 'MC_begin' else 'actual_draw_count')])
            if action == 'MC_begin':
                names = cursor.kept[('value', 'names')]
                need(names['tag'] == 'C' and names['header']['class'] == 'cell' and
                     names['header']['numel'] == len(SCHEMES), 'MC scheme names ABI')
                val['names'] = [text_char(source, cursor.kept[('value', 'names', '{%d}' % i)]) for i in range(len(SCHEMES))]
            else:
                samples = cursor.kept[('value', 'actual_rate_samples')]
                h = samples['header']
                need(samples['tag'] == 'N' and h.get('class') == 'double' and h.get('isreal') is True and
                     h.get('size') == [audit.draws, len(SCHEMES)], 'MC sample matrix ABI')
                span, = samples['raw_spans']
                need(span['length'] == audit.draws * len(SCHEMES) * 8, 'MC sample matrix bytes')
                val['samples'] = source.read(span['offset'], span['length'])
        elif action in ('geometry_begin', 'geometry_end'):
            val['rng'] = rng_node_bytes(source, cursor.kept[('value', 'native_rng_before' if action == 'geometry_begin' else 'native_rng_after')])
            if action == 'geometry_end':
                val['nhu'] = nhu_bytes(source, cursor.kept[('value', 'original_return', 'nhu')])
        elif action in ('MC_draw', 'MC_evaluation'):
            val['draw'] = scalar_double(source, cursor.kept[('value', 'draw')])
            if action == 'MC_evaluation':
                val['scheme'] = text_char(source, cursor.kept[('value', 'scheme')])
                val['rate'] = scalar_double(source, cursor.kept[('value', 'original_rate_sample')])
                val['nhu'] = nhu_bytes(source, cursor.kept[('value', 'NHU')])
        audit.accept(action, ctx, val)
        need(budget.read_bytes <= MAX_READ_BYTES, 'metadata read byte limit')
        observe({'stage': 'event_complete', 'ordinal': ordinal,
                 'next_offset': cursor.offset, 'action': action,
                 'events_completed': ordinal - FIRST + 1,
                 'rate_mismatch_count': len(audit.rate_mismatch),
                 'geometry_rng_pairs_compared': audit.rng_pairs})
        offset = cursor.offset
        ordinal += 1
    need(offset == END and ordinal == AFTER, 'complete interval boundary')
    result = audit.result()
    result['read_bytes'] = budget.read_bytes
    result['complete_interval_recorded'] = True
    return result
