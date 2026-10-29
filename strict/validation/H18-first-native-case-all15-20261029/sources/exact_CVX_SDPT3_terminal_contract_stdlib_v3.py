"""SOURCE ONLY exact native CVX/SDPT3 requested-return classification.

Only STD raw-byte inspection. Never MP-promotes NaN/Inf, replaces a native
word, calls a backend, or labels an unavailable point residual PASS. The
source-bound shim vocabulary is not outer CVX's final-status vocabulary.
"""
import math
from pathlib import Path
import struct
from bounded_closed_typed_reader_sourceonly_v1 import need

HERE=Path(__file__).resolve().parent
CVX_SHIM=HERE.parents[1]/'work/external-cvx-2.2.2/cvx/shims/cvx_sdpt3.m'
CVX_SHIM_SHA='c0fce2601a79a45ed2374ca579608132718a610a2aafe4a84ccd54ba8c82a0bf'
STATUS=('Solved','Inaccurate/Solved','Infeasible','Unbounded','Failed')


def raw_provenance(node):
    out=dict(tag=node.tag.decode('ascii'),header=dict(node.header),
        global_start=node.global_start,global_end=node.global_end)
    if node.tag==b'P':out['all_original_children']=[raw_provenance(child) for child in node.parts]
    else:out['all_original_raw_components']=[dict(global_offset=part.offset,bytes=part.length,SHA256=part.digest()) for part in node.parts]
    return out


def _word_bytes(span):
    tail=b''
    for block in span.slices():
        payload=tail+block;end=len(payload)//8*8
        for at in range(0,end,8):yield payload[at:at+8]
        tail=payload[end:]
    need(tail==b'','No incomplete native binary64 word in terminal output')


def _category(word):
    bits=int.from_bytes(word,'little');exponent=(bits>>52)&2047;fraction=bits&((1<<52)-1)
    if exponent!=2047:return 'finite'
    if fraction:return 'NaN'
    return 'negative_Infinity' if bits>>63 else 'positive_Infinity'


def scan_real_numeric(node,shape):
    count=math.prod(shape)
    need(node.tag==b'N' and node.header.get('class')=='double' and node.header.get('size')==shape
        and type(node.header.get('size')) is list and len(node.header['size'])==len(shape)
        and all(type(value) is int and value>=0 for value in node.header['size'])
        and type(node.header.get('ndims')) is int and node.header['ndims']==len(shape)
        and type(node.header.get('numel')) is int and node.header['numel']==count
        and node.header.get('isreal') is True and node.header.get('order')=='MATLAB_column_major'
        and all(type(value) is int and value>=0 for value in shape)
        and len(node.parts)==1 and node.parts[0].length==8*count,
        'Exact original real double output/coefficient dimensions and all word bytes')
    rows=[];counts={kind:0 for kind in ('finite','NaN','positive_Infinity','negative_Infinity')}
    for index,word in enumerate(_word_bytes(node.parts[0])):
        category=_category(word);counts[category]+=1
        rows.append(dict(native_logical_index=index,original_binary64_little_endian_hex=word.hex(),
            original_global_word_offset=node.parts[0].offset+8*index,classification=category))
    need(len(rows)==count,'Every original requested numeric return/coefficient coordinate')
    return dict(actual_native_storage=raw_provenance(node),full_original_component_count=count,
        all_original_binary64_words=rows,classification_counts=counts,
        all_finite=counts['finite']==count,all_NaN=counts['NaN']==count,
        nonfinite_component_count=count-counts['finite'],point_residual_PASS=False)


def scan_vector(node,count):
    need(type(count) is int and count>=0,'Exact native output logical count')
    shape=node.header.get('size')
    need(type(shape) is list and len(shape)==2 and all(type(value) is int and value>=0 for value in shape)
        and shape in ([count,1],[1,count]),'Whole native row/column vector, no squeeze')
    result=scan_real_numeric(node,shape)
    # The frozen shim uses all(isfinite(point)); an unavailable return is
    # explicitly NaN*ones(...), not a partially repaired mixed-finite vector.
    need(result['all_finite'] or result['all_NaN'],
        'Exact original shim finite-vector OR all-NaN-vector return boundary')
    result['finite_point_available']=result['all_finite']
    result['finite_point_residual_scope']='AVAILABLE_POINT_DIAGNOSTIC_NOT_OPTIMALITY_PASS' if result['all_finite'] else 'UNAVAILABLE_NATIVE_ALL_NAN_POINT_NO_PASS'
    return result


