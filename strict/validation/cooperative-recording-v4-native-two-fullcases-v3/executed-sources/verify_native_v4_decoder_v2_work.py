"""Actual read-only decoder compatibility checks, NOT a numerical case audit."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
import mat73_readonly_work as old
import mat73_readonly_v2_work as new


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def run(args):
    assert not args.output.exists()
    state=Path(str(args.actual_result)+'.states.mat');before=sha(state)
    original=Path(old.__file__).read_text(encoding='utf-8').rstrip()
    changed=Path(new.__file__).read_text(encoding='utf-8').rstrip()
    reverse=changed.replace("if isinstance(field, h5py.Dataset) and h5py.check_dtype(ref=field.dtype) and class_name(field) == '':",
        'if isinstance(field, h5py.Dataset) and h5py.check_dtype(ref=field.dtype):')
    assert reverse==original,'Only MATLAB-class distinction permitted in the new decoder'
    audit1=Path(__file__).with_name('audit_cooperative_native_v4_actual_work.py').read_text(encoding='utf-8').rstrip()
    audit2=Path(__file__).with_name('audit_cooperative_native_v4_actual_v2_work.py').read_text(encoding='utf-8').rstrip()
    assert audit2.replace('mat73_readonly_v2_work','mat73_readonly_work')==audit1
    failure=None
    try:old.read(state,['recordedCases','recordingMetadata'])
    except ValueError as exception:failure={'exception_class':type(exception).__name__,'actual_exception_message':str(exception)}
    assert failure and failure['actual_exception_message']=='Direct fields only supported for scalar struct'
    raw=new.read(state,['recordedCases','recordingMetadata']);case=raw['recordedCases'][0]
    assert case['complete_original_return']
    ss=case['scheme_state'];trace=ss['actual_call_trace'];p=case['configuration']['reported']
    J,U,N,M,K=[int(p[x]) for x in ['J','U','N','M','K']]
    direct_cells=[];array_field_refs=[]
    with new.h5py.File(state,'r') as f:
        def visit(name,node):
            if isinstance(node,new.h5py.Dataset) and new.h5py.check_dtype(ref=node.dtype):
                metadata={'HDF5_object':name,'storage_shape':list(node.shape),'MATLAB_class':new.class_name(node)}
                (direct_cells if metadata['MATLAB_class']=='cell' else array_field_refs).append(metadata)
        f.visititems(visit)
    actual_shapes={'d_mean':list(np.asarray(ss['data']['d_mean']).shape),
        'G_mean':list(np.asarray(ss['data']['G_mean']).shape),'r_mean':list(np.asarray(ss['data']['r_mean']).shape),
        'gt_second':list(np.asarray(ss['data']['gt_second']).shape),
        'all1000_effective_channels':list(np.asarray(case['actual_moment_draw_record']['actual_effective_channels']).shape)}
    assert actual_shapes['d_mean']==[J,U,N]
    assert actual_shapes['G_mean']==[J,U,N,M]
    assert actual_shapes['all1000_effective_channels']==[J,U,N,1000]
    # A direct, class=cell ref dataset is one scalar-struct field, not the
    # number of structs in its parent. Numeric row/column data are not flattened.
    synthetic=Path(str(args.output)+'.SYNTHETIC-class-cell-fixture.h5')
    assert not synthetic.exists()
    with new.h5py.File(synthetic,'x') as f:
        refs=f.create_group('#refs#');values=[]
        for i in range(2):
            n=refs.create_dataset(str(i),data=np.array([[i+1]],float));n.attrs['MATLAB_class']=np.bytes_('double');values.append(n)
        group=f.create_group('scalar_struct');group.attrs['MATLAB_class']=np.bytes_('struct')
        cell=group.create_dataset('actual_cells',shape=(2,1),dtype=new.h5py.ref_dtype)
        cell.attrs['MATLAB_class']=np.bytes_('cell');cell[:,0]=[v.ref for v in values]
        number=group.create_dataset('number',data=np.array([[7.]],float));number.attrs['MATLAB_class']=np.bytes_('double')
        column=group.create_dataset('numeric_column',data=np.array([[11.,12.,13.]],float));column.attrs['MATLAB_class']=np.bytes_('double')
        row=group.create_dataset('numeric_row',data=np.array([[11.],[12.],[13.]],float));row.attrs['MATLAB_class']=np.bytes_('double')
    decoded=new.read(synthetic,['scalar_struct'])['scalar_struct']
    checks={'actual_native_read_only_byte_identity':before==sha(state),
        'original_decoder_failure_actually_reproduced_before_numeric_audit':failure is not None,
        'new_decoder_class_discrimination_only_source_reverse_proof':reverse==original,
        'new_auditor_reader_route_only_numeric_body_reverse_proof':audit2.replace('mat73_readonly_v2_work','mat73_readonly_work')==audit1,
        'synthetic_direct_cell_is_scalar_struct_field':isinstance(decoded,dict) and decoded['actual_cells']==[1.,2.] and decoded['number']==7.,
        'synthetic_numeric_column_not_flattened':decoded['numeric_column'].shape==(3,1),
        'synthetic_numeric_row_not_flattened':decoded['numeric_row'].shape==(1,3),
        'actual_complete_recorded_case_structure_and1000_draw_dimensions':len(ss['scheme_states'])==8 and bool(trace['phase']) and bool(trace['QT'])}
    output={'scope':'ACTUAL_MATLAB_saved_HDF5_schema_decoder_only_plus_separate_SYNTHETIC_class_cell_regression_NOT_numerical_certification',
        'checks':checks,'all_decoder_and_route_checks_pass':all(checks.values()),
        'actual_native_saved_state_sha256':before,'actual_original_decoder_failure_reproduction':failure,
        'initial_auditor_v1_tool_observation':{'session_id':46865,'exit_code':1,'raw_stderr_file_available':False,
            'phase_QT_matrix_or_moment_audit_executed':False},
        'actual_numeric_shapes_without_flattenting':actual_shapes,'actual_phase_stage_count':len(trace['phase']),
        'actual_QT_candidate_count':len(trace['QT']),
        'actual_direct_class_cell_dataset_count':len(direct_cells),'actual_noncell_ref_field_dataset_count':len(array_field_refs),
        'actual_direct_class_cell_schema_examples':direct_cells[:8],
        'actual_numeric_finalstate_audit_pass':False,'full183_or_historical_reproduction_pass':False,
        'decoder_v1_sha256':sha(old.__file__),'decoder_v2_sha256':sha(new.__file__),
        'auditor_v1_sha256':sha(Path(__file__).with_name('audit_cooperative_native_v4_actual_work.py')),
        'auditor_v2_sha256':sha(Path(__file__).with_name('audit_cooperative_native_v4_actual_v2_work.py')),
        'check_source_sha256':sha(__file__),'synthetic_fixture_sha256':sha(synthetic)}
    args.output.write_text(json.dumps(output,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'actual_decoder_class_and_source_checks_pass':all(checks.values()),
        'actual_phase_stages':len(trace['phase']),'actual_QT_candidates':len(trace['QT']),
        'actual_numeric_audit_pass':False}),flush=True)
    assert all(checks.values())


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('actual_result',type=Path);p.add_argument('output',type=Path)
    run(p.parse_args())
