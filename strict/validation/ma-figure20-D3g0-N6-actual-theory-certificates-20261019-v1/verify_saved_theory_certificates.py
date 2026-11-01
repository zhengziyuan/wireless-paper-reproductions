"""Verify only the two frozen original N6 theory certificates.

All numerical functions are unchanged source copies. This host decodes stored
float.hex arrays, restores the documented original typed containers and reads
the supplied certificate once for independent partition/bound/leaf checking.
It never imports an original model/search/optimizer, samples MC, or enumerates
all84 sets. Pruned subtrees are counted without objective evaluation.
"""
from pathlib import Path
from fractions import Fraction
import argparse, hashlib, importlib.util, itertools, json, math, os, pickle, sys, traceback

def enc(v):return json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
def need(v,s):
    if not v:raise ValueError(s)
def load(p,name):
    spec=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m
def digest(raw):return hashlib.sha256(raw).hexdigest()

def decode(value,np):
    if isinstance(value,list):return [decode(v,np) for v in value]
    if not isinstance(value,dict):return value
    if set(value)=={'binary64_hex'}:
        number=float.fromhex(value['binary64_hex']);need(number.hex()==value['binary64_hex'],'Noncanonical scalar hex');return number
    if {'shape','dtype','column_major','real_hex','imag_hex'}<=set(value):
        need(value['column_major'] is True,'Fixture flattening must be Fortran order')
        shape=value['shape'];need(all(type(x) is int and x>=0 for x in shape),'Array shape integers')
        dtype=value['dtype'];need(dtype in ['float64','complex128'],'Frozen dtype')
        size=math.prod(shape);need(len(value['real_hex'])==size,'Real operand count')
        real=np.array([float.fromhex(x) for x in value['real_hex']],dtype=np.float64).reshape(shape,order='F')
        if dtype=='complex128':
            need(value['imag_hex'] is not None and len(value['imag_hex'])==size,'Imag operand count')
            imag=np.array([float.fromhex(x) for x in value['imag_hex']],dtype=np.float64).reshape(shape,order='F')
            array=np.empty(shape,dtype=np.complex128,order='F')
            # Assignment preserves the two saved components, including -0.0.
            array.real=real;array.imag=imag
            need([float(x).hex() for x in array.imag.ravel(order='F')]==value['imag_hex'],'Imag IEEE bits changed')
        else:
            need(value['imag_hex'] is None,'Real fixture must not carry imaginary data');array=real
        need([float(x).hex() for x in array.real.ravel(order='F')]==value['real_hex'],'Real IEEE bits changed')
        need(list(array.shape)==shape and str(array.dtype)==dtype,'Frozen dtype or shape changed')
        return array
    return {key:decode(v,np) for key,v in value.items()}

