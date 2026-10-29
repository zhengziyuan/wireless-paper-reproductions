"""SOURCE-ONLY full18 typed-event ABI and scientific coverage contract.

This module imports only the standard library. It does not open campaign data,
load numerical dependencies, regenerate a field, draw RNG, optimize or invoke
MATLAB/CVX. Future decoded events are checked without squeezing/reconstructing
numeric nodes. This is not the complete independent scientific executor.
"""
import hashlib
import json
import math
from pathlib import Path
import re
import struct

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SOURCE = ROOT / 'work/hotspot-native18-return-existing-observer-prepared-v1'
CANDIDATE = SOURCE / 'candidate-scientific-source-observed18-v2'
FREEZE = SOURCE / 'SOURCE-ONLY-full18-observer-freeze-v1.json'
FREEZE_SHA = 'abf03a64ba989e24533449324d792492036f4a2e1cf0ef23632801c0bac8de5e'
SCHEMA = 'SOURCE_ONLY_FULL18_TYPEDSTREAM_SCIENTIFIC_SCOPE_V1'
WIDTH = {'double': 8, 'single': 4, 'int8': 1, 'uint8': 1, 'int16': 2,
         'uint16': 2, 'int32': 4, 'uint32': 4, 'int64': 8, 'uint64': 8,
         'logical': 1, 'char': 2}
CONTEXT = ('case_id', 'U', 'beta', 'scheme', 'start_id', 'geometry_id',
           'phase_id', 'QT_id', 'initializer_id', 'MC_draw')
SCHEMES = ('NoRIS', 'TwoStage', 'AO')
MEAN_FIELDS = ('direct_mean', 'direct_variance', 'matrix_mean',
               'matrix_variance', 'ground_mean', 'ground_variance',
               'nhu_mean', 'nhu_variance')
REQUIRED_POPULATION = dict(cases=18, starts=243, initializers=243,
                           geometry=18018, MC=54000)

