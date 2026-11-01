"""Verify/read this finite saved-state capsule; no solver, physics MP or RNG."""
from pathlib import Path
import argparse, gzip, hashlib, io, json

ROOT=Path(__file__).resolve().parent
STATE_FILES={
    'native':'evidence/native-all8-all53phase-all56QT-states.mat.gz',
    'python':'evidence/python-all8-all53phase-all56QT-states.mat.gz'}

def load_json(relative):
    raw=(ROOT/relative).read_bytes()
    return json.loads(gzip.decompress(raw) if relative.endswith('.gz') else raw)

def verify_files():
    manifest=load_json('MANIFEST.json')
    for relative,expected in manifest['files'].items():
        path=(ROOT/relative).resolve()
        assert path.is_relative_to(ROOT),'Manifest path escapes capsule'
        raw=path.read_bytes()
        assert len(raw)==expected['bytes'],relative
        assert hashlib.sha256(raw).hexdigest()==expected['SHA256'],relative
    return manifest

def load_saved_recording(lane):
    """Return full original MAT arrays without squeezing or phase alignment.

    MATLAB column/row conventions remain visible. The saved MATLAB projection
    receipt proves original numeric classes/shapes/real+imag IEEE bits; SciPy's
    representation of compact MAT storage is not used to redefine that proof.
    """
    from scipy.io import loadmat
    raw=gzip.decompress((ROOT/STATE_FILES[lane]).read_bytes())
    return loadmat(io.BytesIO(raw),struct_as_record=False,squeeze_me=False,
                   chars_as_strings=True)['recording'][0,0]

