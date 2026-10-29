"""SOURCE ONLY full component comparison and bounded complete proof streams.

No numerical imports. Caller supplies the independently bound MP100 context.
Every native scalar/complex coordinate, both reference precisions and actual
error/tolerance are written (streaming compressed JSON lines). No norm-only
substitution, failure sampling, first-nine filter, event cap or tolerance fit.
The whole original complex field error uses complex magnitude exactly as the
frozen V6 Checker.close; crossprecision separately checks real and imaginary.
"""
import gzip
import hashlib
import json
import math
from pathlib import Path
import struct
import literal_typed_MP_adapter_sourceonly_v1 as a
import exact_CVX_SDPT3_terminal_contract_stdlib_v3 as terminal
from bounded_closed_typed_reader_sourceonly_v1 import need

FIELD_ABSOLUTE='0.000000001'
FIELD_RELATIVE='0.0000000001'
CROSS_PRECISION='1e-40'


def index_coordinates(index,shape):
    need(type(index) is int and 0<=index<math.prod(shape),'Every original logical full component index')
    result=[]
    for dim in shape:result.append(index%dim);index//=dim
    return result


def exact_promoted_record(mp,value):
    if hasattr(value,'_mpc_'):
        return mp.make_mpc(value._mpc_)
    if hasattr(value,'_mpf_'):return mp.make_mpf(value._mpf_)
    return a.exact_number(mp,value)


def point_text(mp,value):
    # Human-readable 105 digits plus exact canonical MP raw tuples in every
    # row. Decimal text is output only; no reference is re-imported from text.
    return dict(real=mp.nstr(mp.re(value),105),imag=mp.nstr(mp.im(value),105),
                exact_real_mpf=list(mp.re(value)._mpf_),exact_imag_mpf=list(mp.im(value)._mpf_))


def compare_value(mp,native,p80,p100,residual=False):
    ref80=exact_promoted_record(mp,p80);ref100=exact_promoted_record(mp,p100)
    if residual:
        # Full Gram residuals are derived from every literal native factor
        # and fixed-input moment, not a forged native zero record. Both
        # precisions retain the complete residual; original field tolerance
        # is unchanged (reference zero => absolute 1e-9, no fitted scale).
        observed=ref100;reference=mp.mpf(0)
    else:observed=a.exact_number(mp,native);reference=ref100
    absolute=mp.mpf(FIELD_ABSOLUTE);relative=mp.mpf(FIELD_RELATIVE)
    tolerance=absolute+relative*max(abs(observed),abs(reference));error=abs(observed-reference)
    ratio=error/tolerance
    cross=[]
    for aa,bb in ((mp.re(ref80),mp.re(ref100)),(mp.im(ref80),mp.im(ref100))):
        limit=mp.mpf(CROSS_PRECISION)+mp.mpf(CROSS_PRECISION)*max(abs(aa),abs(bb));delta=abs(aa-bb)
        cross.append(dict(error=mp.nstr(delta,105),tolerance=mp.nstr(limit,105),pass_=bool(mp.isfinite(delta) and delta<=limit)))
    return dict(native=point_text(mp,observed),reference_MP80=point_text(mp,ref80),reference_MP100=point_text(mp,ref100),
                error=mp.nstr(error,105),original_tolerance=mp.nstr(tolerance,105),scaled_error=mp.nstr(ratio,105),
                original_field_pass=bool(mp.isfinite(error) and error<=tolerance),
                both_real_imag_crossprecision=cross,original_MP80_MP100_pass=all(v['pass_'] for v in cross),
                derived_full_factor_Gram_residual_not_native_zero_record=residual),ratio