def classify_requested_returns(requested,outputs,n,m):
    need(type(requested) is int and 0<=requested<=6 and outputs.tag==b'C'
        and outputs.header.get('class')=='cell'
        and type(outputs.header.get('numel')) is int and outputs.header['numel']==requested
        and len(outputs.parts)==requested,'Exactly every requested original six-output shim return')
    status=outputs.parts[1].text() if requested>=2 else None
    need(status is None or status in STATUS,'Exact pinned inner cvx_sdpt3 status vocabulary, no outer alias')
    blocks={}
    for label,ordinal,count in (('x',0,n),('y',4,m),('z',5,n)):
        if requested>ordinal:blocks[label]=scan_vector(outputs.parts[ordinal],count)
    tolerance=scan_real_numeric(outputs.parts[2],[1,1]) if requested>=3 else None
    iterations=scan_real_numeric(outputs.parts[3],[1,1]) if requested>=4 else None
    iteration_count=None
    if iterations is not None:
        need(iterations['all_finite'],'Actual source info.iter is finite integer metadata, not a repaired return')
        word=bytes.fromhex(iterations['all_original_binary64_words'][0]['original_binary64_little_endian_hex'])
        value=struct.unpack('<d',word)[0]
        need(value>=0 and value==math.trunc(value),'Exact original nonnegative native info.iter')
        iteration_count=int(value)
    if status=='Infeasible' and 'x' in blocks:
        need(blocks['x']['all_NaN'],'Pinned status Infeasible sets x_good=false and all-NaN x')
    if status=='Unbounded':
        for label in ('y','z'):
            if label in blocks:need(blocks[label]['all_NaN'],'Pinned status Unbounded sets y_good=false and all-NaN y/requested z')
    role={'Solved':'native_reported_solved_not_independent_optimality_certificate',
        'Inaccurate/Solved':'native_reported_inaccurate_solved_not_independent_optimality_certificate',
        'Infeasible':'native_infeasibility_terminal_available_dual_or_unavailable_point',
        'Unbounded':'native_unbounded_terminal_direction_not_primal_optimum',
        'Failed':'native_failed_terminal_finite_iterate_or_unavailable_point',
        None:'native_status_not_requested_no_status_certificate'}[status]
    unavailable=[label for label,block in blocks.items() if not block['finite_point_available']]
    unavailable_scalar=bool(tolerance is not None and not tolerance['all_finite'])
    return dict(schema='EXACT_SOURCE_BOUND_INNER_CVX_SDPT3_TERMINAL_RETURN_CLASSIFICATION_V3',
        actual_requested_nargout=requested,actual_original_status=status,source_bound_status_role=role,
        source_bound_status_vocabulary=list(STATUS),status_source=dict(path=CVX_SHIM.as_posix(),sha256=CVX_SHIM_SHA,
            seven_input_six_output_source='solve(At,b,c,nonls,quiet,prec,settings)',
            actual_internal_sqlp_termination_or_transformed_solver_data_captured=False),
        every_actual_requested_point_block=blocks,actual_reported_tolerance_raw=tolerance,
        actual_reported_iteration_metadata_raw=iterations,actual_reported_iteration_count=iteration_count,
        finite_original_reported_tolerance_available=tolerance is not None and tolerance['all_finite'],
        unavailable_point_blocks=unavailable,unavailable_scalar_tolerance=unavailable_scalar,
        any_unavailable_numeric_return=bool(unavailable) or unavailable_scalar,
        all_requested_point_blocks_available=not unavailable,
        all_requested_numeric_returns_available=not unavailable and not unavailable_scalar,
        original_source_return_shape_and_status_boundary_consistent=True,
        unavailable_is_NOT_paper_or_whole_native_failure=True,
        original_backend_terminal_or_unavailable_point_PASS=False,
        all_original_nonfinite_words_retained_without_MP_promotion_or_repair=True)


def split_final_gates(recorder_complete,numeric_dispatch_complete,interval,field_failures,
        precision_failures,rule_failures,unsupported_conic_scopes,terminal_unavailable_callbacks):
    need(all(type(value) is bool for value in (recorder_complete,numeric_dispatch_complete,interval)),
        'Exact independently separated completion/dispatch/source-interval boolean gates')
    counts=(field_failures,precision_failures,rule_failures,unsupported_conic_scopes,terminal_unavailable_callbacks)
    need(all(type(value) is int and value>=0 for value in counts),'Exact complete failure/unavailable counts, not bool aliases')
    finite_math=numeric_dispatch_complete and interval and not any((field_failures,precision_failures,unsupported_conic_scopes))
    source_stops=numeric_dispatch_complete and interval and rule_failures==0
    available=finite_math and source_stops
    return dict(complete_recorder_and_original_control_flow_verified=recorder_complete and interval,
        all_available_finite_math_checks_PASS=finite_math,
        all_original_source_stops_and_constraints_PASS=source_stops,
        all_available_finite_math_and_original_stops_PASS=available,
        all_requested_native_numeric_return_scopes_available=terminal_unavailable_callbacks==0,
        all_captured_fixed_input_source_math_and_original_stops_PASS=available and terminal_unavailable_callbacks==0,
        terminal_unavailable_callback_count=terminal_unavailable_callbacks,
        unavailable_terminal_is_NOT_relabelled_finite_point_PASS=True,
        original_backend_terminal_or_unavailable_point_or_internal_solver_optimality_PASS=False,
        publisher_curve_or_historical_author_geometry_or_full_physics_PASS=False)
