"""Verify saved case7 evidence; zero reintegration, optimizer or native calls.

Use --package-dir with optional existing --source-dir/--base-verifier, or all
explicit paths. --expected-manifest-sha256 is always required. The first-case
portable verifier and its six original source modules are referenced, not
copied. Only an existing Python/mpmath dependency is needed. An external
resource guard is the caller's responsibility. One fresh output is<=64KiB.
"""
import sys
sys.dont_write_bytecode=True
import argparse
from datetime import datetime,timezone
import gzip
import hashlib
import io
import json
import math
from pathlib import Path
import platform
import re
import struct
import time
import types

CASE=dict(case_id=7,U=1,K=15,beta=10,N=16,J=16,M=25,geometry_id=6007,
          geometry_event_ordinal=1166118,design_event_ordinal=1166119)
BASE_BYTES=23798
BASE_SHA='dcc061e5a2f7e751b1b6b0471acb488dae52c257c165be1218ae07016c448ae0'
SOURCE_COMMIT='8e1450ab018f09adb8d7f7c80789585a2db1984c'
BASE_PUBLICATION_COMMIT='e6084095123a138e375a47ac5a87660ae79e2bb4'
PROVENANCE=dict(composite_fact_SHA256='082548c0cc4d4174ea2cbc284eba88da7051db0eb02a0d750edeb3f147c64098',
    actual_map_SHA256='b90fa75b71b2981904a1e2b0dd0d5cf330592f322cd6aaa7681a813706eca4e2',
    physical_constraints_fact_SHA256='2cae2c06092171263b25294996629f17ff8d8d89450a10d15efd8ebd356641f0',
    component_stream_SHA256='1f83362f3dbbb7c55ba09005481606f09b35aff9b125be81405c624dde750a7a')
EPOCH_SHA='77be0b924452969c33cdac4149eae1ac9034d197ced71ed999ca9b9b21e55bd0'
NAMES=dict(values='case7-projector-values-only.json.gz',
           components='all256-native-P-components-original-gates.jsonl.gz',manifest='public-case7-manifest.json')
HEX=re.compile(r'[0-9a-f]{64}\Z')
DEADLINE=0


def need(ok,message):
    if not ok:
        raise ValueError(message)


def tick():
    need(time.monotonic()<DEADLINE,'Internal540s saved-evidence deadline')


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode('utf-8')


def parse(raw):
    def pairs(items):
        result={}
        for k,v in items:
            need(k not in result,'Duplicate JSON key');result[k]=v
        return result
    return json.loads(raw,object_pairs_hook=pairs,
        parse_constant=lambda token: (_ for _ in ()).throw(ValueError('Nonfinite JSON')))


def pinned(path,size,digest,limit):
    tick();need(type(size) is int and 0<size<=limit and type(digest) is str and HEX.fullmatch(digest),'Bounded pin')
    with path.open('rb') as f:
        raw=f.read(limit+1)
    need(len(raw)==size and sha(raw)==digest,'Exact source/input bytes: '+path.name)
    return raw


def inflate(raw,limit):
    with gzip.GzipFile(fileobj=io.BytesIO(raw),mode='rb') as f:
        decoded=f.read(limit+1)
    need(len(decoded)<=limit,'Bounded gzip expansion')
    return decoded


def load_base(path):
    raw=pinned(path,BASE_BYTES,BASE_SHA,32768)
    name='_published_firstcase_saved_evidence_base'
    need(name not in sys.modules,'One unchanged base module')
    module=types.ModuleType(name);module.__file__=str(path);module.__package__=''
    sys.modules[name]=module
    exec(compile(raw,str(path),'exec'),module.__dict__)
    need(module.PACKAGE_COMMIT==SOURCE_COMMIT,'Original source snapshot commit')
    return module


