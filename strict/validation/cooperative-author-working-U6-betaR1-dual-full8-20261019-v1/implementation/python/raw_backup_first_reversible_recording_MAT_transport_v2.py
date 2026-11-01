"""Prepared transport only; never computes or reconstructs scientific values.

Install on a fresh recorder BEFORE its numerical action. The old failed run's
128-byte MAT cannot be repaired by this module: its full in-memory tape is gone.
No optimizer/RNG/source factory is imported or called here.
"""
from pathlib import Path
import hashlib
import json
import os
import pickle
import re


def fresh_bytes(path, raw):
    with Path(path).open('xb') as stream:
        if stream.write(raw) != len(raw):
            raise OSError('Incomplete exclusive transport write')
        stream.flush()
        os.fsync(stream.fileno())


def fresh_json(path, value):
    fresh_bytes(path, (json.dumps(value, indent=2, allow_nan=False)+'\n').encode('utf-8'))


def encode_mat_copy(value):
    """Reversible field names/nulls on a COPY; all numeric arrays unchanged.

    Raw backup is authoritative and includes original None/dict keys. MAT readers
    can use the codebook after ordinary MAT structs/cells are normalized to
    dictionaries/object arrays. This is a schema codec, not a numerical repair.
    """
    import numpy as np
    keys = set()
    def inventory(x):
        if isinstance(x, dict):
            for key, item in x.items():
                if not isinstance(key, str):
                    raise TypeError('Only string recording dictionary keys supported')
                keys.add(key)
                inventory(item)
        elif isinstance(x, (list, tuple)):
            for item in x:
                inventory(item)
        elif isinstance(x, np.ndarray) and x.dtype.hasobject:
            for item in x.flat:
                inventory(item)
    inventory(value)
    aliases = {}
    for key in sorted(keys):
        if len(key) <= 63 and re.fullmatch(r'[A-Za-z][A-Za-z0-9_]*', key):
            continue
        # Reversible aliases cover both long keys and short unsafe metadata
        # such as actual source binding keys core.py; no key is dropped.
        salt = 0
        while True:
            encoded = 'longfield_'+hashlib.sha256((str(salt)+'\0'+key).encode()).hexdigest()[:48]
            if encoded not in keys and encoded not in aliases:
                aliases[encoded] = key
                break
            salt += 1
    null_key = 'transport_original_None_marker_v1'
    while null_key in keys or null_key in aliases:
        null_key += '_'
    if len(null_key) > 63:
        raise ValueError('Cannot reserve null marker; raw backup retained')
    by_original = {original: encoded for encoded, original in aliases.items()}
    none_count = 0
    def encode(x):
        nonlocal none_count
        if x is None:
            none_count += 1
            return {null_key: np.uint8(1)}
        if isinstance(x, dict):
            return {by_original.get(key, key): encode(item) for key, item in x.items()}
        if isinstance(x, list):
            return [encode(item) for item in x]
        if isinstance(x, tuple):
            return tuple(encode(item) for item in x)
        if isinstance(x, np.ndarray) and x.dtype.hasobject:
            result = np.empty(x.shape, dtype=x.dtype)
            for index in np.ndindex(x.shape):
                result[index] = encode(x[index])
            return result
        return x  # In particular, no cast/copy/arithmetic on numeric arrays.
    encoded = encode(value)
    codebook = dict(schema='recording-MAT-safe-field-name-and-original-None-codec-v2',
                    original_key_by_encoded_key=aliases,
                    original_None_marker_field=null_key,
                    original_None_values_encoded=none_count,
                    numerical_arrays_dtype_shape_and_values_not_modified=True)
    return encoded, codebook


def decode_normalized_mat_copy(value, codebook):
    """Decode already normalized MAT dictionaries/cells, not a raw mat_struct."""
    import numpy as np
    aliases = codebook['original_key_by_encoded_key']
    null_key = codebook['original_None_marker_field']
    def decode(x):
        if isinstance(x, dict):
            if set(x) == {null_key}:
                marker = np.asarray(x[null_key])
                if marker.size != 1 or int(marker.reshape(-1)[0]) != 1:
                    raise ValueError('Corrupt original-None transport marker')
                return None
            return {aliases.get(key, key): decode(item) for key, item in x.items()}
        if isinstance(x, list):
            return [decode(item) for item in x]
        if isinstance(x, tuple):
            return tuple(decode(item) for item in x)
        if isinstance(x, np.ndarray) and x.dtype.hasobject:
            result = np.empty(x.shape, dtype=x.dtype)
            for index in np.ndindex(x.shape):
                result[index] = decode(x[index])
            return result
        return x
    return decode(value)


def install_raw_backup_first_recorder_saver(recorder):
    """Patch only recorder.savemat; science/recorder loop remains untouched.

    A successful exclusive protocol5 pickle is written before attempting any
    MAT encoding. Loading that backup later requires an explicitly trusted local
    artifact with its saved digest; never unpickle downloaded/untrusted evidence.
    """
    original_savemat = recorder.savemat
    def backup_first_savemat(filename, mdict, *args, **kwargs):
        path = Path(filename)
        if path.exists():
            raise FileExistsError('Preserve prior MAT or damaged header: '+str(path))
        backup = Path(str(path)+'.full-unaltered-recording-before-MAT.pickle')
        mapping = Path(str(path)+'.reversible-field-and-None-codec.json')
        outcome = Path(str(path)+'.transport-outcome.json')
        raw = pickle.dumps(mdict, protocol=5)
        fresh_bytes(backup, raw)
        receipt = dict(raw_backup=backup.name, raw_backup_bytes=len(raw),
                       raw_backup_SHA256=hashlib.sha256(raw).hexdigest(),
                       raw_backup_contains_full_unmodified_input_payload=True,
                       original_saved_payload_not_numerically_recomputed=True,
                       MAT_written=False, error=None,
                       independent_scientific_acceptance_PASS=False)
        try:
            encoded, codebook = encode_mat_copy(mdict)
            fresh_json(mapping, codebook)
            result = original_savemat(path, encoded, *args, **kwargs)
            receipt.update(MAT_written=True, MAT_bytes=path.stat().st_size,
                           reversible_codebook=mapping.name,
                           field_alias_count=len(codebook['original_key_by_encoded_key']),
                           original_None_values_encoded=codebook['original_None_values_encoded'])
            return result
        except BaseException as error:
            receipt['error'] = dict(type=type(error).__name__, message=str(error))
            raise
        finally:
            fresh_json(outcome, receipt)
    recorder.savemat = backup_first_savemat
    return dict(only_recorder_savemat_wrapper_changed=True,
                unmodified_raw_backup_precedes_any_MAT_codec_or_write=True,
                original_scientific_functions_or_calls_changed=False,
                installer_first_true_use_pending=True)