class CompleteProofStreams:
    """Caller-owned NEW outputs; science loss/error leaves partial evidence."""
    def __init__(self,output,mp):
        self.output=Path(output);need(not self.output.exists(),'Strict new independent output, no resume/share/overwrite')
        self.output.mkdir();self.mp=mp;self.closed=False
        self.raw=(self.output/'all-original-components.jsonl.gz.partial').open('xb')
        self.components=gzip.GzipFile(filename='',mode='wb',fileobj=self.raw,mtime=0)
        self.events=(self.output/'all-original-event-checks.jsonl.partial').open('x',encoding='utf-8',newline='\n')
        self.component_sha=hashlib.sha256();self.event_sha=hashlib.sha256()
        self.coordinates=0;self.quantities=0;self.events_count=0;self.field_failures=0;self.precision_failures=0
        self.rule_failures=0;self.unavailable_conic_scopes=0;self.maximum_scaled_error=mp.mpf(0)
        self.scientific_exceptions=0
        self.terminal_status_class_counts={};self.terminal_unavailable_callbacks=0
        self.terminal_unavailable_point_callbacks=0;self.terminal_unavailable_tolerance_callbacks=0
        self.terminal_nonfinite_return_coordinates=0;self.terminal_unavailable_block_counts={}

    def component(self,row):
        raw=(json.dumps(row,separators=(',',':'),ensure_ascii=False,allow_nan=False)+'\n').encode('utf-8')
        self.components.write(raw);self.component_sha.update(raw)

    def event(self,row):
        raw=(json.dumps(row,separators=(',',':'),ensure_ascii=False,allow_nan=False)+'\n').encode('utf-8')
        self.events.write(raw.decode('utf-8'));self.event_sha.update(raw);self.events_count+=1

    def check_event(self,r,p80,p100):
        need(set(p80['quantities'])==set(p100['quantities']) and set(p80['rules'])==set(p100['rules']),
             'Both independently executed precisions cover exactly every quantity and gate')
        quantities=[];mp=self.mp
        for label in p80['quantities']:
            packet80=p80['quantities'][label];packet100=p100['quantities'][label]
            node,ref80=packet80[:2];node100,ref100=packet100[:2]
            residual=node is None;need((node100 is None)==residual and len(ref80)==len(ref100),'Identical whole quantity ABI both precisions')
            if not residual:need(node100 is node,'Both independent references point to the same actual immutable typed input node')
            native=[None]*len(ref80) if residual else a.flat_binary64(node)
            derived=None
            if residual:
                need(len(packet80)==len(packet100)==3 and packet80[2]['shape']==packet100[2]['shape']
                    and a.bit_identity(packet80[2]['literal_factor'],packet100[2]['literal_factor']),
                    'Full derived Gram logical16x16 and every actual native factor bit both precisions')
                provenance=packet80[2];factor=provenance['literal_factor'];shape=provenance['shape']
                derived=dict(actual_native_factor_header=factor.header,full_derived_logical_size=shape,original_math=provenance['math'],
                    actual_native_factor_components=[dict(global_offset=part.offset,bytes=part.length,SHA256=part.digest()) for part in factor.parts])
            else:shape=node.header['size']
            count=0;field_failed=0;precision_failed=0;maximum=mp.mpf(0);worst=None;digest=hashlib.sha256()
            for index,(observed,reference80,reference100) in enumerate(zip(native,ref80,ref100)):
                row,ratio=compare_value(mp,observed,reference80,reference100,residual)
                row.update(actual_event=r['ordinal'],action=r['action'],context=r['context'],quantity=label,
                           component=index,original_MATLAB_logical_index=index_coordinates(index,shape),size=shape)
                if residual:row['full_derived_Gram_input_provenance']=derived
                if not residual:
                    value=observed if type(observed) is complex else complex(observed,0)
                    row['native_binary64_real_hex']=struct.pack('<d',value.real).hex()
                    row['native_binary64_imag_hex']=struct.pack('<d',value.imag).hex() if not node.header['isreal'] else None
                self.component(row);digest.update((str(row['reference_MP80']['exact_real_mpf'])+str(row['reference_MP80']['exact_imag_mpf'])
                    +str(row['reference_MP100']['exact_real_mpf'])+str(row['reference_MP100']['exact_imag_mpf'])).encode('ascii'))
                count+=1;field_failed+=not row['original_field_pass'];precision_failed+=not row['original_MP80_MP100_pass']
                if ratio>maximum:maximum=ratio;worst=index
            need(count==len(ref80)==len(ref100) and (residual or count==node.header['numel']),
                 'Every component checked/written, no zip truncation or norm-only comparison')
            self.coordinates+=count;self.quantities+=1;self.field_failures+=field_failed;self.precision_failures+=precision_failed
            self.maximum_scaled_error=max(self.maximum_scaled_error,maximum)
            quantities.append(dict(label=label,full_component_count=count,reference_bothprecision_point_commitment=digest.hexdigest(),
                all_field_failure_count=field_failed,all_crossprecision_failure_count=precision_failed,
                maximum_scaled_error=str(maximum),worst_original_component=worst,
                native_raw_spans=None if residual else dict(header=node.header,
                    components=[dict(global_offset=part.offset,bytes=part.length,SHA256=part.digest()) for part in node.parts])))
        rules=[]
        for label in p80['rules']:
            passed=p80['rules'][label] is True and p100['rules'][label] is True
            self.rule_failures+=not passed;rules.append(dict(label=label,MP80=p80['rules'][label],MP100=p100['rules'][label],both_pass=passed))
        self.event(dict(actual_event=r['ordinal'],action=r['action'],context=r['context'],all_quantities=quantities,
            every_original_rule=rules,qualifications=sorted(set(p80['qualifications']+p100['qualifications'])),
            complete_literal_source_causal_metadata_MP80=p80['complete_literal_source_causal_metadata'],
            complete_literal_source_causal_metadata_MP100=p100['complete_literal_source_causal_metadata']))

    def conic(self,r,rows80,rows100):
        """All returned conic prefix data, with no invented convergence gate."""
        def encode(mp,value):
            if type(value) is dict:return {key:encode(mp,item) for key,item in value.items()}
            if type(value) in (list,tuple):return [encode(mp,item) for item in value]
            if type(value) in (str,int,bool) or value is None:return value
            return point_text(mp,exact_promoted_record(mp,value))
        def full_cross(left,right,path):
            if type(left) is dict:
                need(type(right) is dict and set(left)==set(right),'Both complete conic prefix field sets')
                for key in left:full_cross(left[key],right[key],path+[key])
            elif type(left) in (tuple,list):
                need(type(right) in (tuple,list) and len(left)==len(right),'Every conic prefix coordinate, no zip shrink')
                for index,(aa,bb) in enumerate(zip(left,right)):full_cross(aa,bb,path+[index])
            elif type(left) in (str,int,bool) or left is None:
                need(type(left) is type(right) and left==right,'Exact same conic metadata both precisions')
            else:
                aa=exact_promoted_record(self.mp,left);bb=exact_promoted_record(self.mp,right);checks=[]
                for one,two in ((self.mp.re(aa),self.mp.re(bb)),(self.mp.im(aa),self.mp.im(bb))):
                    error=abs(one-two);limit=self.mp.mpf(CROSS_PRECISION)*(1+max(abs(one),abs(two)))
                    checks.append(dict(error=str(error),original_tolerance=str(limit),pass_=bool(self.mp.isfinite(error) and error<=limit)))
                self.coordinates+=1;self.precision_failures+=not all(row['pass_'] for row in checks)
                self.component(dict(actual_event=r['ordinal'],action=r['action'],context=r['context'],
                    full_conic_coordinate_path=path,reference_MP80=point_text(self.mp,aa),reference_MP100=point_text(self.mp,bb),
                    both_real_imag_original_MP80_MP100_checks=checks,conic_observation_has_no_new_threshold=True))
        full_cross(rows80,rows100,[])
        classification=rows80['exact_native_terminal_classification']
        status=classification['actual_original_status'] or 'status_not_requested'
        self.terminal_status_class_counts[status]=self.terminal_status_class_counts.get(status,0)+1
        self.terminal_unavailable_callbacks+=int(classification['any_unavailable_numeric_return'])
        self.terminal_unavailable_point_callbacks+=int(bool(classification['unavailable_point_blocks']))
        self.terminal_unavailable_tolerance_callbacks+=int(classification['unavailable_scalar_tolerance'])
        for label,block in classification['every_actual_requested_point_block'].items():
            self.terminal_nonfinite_return_coordinates+=block['nonfinite_component_count']
            if not block['finite_point_available']:
                self.terminal_unavailable_block_counts[label]=self.terminal_unavailable_block_counts.get(label,0)+1
        reported=classification['actual_reported_tolerance_raw']
        if reported is not None:self.terminal_nonfinite_return_coordinates+=reported['nonfinite_component_count']
        self.component(dict(actual_event=r['ordinal'],action=r['action'],context=r['context'],
            full_original_backend_prefix_MP80=encode(self.mp,rows80),full_original_backend_prefix_MP100=encode(self.mp,rows100),
            standard_form_internal_optimality_or_trajectory_PASS=False))
        if rows80.get('unsupported_original_cones') or rows100.get('unsupported_original_cones'):
            self.unavailable_conic_scopes+=1

    def exception(self,r,error):
        self.scientific_exceptions+=1;self.event(dict(actual_event=r['ordinal'],action=r['action'],context=r['context'],
            independent_scientific_exception=error,all_original_recorded_scope_retained_not_upgraded=True))

    def seal(self,trajectory,interval):
        self.components.close();self.raw.close();self.events.close()
        self.raw_path=self.output/'all-original-components.jsonl.gz';self.event_path=self.output/'all-original-event-checks.jsonl'
        (self.output/'all-original-components.jsonl.gz.partial').rename(self.raw_path)
        (self.output/'all-original-event-checks.jsonl.partial').rename(self.event_path);self.closed=True
        recorder_complete=self.events_count==trajectory['actual_event_count']
        complete=recorder_complete and self.scientific_exceptions==0
        separated_gates=terminal.split_final_gates(recorder_complete,complete,interval,self.field_failures,
            self.precision_failures,self.rule_failures,self.unavailable_conic_scopes,self.terminal_unavailable_callbacks)
        return dict(complete_original_typed_event_math_dispatch=complete,actual_all_component_coordinates=self.coordinates,
            actual_all_compared_quantities=self.quantities,actual_event_reports=self.events_count,
            all_field_failures=self.field_failures,all_original_MP80_MP100_delta_failures=self.precision_failures,
            all_original_rule_failures=self.rule_failures,all_scientific_exceptions=self.scientific_exceptions,
            unsupported_actual_conic_prefixes=self.unavailable_conic_scopes,maximum_original_scaled_field_error=str(self.maximum_scaled_error),
            component_uncompressed_stream_SHA256=self.component_sha.hexdigest(),event_uncompressed_stream_SHA256=self.event_sha.hexdigest(),
            exact_separated_terminal_and_available_math_gates=separated_gates,
            complete_recorder_and_original_control_flow_verified=separated_gates['complete_recorder_and_original_control_flow_verified'],
            all_available_finite_math_checks_PASS=separated_gates['all_available_finite_math_checks_PASS'],
            all_original_source_stops_and_constraints_PASS=separated_gates['all_original_source_stops_and_constraints_PASS'],
            all_available_finite_math_and_original_stops_PASS=separated_gates['all_available_finite_math_and_original_stops_PASS'],
            all_captured_fixed_input_source_math_and_original_stops_PASS=separated_gates['all_captured_fixed_input_source_math_and_original_stops_PASS'],
            all_actual_native_terminal_status_class_counts=self.terminal_status_class_counts,
            terminal_unavailable_callback_count=self.terminal_unavailable_callbacks,
            terminal_unavailable_point_callback_count=self.terminal_unavailable_point_callbacks,
            terminal_unavailable_tolerance_callback_count=self.terminal_unavailable_tolerance_callbacks,
            all_terminal_nonfinite_return_coordinate_count=self.terminal_nonfinite_return_coordinates,
            all_terminal_unavailable_point_block_counts=self.terminal_unavailable_block_counts,
            rigorous_forward_library_or_quadrature_or_internal_solver_certificate=False,
            exact_random_base_draw_crosslanguage_parity_verified=False,original_printed_algorithm_reproduction_PASS=False,
            publisher_curve_or_historical_author_geometry_or_full_physics_PASS=False,
            all_components_and_bothprecision_point_values_written_not_normonly_or_failed_subset=True)

    def retain_partial(self):
        for handle in (getattr(self,'components',None),getattr(self,'raw',None),getattr(self,'events',None)):
            if handle is not None:
                try:handle.close()
                except BaseException:pass