# Exact value fields in the frozen existing-return exposure. No inferred field.
# phase_FG has the two explicitly different initial/accepted original packets.
FIELDS = {
    'run_begin': ('new_outer_identity', 'original_configs', 'runtime_before',
                  'native_version', 'backend_name', 'backend_version',
                  'actual_original_callback_description'),
    'case_begin': ('actual_config', 'configuration_path', 'scope', 'native_rng_before_reseed'),
    'geometry_begin': ('actual_config', 'native_rng_before'),
    'geometry_G': ('G', 'Gmean', 'Gvar'),
    'geometry_ground': ('u', 'r'),
    'geometry_end': ('original_return', 'native_rng_after', 'physical_thermal_noise_W'),
    'design_context': ('config', 'f', 'x', 'P', 'phases', 'names'),
    'start_begin': ('scheme', 'start_id', 'actual_input_phi'),
    'initializer_begin': ('Q', 'Psi', 'mu', 'nhuMu', 'noise', 'power', 'target'),
    'initializer_D': ('D',),
    'initializer_native_candidate': ('V', 'cvx_status', 'cvx_optval', 'cvx_slvtol'),
    'initializer_existing_e': ('W', 'evaluation'),
    'initializer_end': ('W', 'evaluation'),
    'initializer_ensemble_return': ('W0', 'proof', 'Q', 'Psi', 'mu', 'original_phi', 'start_id'),
    'QT_loop_begin': ('W', 'Q', 'Psi', 'evaluation', 'settings'),
    'QT_begin': ('Q', 'Psi', 'W0', 'noise', 'power', 'target'),
    'QT_aux': ('D', 'z'),
    'QT_native_candidate': ('V', 'cvx_status', 'cvx_optval', 'cvx_slvtol'),
    'QT_end': ('W', 'info', 'before', 'after', 'old_bounds', 'new_bounds', 'primal'),
    'QT_loop_iteration': ('iteration', 'W', 'history', 'existing_info'),
    'QT_loop_end': ('W', 'history', 'stop', 'solver_records'),
    'phase_begin': ('actual_initial_phi', 'x', 'mode', 'fixed_param', 'noise', 'settings'),
    'Armijo_trial': ('iteration', 'search', 'old_phi', 'trial_phi', 'alpha', 'delta', 'norm2', 'seed'),
    'Armijo_decision': ('iteration', 'search', 'accepted', 'alpha', 'delta', 'norm2'),
    'phase_iteration': ('iteration', 'phi', 'value', 'gradient', 'step', 'old_theta',
                        'new_theta', 'curvature', 'distance', 'seed', 'alpha', 'backtracks'),
    'phase_end': ('actual_final_phi', 'actual_history', 'actual_stop', 'final_gradient'),
    'AO_iteration': ('iteration', 'W', 'phi', 'Q', 'Psi', 'evaluation', 'history', 'phase_stop', 'QT_info'),
    'execute_final': ('actual_W', 'actual_phi', 'actual_initial_W', 'actual_initial_phi',
                      'Q', 'Psi', 'noise', 'power', 'target', 'no_ris', 'evaluation',
                      'status', 'history', 'proof'),
    'start_exception': ('identifier', 'message', 'stack'),
    'start_end': ('original_result',),
    'selected_state': ('scheme', 'selected_original_result', 'selected_state'),
    'MC_begin': ('native_rng_before', 'selected_states', 'names', 'original_draw_count'),
    'MC_draw': ('draw',),
    'MC_evaluation': ('draw', 'scheme', 'state', 'effective_HU', 'NHU', 'noise',
                      'existing_evaluation', 'original_rate_sample', 'existing_received_power_accumulation'),
    'MC_end': ('native_rng_after', 'actual_rate_samples', 'actual_received_power_accumulation', 'actual_draw_count'),
    'case_end': ('original_result', 'native_rng_after'),
    'case_file_closed': ('case', 'original_result_path', 'sha256', 'original_checks'),
    'backend_attempted': ('id', 'requested_nargout', 'original_args'),
    'backend_forwarded': ('id', 'requested_nargout', 'resolved', 'unresolved_optional', 'source_before'),
    'backend_returned': ('id', 'requested_nargout', 'original_returns', 'source_before', 'source_after', 'unchanged'),
    'backend_preforward_exception': ('id', 'original_invoked', 'identifier', 'message', 'stack'),
    'backend_original_exception': ('id', 'source_before', 'source_after', 'original_invoked',
                                   'original_returned', 'identifier', 'message', 'stack'),
    'run_end': ('actual_counts', 'population_complete', 'callback_forwarding_complete',
                'runtime_before', 'runtime_after', 'new_recorded_math_or_physics_pass'),
    'observer_close': ('actual_counts',),
}
FG_INITIAL = ('phi', 'value', 'gradient', 'kind')
FG_ACCEPTED = FG_INITIAL + ('iteration', 'search')
EVENT_NAMES = frozenset(FIELDS) | {'phase_FG'}
ORACLE_FUNCTIONS = ('number', 'input_matrices', 'moments', 'evaluate', 'qt_values',
                    'rate_gradient', 'criterion_gradient', 'instantaneous', 'projector_square')
ORACLE = ROOT / 'work/hotspot-native27-independent-prepared-v6/mp_original_statistics.py'


def need(value, message):
    if value is not True:
        raise ValueError(message)


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1048576), b''):
            digest.update(block)
    return digest.hexdigest()


