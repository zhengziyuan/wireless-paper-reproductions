"""Portable saved-only native D3/g1 readback; no MATLAB, search, RNG or pickle."""
from pathlib import Path
import argparse,base64,gzip,hashlib,importlib.util,json,struct
import numpy as np

DEPENDENCY='ma-figure19-statistical-D3-g1-20261019-v1'
SHARED_SHA='09b8c681ad40ffb0021c49746f656ba1fca65cc080845e06a67e0912c6374182'
ORACLE_SHA='9db2b29a4d2235122feb3438c2a47ffe8fdebfce738b6bf3779c4d0a7cc2b81d'
SAMPLE_ATOL=1e-7
MEAN_POWER_ATOL=DESIGN_ATOL=1e-9

def sha(raw):return hashlib.sha256(raw).hexdigest()
def need(value,message):
    if not value:raise ValueError(message)
def field_bytes(field):
    return base64.b64decode(field['real_F_bytes_base64']),base64.b64decode(field.get('imag_F_bytes_base64',''))
def decode_field(field):
    if field['MATLAB_class']=='char':return field['value']
    real,imag=field_bytes(field);shape=tuple(field['MATLAB_shape'])
    dtype=np.uint8 if field['MATLAB_class']=='logical' else np.dtype('<f8')
    a=np.frombuffer(real,dtype=dtype).reshape(shape,order='F').copy()
    if field['MATLAB_class']=='logical':return a.astype(bool)
    if field['complex']:
        z=np.empty(shape,dtype='<c16');z.real=a;z.imag=np.frombuffer(imag,dtype='<f8').reshape(shape,order='F');return z
    return a