def documents(paths,manifest):
    need(manifest['schema']=='CASE7_PORTABLE_SAVED_EVIDENCE_INPUT_MANIFEST_V1'
         and manifest['case']==CASE and manifest['provenance']==PROVENANCE
         and manifest['original_source_snapshot_commit']==SOURCE_COMMIT
         and manifest['base_verifier_SHA256']==BASE_SHA and set(manifest['data'])=={'values','components'},
         'Explicit case7 public input/source manifest')
    data={};commitments={}
    for name in ('values','components'):
        pin=manifest['data'][name]
        need(pin['filename']==NAMES[name],'One fixed data filename')
        raw=pinned(paths[name],pin['bytes'],pin['SHA256'],262144)
        commitments[name]=dict(filename=NAMES[name],bytes=len(raw),SHA256=sha(raw))
        decoded=inflate(raw,2097152 if name=='values' else 1048576)
        if name=='values':
            data[name]=parse(decoded)
        else:
            need(pin['bytes']==184167 and pin['SHA256']==PROVENANCE['component_stream_SHA256'],
                 'Existing original case7 component stream')
            lines=decoded.splitlines();need(len(lines)==256 and all(0<len(x)<=16384 for x in lines),'All256 bounded records')
            data[name]=[parse(x) for x in lines]
    values=data['values']
    need(values['schema']=='SAVED_CASE7_COMPLETE_PROJECTOR_MPWORDS_VALUE_ONLY_V1' and values['case']==CASE
         and values['scope']==dict(K=15,N=16,U=1,complete_matrix_cells=7680,complete_row_precision_pairs=30,
             original_case=7,original_column_major_order=True,precisions=[80,100])
         and values['original_cache_keys_recomputable_from_export'] is False
         and values['original_three_file_cache_API_replay_compatible'] is False
         and values['original_kernel_epoch_SHA256_recorded_provenance_only']==EPOCH_SHA
         and values['provenance']==PROVENANCE and values['new_integrals']==0
         and values['full_physical_or_paper_PASS'] is False,'Complete value-only saved case7 scope')
    records=values['records']
    need(type(records) is list and len(records)==30
         and [(r['row_zero_based'],r['precision']) for r in records]==[(r,p) for r in range(15) for p in (80,100)]
         and all(type(r['row_zero_based']) is type(r['precision']) is int for r in records),'All30 original row identities')
    need(all(type(r[k]) is str and HEX.fullmatch(r[k]) for r in records for k in
             ('original_descriptor_key','original_payload_SHA256','original_run_SHA256'))
         and len({r['original_descriptor_key'] for r in records})==30,'Opaque original record commitments')
    expected=manifest['original_value_commitments']
    need(type(expected) is list and len(expected)==30,'All30 separately pinned original value digests')
    for record,pin in zip(records,expected):
        need(set(pin)=={'row_zero_based','precision','original_payload_SHA256','value_SHA256'}
             and type(pin['row_zero_based']) is type(pin['precision']) is int
             and pin['row_zero_based']==record['row_zero_based'] and pin['precision']==record['precision']
             and pin['original_payload_SHA256']==record['original_payload_SHA256']
             and type(pin['value_SHA256']) is str and HEX.fullmatch(pin['value_SHA256'])
             and sha(canonical(record['value']))==pin['value_SHA256'],'Exported value equals pinned original tuple content')
    array=dict(header=None,real_hex_column_major=[],imag_hex_column_major=[])
    for index,item in enumerate(data['components']):
        need(type(item['component']) is int and item['component']==index
             and item['MATLAB_zero_based_logical_index']==[index%16,index//16],'Every original column-major component')
        header=item['original_native_header'];isreal=header.get('isreal')
        need(type(isreal) is bool and header==dict(**{'class':'double'},size=[16,16],ndims=2,numel=256,
             order='MATLAB_column_major',isreal=isreal),'Original native ABI header')
        if index==0:
            array['header']=header
        need(header==array['header'],'One consistent original native header')
        real=item['native_binary64_real_hex'];imag=item['native_binary64_imag_hex']
        need(type(real) is str and re.fullmatch('[0-9a-f]{16}',real),'Every original real binary64 word')
        need((isreal and imag is None) or (not isreal and type(imag) is str and re.fullmatch('[0-9a-f]{16}',imag)),
             'Preserve original absent or complex imaginary span')
        array['real_hex_column_major'].append(real);array['imag_hex_column_major'].append(imag)
    data['native']=dict(native_composite_P=array)
    return data,commitments


def compare_composites(mp,comparison,matrices,docs):
    """First-case comparison loop, with only ABI-faithful native decode adapted.

    The actual tolerance algorithm remains the unchanged original compare_value.
    All component/replay comparisons and ordering retain the published algorithm.
    """
    native=docs['native']['native_composite_P']
    field_failed=cross_failed=exact_failed=record_failed=0
    checked=cross_checked=0;maximum_ratio=None;worst=None;proof=hashlib.sha256()
    for column in range(16):
        tick()
        for row in range(16):
            index=row+16*column
            real=struct.unpack('<d',bytes.fromhex(native['real_hex_column_major'][index]))[0]
            if native['header']['isreal']:
                need(math.isfinite(real),'Finite original real native field');actual=real
            else:
                imag=struct.unpack('<d',bytes.fromhex(native['imag_hex_column_major'][index]))[0]
                need(math.isfinite(real) and math.isfinite(imag),'Finite original complex native field')
                actual=complex(real,imag)
            result,ratio=comparison.compare_value(mp,actual,matrices[80][row,column],matrices[100][row,column])
            historical=docs['components'][index]
            if not result['original_field_pass']:
                field_failed|=1<<index
            for component,record in enumerate(result['both_real_imag_crossprecision']):
                if not record['pass_']:
                    cross_failed|=1<<(2*index+component)
                cross_checked+=1
            tuple_match=all(result[key][word]==historical[key][word]
                for key in ('native','reference_MP80','reference_MP100')
                for word in ('exact_real_mpf','exact_imag_mpf'))
            if not tuple_match:
                exact_failed|=1<<index
            if any(value!=historical[key] for key,value in result.items()):
                record_failed|=1<<index
            proof.update(canonical(dict(component=index,comparison=result))+b'\n')
            if mp.isfinite(ratio) and (maximum_ratio is None or ratio>maximum_ratio):
                maximum_ratio,worst=ratio,index
            checked+=1
    need(checked==256 and cross_checked==512,'Every native and crossprecision gate')
    return (dict(native_complex_checks=checked,crossprecision_real_imag_checks=cross_checked,
        native_all_pass=field_failed==0,crossprecision_all_pass=cross_failed==0,
        native_failure_count=field_failed.bit_count(),crossprecision_failure_count=cross_failed.bit_count(),
        native_failure_bitmap_hex=format(field_failed,'064x'),crossprecision_failure_bitmap_hex=format(cross_failed,'0128x'),
        native_bit_order='bit index; index=row+16*column',crossprecision_bit_order='bit2*index+component;real0,imag1',
        maximum_native_scaled_error=None if maximum_ratio is None else mp.nstr(maximum_ratio,105),worst_native_index=worst,
        ordered_all256_current_comparison_SHA256=proof.hexdigest(),
        gate_function='unchanged full_coordinate_comparison_sourceonly_v4.compare_value',
        field_absolute=comparison.FIELD_ABSOLUTE,field_relative=comparison.FIELD_RELATIVE,
        crossprecision_epsilon=comparison.CROSS_PRECISION),
        dict(component_records_checked=checked,exact_native_and_reference_MP_tuples_match=exact_failed==0,
             exact_tuple_mismatch_count=exact_failed.bit_count(),exact_tuple_mismatch_bitmap_hex=format(exact_failed,'064x'),
             entire_original_comparison_records_match=record_failed==0,comparison_record_mismatch_count=record_failed.bit_count(),
             comparison_record_mismatch_bitmap_hex=format(record_failed,'064x'),byte_equivalence_of_historical_runtime_proven=False))


def execute(a,paths,manifest,manifest_size,report):
    report['stage']='bounded_source_and_input_validation'
    base=load_base(a.base_verifier)
    docs,commitments=documents(paths,manifest)
    geometry,comparison,sources=base.load_sources(a.source_dir)
    import mpmath
    report['provenance']=dict(original_source_snapshot_commit=SOURCE_COMMIT,
        base_verifier_publication_commit=BASE_PUBLICATION_COMMIT,base_verifier_SHA256=BASE_SHA,
        inputs=commitments,original_source_bytes=sources,
        current_runtime=dict(python=sys.version,implementation=platform.python_implementation(),mpmath_version=mpmath.__version__,
                             mpmath_module_path=str(Path(mpmath.__file__).resolve())),
        historical_runtime_byte_equivalence_proven=False,private_cache_admission_replayed=False,
        original_NHU_or_full_typed_input_independently_reread=False,
        all30_exported_value_digests_match_pinned_originals=True,
        prior_private_receipt_commitments=PROVENANCE,original_kernel_epoch_SHA256_provenance_only=EPOCH_SHA)
    contexts={p:mpmath.mp.clone() for p in (80,100)}
    for precision,mp in contexts.items():
        mp.dps=precision
    pairs={80:[],100:[]}
    report['stage']='decode_all30_exact_saved_matrices'
    for record in docs['values']['records']:
        tick();p=record['precision'];pairs[p].append(base.decode_matrix(contexts[p],record['value']))
    report['stage']='all7680_row_checks'
    report['scientific_checks']['saved_rows']=base.row_checks(contexts[100],pairs)
    tick();report['stage']='unchanged_full_moment_assembly'
    matrices={p:geometry.complete_projector_square(contexts[p],pairs[p]) for p in (80,100)}
    report['scientific_checks']['aggregation']=dict(precisions=[80,100],row_terms_per_precision=15,
        ordered_cross_products_per_precision=210,integration_calls=0,optimizer_calls=0,
        function='unchanged independent_geometry_kernels_sourceonly_v1.complete_projector_square',
        formula='I-sum(M_k)+sum_{k!=j}M_k*M_j, followed by original Hermitian symmetrization')
    report['stage']='original_native_and_crossprecision_gates'
    gates,replay=compare_composites(contexts[100],comparison,matrices,docs)
    report['scientific_checks']['native_composite']=gates;report['saved_reference_replay']=replay
    report['stage']='saved_source_input_interval_closure'
    pinned(a.base_verifier,BASE_BYTES,BASE_SHA,32768)
    for filename,size,digest in base.SOURCES:
        pinned(a.source_dir/filename,size,digest,65536)
    pinned(paths['manifest'],manifest_size,a.expected_manifest_sha256,16384)
    for name in ('values','components'):
        pin=manifest['data'][name];pinned(paths[name],pin['bytes'],pin['SHA256'],262144)
    report['provenance']['source_and_input_interval_unchanged']=True
    numerical=report['scientific_checks']['saved_rows']['all_components_pass'] and gates['native_all_pass'] and gates['crossprecision_all_pass']
    exact=replay['exact_native_and_reference_MP_tuples_match'] and replay['entire_original_comparison_records_match']
    report['scientific_checks']['all_scoped_numerical_gates_pass']=numerical
    report.update(status='SAVED_EVIDENCE_VERIFIED' if numerical and exact else 'SAVED_EVIDENCE_CHECK_FAILED',
                  saved_evidence_verification_pass=numerical and exact,stage='completed')


def arguments():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--package-dir',type=Path);p.add_argument('--source-dir',type=Path);p.add_argument('--base-verifier',type=Path)
    for name in NAMES:
        p.add_argument('--'+name,type=Path)
    p.add_argument('--expected-manifest-sha256',required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args()
    if a.package_dir is not None:
        need(not any(getattr(a,n) is not None for n in NAMES),'No package-dir with explicit data paths')
        paths={name:a.package_dir/filename for name,filename in NAMES.items()}
        sibling=a.package_dir.parent/'H18-first-native-case-all15-20261029'
        a.source_dir=a.source_dir or sibling/'sources'
        a.base_verifier=a.base_verifier or sibling/'verify_portable_saved_first_case.py'
    else:
        need(a.source_dir is not None and a.base_verifier is not None and all(getattr(a,n) is not None for n in NAMES),
             'Supply package-dir or all explicit existing data/source/base paths')
        paths={name:getattr(a,name) for name in NAMES}
    paths={name:path.resolve(strict=True) for name,path in paths.items()}
    a.source_dir=a.source_dir.resolve(strict=True);a.base_verifier=a.base_verifier.resolve(strict=True)
    a.output=a.output.resolve();need(a.output.parent.is_dir() and not a.output.exists(),'One fresh report in existing directory')
    need(a.output not in paths.values() and a.output!=a.base_verifier and a.output!=Path(__file__).resolve(),
         'No output overwrites input or source')
    return a,paths


def main():
    global DEADLINE
    a,paths=arguments();DEADLINE=time.monotonic()+540
    need(not sys.flags.optimize and sys.dont_write_bytecode,'No optimized asserts or bytecode output')
    with paths['manifest'].open('rb') as f:
        raw=f.read(16385)
    need(0<len(raw)<=16384 and sha(raw)==a.expected_manifest_sha256,'Explicit bounded public manifest SHA256')
    manifest=parse(raw);manifest_size=len(raw)
    report=dict(schema='PORTABLE_CASE7_SAVED_EVIDENCE_VERIFICATION_V1',UTC=datetime.now(timezone.utc).isoformat(),
        status='RUNNING',stage='starting',case=CASE,verifier_SHA256=sha(Path(__file__).read_bytes()),
        manifest_SHA256=a.expected_manifest_sha256,scientific_checks={},saved_evidence_verification_pass=False,
        new_integrals=0,full_physical_or_paper_PASS=False,
        limitations=['One case7 saved-value replay, not all18 cases or complete published scenarios/figures.',
            'No rigorous quadrature error certificate, optimizer feasibility, convergence or original-paper reference gate.',
            'P is the recorded independent-channel complete moment, not an established joint-nullspace orthogonal projector.',
            'Prior33 Hermitian/trace and66 PSD results are private receipt provenance, not rerun by this verifier.',
            'Original NHU/full typed-input reproduction, private cache admission and historical runtime byte equivalence are absent.'])
    with a.output.open('xb') as f:
        f.write(canonical(report)+b'\n');f.flush()
        try:
            execute(a,paths,manifest,manifest_size,report)
        except BaseException as exc:
            report.update(status='ERROR_NOT_PASS',saved_evidence_verification_pass=False,
                          error=dict(type=type(exc).__name__,message=str(exc)[:300]))
        raw=canonical(report)+b'\n'
        if len(raw)>65536:
            rows=report.get('scientific_checks',{}).get('saved_rows',{}).get('rows',[])
            report=dict(schema=report['schema'],status='ERROR_NOT_PASS',case=CASE,saved_evidence_verification_pass=False,
                error='Full report exceeded64KiB; bounded failure identities retained',full_report_SHA256=sha(raw),
                row_failures=[{k:r[k] for k in ('row_zero_based','failure_count','failure_bitmap_hex')} for r in rows],
                native_composite=report.get('scientific_checks',{}).get('native_composite'),
                saved_reference_replay=report.get('saved_reference_replay'),full_physical_or_paper_PASS=False)
            raw=canonical(report)+b'\n'
        need(len(raw)<=65536,'Bounded final error report')
        f.seek(0);f.write(raw);f.truncate();f.flush()
    print(json.dumps(dict(status=report['status'],pass_=report['saved_evidence_verification_pass']),separators=(',',':')))
    return 0 if report['saved_evidence_verification_pass'] else 1


if __name__=='__main__':
    raise SystemExit(main())
