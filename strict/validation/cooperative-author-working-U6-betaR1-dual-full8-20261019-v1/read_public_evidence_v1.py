"""Read and verify this finite evidence capsule; never optimize or draw RNG."""
from pathlib import Path
import argparse, gzip, hashlib, io, json

ROOT = Path(__file__).resolve().parent


def load_json(relative):
    raw = (ROOT / relative).read_bytes()
    return json.loads(gzip.decompress(raw) if relative.endswith('.gz') else raw)


def verify_files():
    manifest = load_json('MANIFEST.json')
    for relative, expected in manifest['files'].items():
        raw = (ROOT / relative).read_bytes()
        assert len(raw) == expected['bytes']
        assert hashlib.sha256(raw).hexdigest() == expected['SHA256'], relative
    return manifest


def load_saved_recording(lane):
    """Return every recorded numeric state, endpoint, QT input and candidate.

    scipy.io mat_struct objects retain the MATLAB field structure. No squeeze,
    phase normalization, coefficient reconstruction or numerical solver runs.
    This reader is not an independent physics or convergence oracle.
    """
    from scipy.io import loadmat
    names = {'native': 'evidence/native-all8-all55phase-all67QT-states.mat.gz',
             'python': 'evidence/python-recapture-all8-all55phase-all67QT-states.mat.gz'}
    raw = gzip.decompress((ROOT / names[lane]).read_bytes())
    return loadmat(io.BytesIO(raw), struct_as_record=False, squeeze_me=False,
                   chars_as_strings=True)['recording'][0, 0]


def load_decoded_python_recording():
    """Safe MAT+codebook decoding; never loads a pickle or executable payload.

    Scalar MATLAB structs become dictionaries, cells retain their shape, and
    numeric arrays are returned unchanged. The actual two field aliases and
    109 original None metadata values are restored. Every other numeric leaf
    is checked at its original semantic path for dtype/shape/F-order bits.
    """
    import importlib.util
    import numpy as np
    from scipy.io import loadmat
    relative = 'evidence/python-recapture-all8-all55phase-all67QT-states.mat.gz'
    raw = gzip.decompress((ROOT / relative).read_bytes())
    saved = loadmat(io.BytesIO(raw), struct_as_record=True, squeeze_me=False,
                    chars_as_strings=True)['recording']
    book = load_json('evidence/python-actual-reversible-field-and-None-codebook.json')
    def normalize(x):
        if isinstance(x, np.ndarray) and x.dtype.names:
            def one(index):
                return {name: normalize(x[name][index]) for name in x.dtype.names}
            if x.size == 1:
                return one(tuple(0 for _ in x.shape))
            out = np.empty(x.shape, object)
            for index in np.ndindex(x.shape):
                out[index] = one(index)
            return out
        if isinstance(x, np.ndarray) and x.dtype.hasobject:
            out = np.empty(x.shape, object)
            for index in np.ndindex(x.shape):
                out[index] = normalize(x[index])
            return out
        if isinstance(x, np.ndarray) and x.dtype.kind in 'US' and x.size == 1:
            return str(x.reshape(-1)[0])
        return x
    value = normalize(saved)
    # SciPy represents this actual MATLAB empty scalar struct as one None
    # object slot. Restore only the dictionary proven by the exact source JSON.
    original_config = load_json('configuration/original-exact-working-betaR1.json')
    assert original_config['tuned_not_reported']['solver_options'] == {}
    options = value['input']['configuration']['tuned_not_reported']['solver_options']
    assert isinstance(options, np.ndarray) and options.shape == (1, 1) and options[0, 0] is None
    value['input']['configuration']['tuned_not_reported']['solver_options'] = {}
    aliases = book['original_key_by_encoded_key']
    marker = book['original_None_marker_field']
    def numeric_identity(x, path='recording', result=None):
        result = {} if result is None else result
        if isinstance(x, dict):
            if set(x) == {marker}:
                return result
            for key, item in x.items():
                numeric_identity(item, path+'.'+aliases.get(key, key), result)
        elif isinstance(x, np.ndarray) and x.dtype.hasobject:
            for index in np.ndindex(x.shape):
                numeric_identity(x[index], path+str(index), result)
        elif isinstance(x, np.ndarray) and x.dtype.kind in 'biufc':
            result[path] = (x.dtype.str, x.shape,
                            hashlib.sha256(x.tobytes(order='F')).hexdigest())
        elif isinstance(x, (list, tuple)):
            for index, item in enumerate(x):
                numeric_identity(item, path+'['+str(index)+']', result)
        return result
    source = ROOT/'implementation/python/raw_backup_first_reversible_recording_MAT_transport_v2.py'
    spec = importlib.util.spec_from_file_location('_public_safe_metadata_codec', source)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    before = numeric_identity(value)
    decoded = module.decode_normalized_mat_copy(value, book)
    after = numeric_identity(decoded)
    assert before == after, 'Metadata decode changed a non-marker numeric leaf'
    def none_count(x):
        if x is None:
            return 1
        if isinstance(x, dict):
            return sum(none_count(y) for y in x.values())
        if isinstance(x, np.ndarray) and x.dtype.hasobject:
            return sum(none_count(y) for y in x.flat)
        if isinstance(x, (list, tuple)):
            return sum(none_count(y) for y in x)
        return 0
    count = none_count(decoded)
    assert count == book['original_None_values_encoded'] == 109
    return decoded, dict(original_None_values_restored=count,
                         original_field_aliases_restored=len(aliases),
                         nonmarker_numeric_leaves_bitwise_identical=len(before),
                         dtype_shape_and_F_order_bits_preserved=True,
                         pickle_loading_performed=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--state-inventory', action='store_true')
    parser.add_argument('--decode-python-metadata', action='store_true')
    args = parser.parse_args()
    manifest = verify_files()
    gates = load_json('evidence/SCOPED_SCIENCE_GATES_AND_LIMITS.json')
    comparison = load_json('evidence/dual-eight-final-evaluations.json')
    result = dict(files_verified=len(manifest['files']),
                  variant=gates['variant'],
                  native_four_saved_science_gates_closed=gates['native_all_four_saved_science_gates_closed'],
                  python_original_MC_reuse_and_new_three_gates_closed=gates['python_MC_original1000_reused_and_three_new_recording_gates_closed'],
                  eight_actual_minSINR=[{k: r[k] for k in ('scheme', 'native_minSINR', 'python_recapture_minSINR')}
                                       for r in comparison['rows']],
                  public_per_draw_MC_operands_included=False,
                  no_new_physics_MP_optimizer_or_MC_executed=True,
                  original_reference_or_fullpaper_PASS=False)
    if args.state_inventory:
        result['state_inventory'] = {}
        for lane in ('native', 'python'):
            saved = load_saved_recording(lane)
            counts = dict(final_states=saved.final_states.size,
                          phase_endpoints=saved.phase_endpoints.size,
                          QT_candidates=saved.QT_candidates.size)
            assert list(counts.values()) == [8, 55, 67]
            result['state_inventory'][lane] = counts
    if args.decode_python_metadata:
        _, result['safe_python_metadata_decode'] = load_decoded_python_recording()
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