def tree_header(node):
    need(type(node) is tuple and len(node) >= 2, 'Original typed tuple, not JSON numeric values')
    tag, header = node[:2]
    need(type(header) is dict and header.get('order') == 'MATLAB_column_major', 'Original native storage order')
    dims = header.get('size')
    need(type(dims) is list and len(dims) >= 2 and all(type(v) is int and v >= 0 for v in dims), 'Every original size dimension')
    need(type(header.get('ndims')) is int and header['ndims'] == len(dims)
         and type(header.get('numel')) is int and header['numel'] == math.prod(dims), 'Original ndims/numel without squeeze')
    if tag in (b'N', b'L', b'H'):
        cls = header['class']
        need(cls in WIDTH, 'Original supported native scalar class')
        need((tag == b'N' and cls not in ('logical', 'char') and type(header.get('isreal')) is bool)
             or (tag == b'L' and cls == 'logical') or (tag == b'H' and cls == 'char'), 'Tag/class/complex authority')
        components = 2 if tag == b'N' and not header['isreal'] else 1
        need(len(node) == 2 + components and all(type(raw) is bytes and len(raw) == header['numel'] * WIDTH[cls] for raw in node[2:]), 'Full raw components including imaginary payloads')
        if tag == b'L': need(all(v in (0, 1) for v in node[2]), 'Logical bytes are actual zero/one')
    elif tag == b'S':
        fields = header.get('fields')
        need(header['class'] == 'struct' and type(fields) is list and all(type(v) is str for v in fields)
             and len(set(fields)) == len(fields) and len(node) == 2 + header['numel'] * len(fields), 'Whole ordered struct storage')
    elif tag == b'C':
        need(header['class'] == 'cell' and len(node) == 2 + header['numel'], 'Whole original cell shape and population')
    elif tag == b'P':
        need(header['class'] in WIDTH and header['class'] != 'char' and type(header.get('isreal')) is bool
             and type(header.get('nnz')) is int and 0 <= header['nnz'] <= header['numel'] and len(node) == 5,
             'Original sparse mathematical storage, not fabricated dense mxArray bits')
        children = node[2:]
        for child in children: tree_header(child)
        nnz = header['nnz']
        for child in children[:2]:
            need(child[0] == b'N' and child[1]['class'] == 'double' and child[1]['size'] == [nnz, 1]
                 and child[1]['isreal'] is True, 'Actual MATLAB find index class/column shape')
        values = children[2]
        need(values[0] in (b'N', b'L') and values[1]['class'] == header['class']
             and values[1]['size'] == [nnz, 1] and values[1].get('isreal', True) is header['isreal'], 'Full original sparse value storage')
    else:
        raise ValueError('Unknown native tag is a retained transport failure')
    return header


def struct_fields(node, expected=None):
    header = tree_header(node)
    need(node[0] == b'S' and header['size'] == [1, 1], 'One original scalar struct, never flatten array elements')
    result = dict(zip(header['fields'], node[2:]))
    if expected is not None: need(set(result) == set(expected), 'Exact existing-return field ABI')
    return result


def text(node):
    header = tree_header(node)
    need(node[0] == b'H' and len(header['size']) == 2
         and (header['size'][0] == 1 or header['size'] == [0, 0]),
         'Native metadata char row or original empty char literal, not numeric/string cast')
    return node[2].decode('utf-16le', errors='surrogatepass')


def scalar_metadata(node, *, integer=False, minimum=None):
    header = tree_header(node)
    need(node[0] == b'N' and header['class'] == 'double' and header['size'] == [1, 1]
         and header['isreal'] is True, 'Original scalar double metadata only')
    value = struct.unpack('<d', node[2])[0]
    need(math.isfinite(value), 'Finite native context counter')
    if integer: need(value == math.trunc(value), 'Integer-valued actual native metadata counter')
    if minimum is not None: need(value >= minimum, 'Actual metadata counter lower bound')
    return int(value) if integer else value


def native_array(node, cls, sizes, *, real=None):
    """Check storage without decoding physical values or reconstructing complex."""
    header = tree_header(node)
    need(node[0] == b'N' and header['class'] == cls and header['size'] in sizes, 'Full literal native array dtype/shape')
    if real is not None: need(header['isreal'] is real, 'Native real/complex storage flag, not a guessed value flag')
    return node


def mean_inputs(node, U):
    values = struct_fields(node, MEAN_FIELDS)
    for name in MEAN_FIELDS:
        sizes = [U, 16] if name.startswith('direct_') else [25, 16] if name.startswith('matrix_') else [U, 25] if name.startswith('ground_') else [16-U, 16]
        native_array(values[name], 'double', [sizes], real=True if name.endswith('_variance') else None)
    return values


def event_value(action, value):
    need(action in EVENT_NAMES, 'Every action must match an original observed callsite')
    fields = struct_fields(value)
    if action == 'phase_FG':
        kind = text(fields['kind'])
        need(kind in ('initial', 'accepted'), 'Actual existing initial/accepted FG branch')
        need(set(fields) == set(FG_INITIAL if kind == 'initial' else FG_ACCEPTED), 'No fabricated rejected-trial FG packet')
    else: need(set(fields) == set(FIELDS[action]), 'Complete existing-return action fields')
    return fields