def validate_primitive_payload(primitive):
    for name in primitive['field_order']:
        f=primitive['fields'][name]
        if f['MATLAB_class']=='char':
            need(f['MATLAB_shape']==[1,len(f['value'])],'Character value/shape differs');continue
        real,imag=field_bytes(f);count=int(np.prod(f['MATLAB_shape']))
        need(len(real)==count*(1 if f['MATLAB_class']=='logical' else 8),'Numeric real payload shape differs')
        need(sha(real)==f['real_F_bytes_SHA256'],'Numeric real payload bytes differ')
        if f['complex']:
            need(len(imag)==count*8 and sha(imag)==f['imag_F_bytes_SHA256'],'Complex imaginary payload differs')
        a=decode_field(f)
        rb=np.asarray(a,dtype=np.uint8).tobytes(order='F') if f['MATLAB_class']=='logical' else np.asarray(a.real,dtype='<f8').tobytes(order='F')
        need(list(a.shape)==f['MATLAB_shape'] and rb==real,'Decoded numeric real bits/shape differ')
        if f['complex']:need(np.asarray(a.imag,dtype='<f8').tobytes(order='F')==imag,'Decoded imaginary bits differ')
    return True

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--python-capsule',type=Path)
    parser.add_argument('--output-dir',type=Path,required=True)
    parser.add_argument('--execute',action='store_true',required=True)
    a=parser.parse_args();here=Path(__file__).resolve().parent
    dependency=(a.python_capsule or here.parent/DEPENDENCY).resolve()
    need(not a.output_dir.exists(),'Fresh saved-readback output required')
    manifest=json.loads((here/'MANIFEST.json').read_bytes())
    before={}
    def read(path):
        path=Path(path);raw=path.read_bytes();before[str(path)]={'SHA256':sha(raw),'bytes':len(raw)};return raw
    for relative,pin in manifest['files'].items():
        raw=read(here/relative);need(sha(raw)==pin['SHA256'] and len(raw)==pin['bytes'],'Capsule bytes differ: '+relative)
    shared_raw=read(dependency/'selected-case-and-evidence.json.gz');need(sha(shared_raw)==SHARED_SHA,'Published shared-input fixture differs')
    shared=json.loads(gzip.decompress(shared_raw))
    jobraw=shared['original_input_UTF8']['selected_job'].encode('utf-8')
    cfgraw=shared['original_input_UTF8']['execution_configuration'].encode('utf-8')
    job=json.loads(jobraw);cfg=json.loads(cfgraw)
    data=json.loads(gzip.decompress(read(here/'native-results-and-typed-basis.json.gz')))
    need(sha(jobraw)==data['shared_original_job_SHA256'] and sha(cfgraw)==data['shared_execution_configuration_SHA256'],'Original shared geometry/population/config binding differs')
    oracle_path=dependency/'sources/independent_saved_physics.py'
    need(sha(read(oracle_path))==ORACLE_SHA,'Existing independent physical functions differ')
    spec=importlib.util.spec_from_file_location('_published_saved_physics',oracle_path)
    oracle=importlib.util.module_from_spec(spec);spec.loader.exec_module(oracle)
    _,_,_,draws,noise,channel,design=oracle.geometry_functions(job,cfg)
    need(draws.shape==(1000,4,3),'Complete original1000 population required')
    py=shared['records']['actual_result']['metrics']['brute_force'];rows={}
    for mode,item in data['modes'].items():
        need(validate_primitive_payload(item['native_typed_primitive']),'Actual native numeric payload differs')
        primitive={k:decode_field(v) for k,v in item['native_typed_primitive']['fields'].items()}
        t=np.asarray(item['search']['winner_positions'],dtype=np.float64)
        indices=item['search']['winner_indices_1based'];grid=primitive['grid'];compat=primitive['actual_exact_squared_spacing_compatibility']
        need(np.array_equal(t,grid[np.asarray(indices)-1]) and all(compat[i-1,j-1] for i in indices for j in indices if i!=j),'Native typed grid/winner spacing differs')
        rates,powers=oracle.ma_rates(channel(t),job['power'],noise,mode.lower())
        native=item['original1000'];sr=np.asarray(native['sample_sum_rates']);sp=np.asarray(native['powers'])
        need(rates.shape==powers.shape==sr.shape==sp.shape==(1000,),'All1000 saved outputs required')
        dx=np.linalg.norm(t[:,None]-t[None,:],axis=2)+np.eye(4)*1e9
        feasible=bool(np.isfinite(t).all() and dx.min()>=.5-cfg['verification_tolerance'] and np.all(t>=np.asarray(job['region_lower'])-cfg['verification_tolerance']) and np.all(t<=np.asarray(job['region_upper'])+cfg['verification_tolerance']))
        finite=all(np.isfinite(x).all() for x in (rates,powers,sr,sp))
        se=float(np.max(abs(rates-sr)));pe=float(np.max(abs(powers-sp)));me=abs(float(rates.mean())-native['mean_sum_rate'])
        de=abs(design(t,mode.lower())-item['search']['display_statistical_value'])
        pyr=py[mode];psr=np.asarray(pyr['MC']['sample_sum_rates']);psp=np.asarray(pyr['MC']['powers'])
        positions_equal=t.tobytes(order='F')==np.asarray(pyr['positions'],dtype=np.float64).tobytes(order='F')
        dualrate=float(np.max(abs(sr-psr)));dualpower=float(np.max(abs(sp-psp)));dualmean=abs(native['mean_sum_rate']-pyr['MC']['mean_sum_rate'])
        rows[mode]=dict(native_maximum_sample_error=se,native_maximum_power_error=pe,native_mean_error=me,fixed_point_statistical_error=de,
            typed_numeric_payload_shape_and_bytes_pass=True,original_native_typed_digest_recomputed=False,same_winner_indices=[i-1 for i in indices]==pyr['canonical_indices'],winner_positions_bits_equal=positions_equal,
            dual_maximum_sample_error=dualrate,dual_maximum_power_error=dualpower,dual_mean_error=dualmean,
            passed=bool(finite and feasible and se<=SAMPLE_ATOL and pe<=MEAN_POWER_ATOL and me<=MEAN_POWER_ATOL and de<=DESIGN_ATOL and powers.max()<=job['power']+MEAN_POWER_ATOL and positions_equal and [i-1 for i in indices]==pyr['canonical_indices'] and dualrate<=SAMPLE_ATOL and dualpower<=MEAN_POWER_ATOL and dualmean<=MEAN_POWER_ATOL))
    after={p:{'SHA256':sha(Path(p).read_bytes()),'bytes':Path(p).stat().st_size} for p in before}
    a.output_dir.mkdir(parents=True)
    result=dict(complete=True,rows=rows,source_input_interval_unchanged=before==after,all_scoped_saved_checks_pass=before==after and all(x['passed'] for x in rows.values()),
        precision='Existing independent binary64 physical functions; not MP or interval',new_search_optimizer_RNG_or_samples=0,
        full_search_trajectory_or_exact_cross_language_model_identity=False,independent_complete_prune_certificate_replayed=False,
        full_axes_original_reference_or_paper_PASS=False,source_before=before,source_after=after)
    (a.output_dir/'saved-native-physical-dual-readback.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'all_scoped_saved_checks_pass':result['all_scoped_saved_checks_pass'],'rows':rows}))
    return 0 if result['all_scoped_saved_checks_pass'] else 2

if __name__=='__main__':raise SystemExit(main())