def main(args):
    root=Path(__file__).resolve().parent;out=args.output_dir.resolve()
    need(out!=root and root not in out.parents,'Output must be outside public packet')
    need(not out.exists(),'Fresh output required; no automatic failure retry');out.mkdir(parents=True)
    report=dict(schema='actual-portable-original-N6-two-theory-certificates-v1',rows=[],errors=[],
        original_model_objective_bound_search_optimizer_MA_FPA_MC_RNG_calls=0,
        pruned_subtree_objective_evaluations=0,complete84_exhaustive_replay=False,
        full_point_MA_final1000_native_figure_reference_PASS=False,
        historical_author_search_criterion_recovered=False)
    expected={};before={};code=1;stage='file_format_or_source'
    try:
        manifest_raw=(root/'manifest.json').read_bytes();manifest=json.loads(manifest_raw)
        expected={key:row['SHA256'] for key,row in manifest['files'].items()}
        expected['manifest.json']=digest(manifest_raw)
        blobs={key:(root/key).read_bytes() for key in expected}
        before={key:digest(raw) for key,raw in blobs.items()};need(before==expected,'Public source/input manifest differs')
        for key,row in manifest['files'].items():need(len(blobs[key])==row['bytes'],'Public byte count differs')
        import numpy as np
        k=load(root/'sources/cofactor_kernel.py','_public_independent_cofactor_kernel')
        b=load(root/'sources/certificate_helpers.py','_public_independent_frame_and_scalar_helpers')
        route=load(root/'sources/partition_N6.py','_public_unchanged_N6_partition')
        generic=load(root/'sources/generic_math.py','_public_unchanged_generic_math');route.generic_math=generic
        fixture=json.loads(blobs['inputs/frozen-binary64-primitives.json'])
        previous=json.loads(blobs['evidence/actual-independent-theory-certificate.json'])
        bridge=json.loads(blobs['evidence/existing-frozen-operand-to-original-typed-equality.json'])
        point=json.loads(blobs['inputs/original-point-binding.json'])
        need(len(fixture['models'])==2 and {x['mode'] for x in fixture['models']}=={'MRT','ZF'},'Exactly two original models')
        need(fixture['source_job_SHA256']==point['original_job_SHA256'],'Frozen fixture not this original job')
        need(previous['actual_reader_exit_code']==0 and previous['source_input_interval_closed'] is True
             and previous['both_actual_original_theory_global_certificates_PASS'] is True,'Original actual independent report not closed0')
        need(bridge['all_checks_pass'] is True and bridge['source_input_interval_closed'] is True,'Historical exact operand bridge unavailable')
        for raw_model in fixture['models']:
            p=decode(raw_model,np);mode=p['mode'];need(type(p['N']) is int and p['N']==6 and type(p['D']) is int and p['D']==3,'N6/D3 scope')
            # Serialized arrays are decoded in their declared F flattening.
            # The original producer grid itself was np.array(list-of-rows), C
            # contiguous; make that documented typed container, copying bits.
            p['grid']=np.array(p['grid'],dtype=np.float64,order='C',copy=True)
            operands=generic.operands(p,mode,np,k);compatible=generic.compatible_matrix(operands,k)
            m=operands['m'];need(m==5,'Original five users')
            if mode=='MRT':
                # Original __init__ explicitly inserts (u,v) by outer u, inner v.
                # Tuple keys and Fraction-valued complex pairs remain unchanged.
                operands['terms']={(u,v):[(Fraction(re.numerator,re.denominator),Fraction(im.numerator,im.denominator))
                    for re,im in operands['terms'][u,v]] for u in range(m) for v in range(m) if u!=v}
            groups=dict(grid=operands['grid'],compatible=compatible,terms=operands['terms'],diagonal=operands['diagonal'])
            if mode=='MRT':groups.update(base=operands['offset'],numerator=operands['desired'],coefficient=operands['coefficient'])
            else:groups.update(base=operands['offset'],eta=operands['eta'])
            actual_typed=route.typed_identity(groups,mode,p['D'])
            binding=json.loads(blobs[f'inputs/{mode}-binding.json']);checkpoint=json.loads(blobs[f'inputs/{mode}-checkpoint.json'])
            need(binding['actual_frozen_model']==actual_typed,'Frozen original typed operands differ (NumPy/pickle runtime or fixture mismatch)')
            old_bridge=next(row for row in bridge['rows'] if row['mode']==mode)
            need(old_bridge['original_constructor_typed_identity']==actual_typed and old_bridge['all_exact_grid_constant_phasor_term_diagonal_and_n_m_values_identical'] is True,'Original typed bridge differs')
            need({key:value for key,value in binding.items() if key not in ['mode','actual_frozen_model']}==point,'Original case/model binding differs')
            stage='independent_saved_certificate'
            row=route.certify_partition(operands,compatible,mode,checkpoint,blobs[f'inputs/{mode}-pruned-prefix-certificates.frames'],k,b)
            stage='file_format_or_source'
            row['actual_original_typed_model']=actual_typed;row['verified_prune_rows_count']=len(row.pop('verified_prune_rows'))
            original=next(row0 for row0 in previous['rows'] if row0['mode']==mode)
            need(row==original,'Public actual certificate readback differs from original independent report')
            report['rows'].append(row)
        need(len(report['rows'])==2,'Both modes required');code=0
        report.update(all_frozen_hex_dtype_shape_Forder_and_signedzero_preserved=True,
                      both_actual_original_typed_models_reproduced=True,
                      all_actual_results_exactly_equal_original_independent_rows=True,
                      NumPy_version=np.__version__)
    except BaseException as error:
        code=2 if stage=='independent_saved_certificate' and isinstance(error,ValueError) else 1
        report['errors'].append(dict(type=type(error).__name__,message=str(error),stage=stage,traceback=traceback.format_exc()))
    finally:
        after={}
        for key in expected:
            try:after[key]=digest((root/key).read_bytes())
            except OSError as error:report['errors'].append(dict(source=key,type=type(error).__name__,message=str(error)))
        report.update(source_input_before=before,source_input_after=after,source_input_interval_closed=bool(expected) and before==after==expected)
        if not report['source_input_interval_closed']:code=1
        report['actual_reader_exit_code']=code
        report['both_actual_saved_theory_global_certificates_PASS']=bool(code==0 and len(report['rows'])==2 and report['source_input_interval_closed'])
        (out/'ACTUAL_PORTABLE_SAVED_N6_THEORY_CERTIFICATES_V1.json').write_bytes(enc(report)+b'\n')
    print(json.dumps(dict(exit_code=code,theory_global_PASS=report['both_actual_saved_theory_global_certificates_PASS'],completed_modes=len(report['rows']),full_point_PASS=False)))
    return code
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output-dir',type=Path,required=True)
    raise SystemExit(main(p.parse_args()))