def envelope(action, node):
    fields = struct_fields(node, ('context', 'value'))
    context_nodes = struct_fields(fields['context'], CONTEXT)
    context = {name: text(value) if name == 'scheme' else scalar_metadata(value, integer=True)
               for name, value in context_nodes.items()}
    case = context['case_id']
    need(0 <= case <= 18, 'Original whole18 case identity')
    need(context['scheme'] in ('',) + SCHEMES, 'Original scheme, no substitute')
    if case:
        U = (case-1) % 6 + 1; beta = 10 * ((case-1) // 6)
        need(context['U'] == U and context['beta'] == beta, 'All literal original18 beta/U identities')
        need(-1 <= context['start_id'] <= U, 'Every original start0..U, no hidden start')
    else:
        need(context['U'] == context['beta'] == 0 and context['start_id'] == -1, 'Original pre-case metadata')
    for name in ('geometry_id', 'phase_id', 'QT_id', 'initializer_id', 'MC_draw'):
        need(context[name] >= 0, 'Original nonnegative stage/draw identity')
    need(context['MC_draw'] <= 1000, 'Original per-case1000 draw identity, not a trace event cap')
    return context, event_value(action, fields['value'])


def original_population(counts):
    """Storage census only. All additional actual event counts remain uncapped."""
    need(type(counts) is dict and all(type(v) is int and v >= 0 for v in counts.values()), 'Exact typed complete counts')
    need(all(counts.get(k) == v for k, v in REQUIRED_POPULATION.items()), 'Original complete18/243/18018/54000 population')
    need(all(k in counts for k in ('phase', 'QT', 'FG', 'Armijo', 'backend_attempted', 'backend_forwarded', 'backend_returned')), 'All actual variable-population counters retained')
    need(counts['backend_attempted'] == counts['backend_forwarded'] == counts['backend_returned'], 'Every actual callback forwarded/returned exactly once')
    return dict(storage_population_complete=True, independent_full18_physics_PASS=False,
                all_actual_counts=dict(counts), variable_event_counts_predicted_or_capped=False)


def source_inventory():
    """Read only frozen source/config metadata, never campaign records."""
    need(sha(FREEZE) == FREEZE_SHA, 'Exact unchanged original source-only freeze')
    freeze = json.loads(FREEZE.read_bytes())
    before = {row['path']: sha(row['path']) for row in freeze['source_files']}
    need(len(before) == 20 and all(before[row['path']] == row['sha256'] for row in freeze['source_files']), 'All original frozen20 complete source pins')
    files = [SOURCE/'observe_full18_native.m'] + [CANDIDATE/name for name in (
        'strict_hotspot_geometry.m', 'strict_hotspot_statistical.m',
        'strict_hotspot_rgd_spectral.m', 'run_strict_hotspot_statistical_validated.m')]
    calls = []
    for path in files:
        source = path.read_text(encoding='utf-8')
        for match in re.finditer(r"hotspot_full18_recorder\('([^']+)'", source):
            action = match.group(1)
            if action in ('open', 'status', 'close', 'fail'): continue
            need(action in EVENT_NAMES, 'Source event missing from explicit whole contract')
            calls.append(dict(path=path.as_posix(), source_sha256=sha(path),
                              line=source.count('\n', 0, match.start()) + 1, action=action))
    names = {row['action'] for row in calls} | {'observer_close'}
    need(names == EVENT_NAMES and sum(row['action'] == 'phase_FG' for row in calls) == 2, 'Whole action ABI and both actual FG packets')
    recorder = (SOURCE/'hotspot_full18_recorder.m').read_text(encoding='utf-8')
    need("append('observer_close',struct('actual_counts',counts))" in recorder, 'Original terminal counter packet')
    oracle_source = ORACLE.read_text(encoding='utf-8')
    need(all(re.search(r'^def ' + re.escape(name) + r'\(', oracle_source, re.M) for name in ORACLE_FUNCTIONS), 'Entire existing independent formula API, source inspection only')
    after = {path: sha(path) for path in before}
    need(before == after, 'All20 original source B_A during readonly inventory')
    return dict(schema=SCHEMA, existing_return_calls=calls, source_before=before, source_after=after,
                all20_current_source_B_A_equal=True, oracle_source=dict(path=ORACLE.as_posix(), sha256=sha(ORACLE)),
                actual_campaign_data_opened=False, native_MP_model_optimizer_RNG_backend_or_array_library_executed=False,
                complete_independent_scientific_executor_implemented=False, independent_full18_physics_PASS=False)