def load_decoded_python_recording():
    """Safe MAT+codebook restoration. Never opens or unpickles a pickle.

    Scalar structs become dicts, cells retain MATLAB shape, and numeric arrays
    are returned unchanged. This restores metadata keys/None values, not the
    original Python scalar/list shape conventions or a new scientific result.
    """
    import importlib.util
    import numpy as np
    from scipy.io import loadmat
    raw=gzip.decompress((ROOT/STATE_FILES['python']).read_bytes())
    saved=loadmat(io.BytesIO(raw),struct_as_record=True,squeeze_me=False,
                  chars_as_strings=True)['recording']
    book=load_json('evidence/python-reversible-field-and-None-codebook.json')
    def normalize(x):
        if isinstance(x,np.ndarray) and x.dtype.names:
            def one(index):return {name:normalize(x[name][index]) for name in x.dtype.names}
            if x.size==1:return one(tuple(0 for _ in x.shape))
            out=np.empty(x.shape,object)
            for index in np.ndindex(x.shape):out[index]=one(index)
            return out
        if isinstance(x,np.ndarray) and x.dtype.hasobject:
            out=np.empty(x.shape,object)
            for index in np.ndindex(x.shape):out[index]=normalize(x[index])
            return out
        if isinstance(x,np.ndarray) and x.dtype.kind in 'US' and x.size==1:
            return str(x.reshape(-1)[0])
        return x
    value=normalize(saved)
    config=load_json('configuration/full-original-metadata-projected.json')
    assert config['tuned_not_reported']['solver_options']=={}
    options=value['input']['configuration']['tuned_not_reported']['solver_options']
    # Exact known empty source dictionary: SciPy exposes it as one object None.
    assert isinstance(options,np.ndarray) and options.shape==(1,1) and options[0,0] is None
    value['input']['configuration']['tuned_not_reported']['solver_options']={}
    aliases=book['original_key_by_encoded_key'];marker=book['original_None_marker_field']
    def numeric_identity(x,path='recording',result=None):
        result={} if result is None else result
        if isinstance(x,dict):
            if set(x)=={marker}:return result
            for key,item in x.items():numeric_identity(item,path+'.'+aliases.get(key,key),result)
        elif isinstance(x,np.ndarray) and x.dtype.hasobject:
            for index in np.ndindex(x.shape):numeric_identity(x[index],path+str(index),result)
        elif isinstance(x,np.ndarray) and x.dtype.kind in 'biufc':
            result[path]=(x.dtype.str,x.shape,hashlib.sha256(x.tobytes(order='F')).hexdigest())
        elif isinstance(x,(list,tuple)):
            for index,item in enumerate(x):numeric_identity(item,path+'['+str(index)+']',result)
        return result
    source=ROOT/'implementation/python/raw_backup_first_reversible_recording_MAT_transport_v2.py'
    spec=importlib.util.spec_from_file_location('_public_safe_ground10_codec',source)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    before=numeric_identity(value)
    decoded=module.decode_normalized_mat_copy(value,book)
    assert before==numeric_identity(decoded),'Metadata decode changed a non-marker numeric leaf'
    def none_count(x):
        if x is None:return 1
        if isinstance(x,dict):return sum(none_count(y) for y in x.values())
        if isinstance(x,np.ndarray) and x.dtype.hasobject:return sum(none_count(y) for y in x.flat)
        if isinstance(x,(list,tuple)):return sum(none_count(y) for y in x)
        return 0
    count=none_count(decoded)
    assert count==book['original_None_values_encoded']
    return decoded,dict(original_None_values_restored=count,field_aliases_restored=len(aliases),
        nonmarker_numeric_leaves_bitwise_identical=len(before),
        dtype_shape_and_F_order_bits_preserved=True,pickle_loading_performed=False)

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--state-inventory',action='store_true')
    parser.add_argument('--decode-python-metadata',action='store_true')
    parser.add_argument('--input-inventory',action='store_true')
    parser.add_argument('--output',type=Path)
    args=parser.parse_args()
    manifest=verify_files()
    gates=load_json('evidence/SCOPED_SCIENCE_GATES_AND_LIMITS.json')
    comparison=load_json('evidence/dual-eight-final-unfitted-minSINR.json')
    assert gates['both_actual_four_saved_science_gates_closed']
    assert not gates['original_reference_PASS'] and not gates['full_paper_PASS']
    assert gates['fig4_fig5_author_confirmed_user_count']==6
    result=dict(schema='actual-portable-ground10-U6-saved-capsule-file-and-structure-reader-v1',
        files_verified=len(manifest['files']),variant=gates['variant'],
        original_closed_science_receipts_all_four_per_lane_pass=True,
        original_both_full8_producers_natural0=True,
        eight_actual_minSINR=[{k:row[k] for k in ('scheme','python_minSINR_linear','native_minSINR_linear','absolute_difference')} for row in comparison['rows']],
        no_new_physics_MP_optimizer_MC_or_RNG_executed=True,
        public_per_draw_MC_primitive_streams_included=False,
        original_reference_dual_solution_equality_or_fullpaper_PASS=False,
        Fig4_Fig5_user_count_author_confirmed=6,printed_TableI_U2_discrepancy_retained=True)
    if args.state_inventory:
        result['state_inventory']={}
        for lane in STATE_FILES:
            saved=load_saved_recording(lane)
            counts=dict(final_states=saved.final_states.size,phase_endpoints=saved.phase_endpoints.size,QT_candidates=saved.QT_candidates.size)
            assert list(counts.values())==[8,53,56]
            result['state_inventory'][lane]=counts
    if args.decode_python_metadata:
        _,result['safe_python_metadata_decode']=load_decoded_python_recording()
    if args.input_inventory:
        import numpy as np
        with np.load(ROOT/'inputs/canonical-eleven-arrays-and-limits.npz',allow_pickle=False) as saved:
            assert len(saved.files)==13
            result['input_inventory']={name:dict(dtype=str(saved[name].dtype),shape=list(saved[name].shape),
                F_order_bytes_SHA256=hashlib.sha256(saved[name].tobytes(order='F')).hexdigest()) for name in saved.files}
    assert verify_files()==manifest,'Public bytes changed while being read'
    result['manifest_and_all_public_files_closed_during_this_read']=True
    if args.output:
        assert args.output.resolve()!=ROOT and not args.output.resolve().is_relative_to(ROOT),'Evidence output must be outside frozen capsule'
        with args.output.open('x',encoding='utf-8') as stream:json.dump(result,stream,indent=2,allow_nan=False);stream.write('\n')
    print(json.dumps(result,indent=2,allow_nan=False))
    return 0

if __name__=='__main__':
    raise SystemExit(main())
