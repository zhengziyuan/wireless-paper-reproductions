"""Relevant-input bridge for original saved MA/FPA components; no optimization.

This is an explicit component dependency bridge, not whole-case tape adoption.
Only fixed1000 known inputs and source-bound original returns are eligible.
"""
from pathlib import Path
import copy,hashlib,json,math,struct

EXPECTED_PYTHON_IMPLEMENTATION='b3b8134f4c9be5213dee91930e240792be509003a1b840848131e1f2621ee5ef'
FPA_KINDS=('FPA-MRT','FPA-ZF','FPA-OPT')
MA_CFG_KEYS=('maximum_AO_iterations','fractional_increase_threshold','convex_solver','interpretations','verification_tolerance','matlab_convex_solver','matlab_cvx_precision')

def need(value,message):
    if not value:raise ValueError(message)

def _token(value):
    if isinstance(value,bool):return ['bool',value]
    if isinstance(value,float):return ['float64',struct.pack('<d',value).hex()]
    if isinstance(value,int):return ['int',value]
    if isinstance(value,dict):return ['dict',[[k,_token(v)] for k,v in sorted(value.items())]]
    if isinstance(value,(tuple,list)):return ['list',[_token(v) for v in value]]
    if value is None or isinstance(value,str):return [type(value).__name__,value]
    raise TypeError(type(value).__name__)

def exact_digest(value):
    return hashlib.sha256(json.dumps(_token(value),separators=(',',':'),ensure_ascii=True,allow_nan=False).encode()).hexdigest()

def _f64_array_digest(value,expected_shape=None):
    """The source parses these saved JSON arrays as binary64; no sampling."""
    h=hashlib.sha256(b'binary64-array-C-order-v1\0')
    def visit(x):
        if isinstance(x,list):
            shapes=[visit(v) for v in x]
            need(not shapes or all(s==shapes[0] for s in shapes),'Ragged input array')
            return (len(x),)+(shapes[0] if shapes else ())
        need(type(x) in (int,float) and math.isfinite(float(x)),'Finite numeric source input')
        h.update(struct.pack('<d',float(x)));return ()
    shape=visit(value)
    if expected_shape is not None:need(shape==tuple(expected_shape),'Complete original saved array dimensions')
    return dict(shape=list(shape),dtype='float64',C_order_IEEE754_SHA256=h.hexdigest())

def projection(job,cfg,component):
    """Exact relevant physical/control readset; ignores D/figure/point labels only."""
    need(component in ('MA','FPA'),'Explicit component')
    n,m=job['N'],job['M'];need((n,m) in ((4,3),(6,5)),'Original Fig19/20 dimensions')
    need(cfg['nlos_realizations_per_geometry']==1000,'Full1000 original inputs required')
    need(not any(k in job for k in ('estimated_geometry','antenna_position_error','correlated')),'No unreviewed physical-error/correlated variant')
    nr,nc=cfg['antenna_factorization'][str(n)]
    need(nr*nc==n,'Original initial fixed-array factorization')
    initial=job.get('initial_positions',[[float((i-(nr-1)/2)/2),float((j-(nc-1)/2)/2)] for i in range(nr) for j in range(nc)])
    groups=dict(
        dimensions=[n,m],initial_fixed_lattice=_f64_array_digest(initial,(n,2)),
        geometry={k:_f64_array_digest(job['geometry'][k],(m,)) for k in ('distances_m','elevation','azimuth')},
        linear_Rician_binary64=struct.pack('<d',float(job['kappa'])).hex(),
        power_W_binary64=struct.pack('<d',float(job['power'])).hex(),
        nlos_re=_f64_array_digest(job['nlos_re'],(1000,n,m)),nlos_im=_f64_array_digest(job['nlos_im'],(1000,n,m)),
        source_physics_constants=dict(wavelength=1.,noise_W=[1e-11]*m,beta_reference=1e-4,pathloss_exponent=-2.8,
          directions='cos(elevation)*sin(azimuth), sin(elevation)',channel='LOS*sqrt(beta*k/(k+1)) + NLoS*sqrt(beta/(k+1))'),
        verification_tolerance=cfg['verification_tolerance'])
    if component=='FPA':
        groups['benchmark_solver']=copy.deepcopy(cfg['benchmark_solver'])
    else:
        A=float(job['A'])
        groups['region_lower']=_f64_array_digest(job.get('region_lower',[-nr*A/2,-nc*A/2]),(2,))
        groups['region_upper']=_f64_array_digest(job.get('region_upper',[nr*A/2,nc*A/2]),(2,))
        groups['MA_controls']={k:copy.deepcopy(cfg[k]) for k in MA_CFG_KEYS}
        groups['source_minimum_spacing']=.5
    return dict(schema='original-relevant-input-component-projection-v1',component=component,groups=groups,
                SHA256=exact_digest(groups))

def compare(donor_job,donor_cfg,target_job,target_cfg,component):
    a,b=projection(donor_job,donor_cfg,component),projection(target_job,target_cfg,component)
    differing=[k for k in a['groups'] if exact_digest(a['groups'][k])!=exact_digest(b['groups'][k])]
    return dict(component=component,equal=not differing,donor_projection_SHA256=a['SHA256'],target_projection_SHA256=b['SHA256'],differing_groups=differing)

def read_bound_json(identity):
    """Only an actually consumed selected file is read/hashed; never scan a bank."""
    p=Path(identity['path']);raw=p.read_bytes()
    expected=identity.get('SHA256',identity.get('sha256'))
    need(expected is not None and hashlib.sha256(raw).hexdigest()==expected,'Exact sealed selected file: '+str(p))
    if 'bytes' in identity:need(len(raw)==identity['bytes'],'Sealed selected byte length')
    return json.loads(raw)


def _bound_original(donor,target_job,target_cfg,component):
    # Read selected actual source/input/results once each; no bank scan.
    values={};original_bytes={}
    for key in ('job','config','python_raw'):
        identity=donor[key];b=Path(identity['path']).read_bytes()
        expected=identity.get('SHA256',identity.get('sha256'))
        need(expected is not None and hashlib.sha256(b).hexdigest()==expected,'Exact sealed consumed '+key)
        if 'bytes' in identity:need(len(b)==identity['bytes'],'Exact consumed byte length')
        values[key]=json.loads(b);original_bytes[key]=b
    job,cfg,result=values['job'],values['config'],values['python_raw']
    agreement=compare(job,cfg,target_job,target_cfg,component)
    need(agreement['equal'],'Different relevant source/input/control projection')
    need(result.get('status')!='failed','No absent/failed state may be invented')
    need(result['implementation_fingerprint']==EXPECTED_PYTHON_IMPLEMENTATION,'Original source/runtime identity mismatch')
    original_fp=hashlib.sha256(b'strict-v1\0'+original_bytes['config']+b'\0'+original_bytes['job']).hexdigest()
    need(original_fp==result['input_fingerprint']==donor['input_fingerprint'],'Keep original full-config identity; never relabel old tape as fresh whole case')
    receipt=dict(schema='actual-original-component-reuse-not-whole-case-adoption-v1',component=component,
        original_job=donor['job'],original_configuration=donor['config'],original_result=donor['python_raw'],
        original_input_fingerprint=original_fp,original_implementation_fingerprint=result['implementation_fingerprint'],
        relevant_projection=agreement,original_closed_population_evidence=donor.get('closed_population_metadata',donor.get('original_closed_receipt')),
        original_source_history_boundary=donor.get('source_history_boundary','Original closed MC case; source pins and failures retained.'),
        original_source_algorithm_and_parameter_epoch_retained=True,
        new_optimizer_MC_RNG_calls=0,old_whole_configuration_tape_not_adopted=True,
        saved_return_reuse_is_not_new_independent_physics_or_FPA_KKT_PASS=True)
    return result,receipt

def load_fpa_components(target_job,target_cfg,donor_record):
    """Return (all3_original_schemes, actual_bound_receipt); unknown fails.

    No history is reconstructed: complete exported original arrays/mean/cap
    fields are copied verbatim, including every nonconverged outcome.
    """
    result,receipt=_bound_original(donor_record,target_job,target_cfg,'FPA')
    schemes={}
    for kind in FPA_KINDS:
        row=result['metrics']['schemes'][kind];rates=row['sample_sum_rates']
        need(len(rates)==1000 and all(type(v) in (int,float) and math.isfinite(v) for v in rates),'Complete actual1000 finite saved rates')
        need(type(row['nonconverged_samples']) is int and 0<=row['nonconverged_samples']<=1000,'Actual original total nonconverged count')
        need(type(row['mean_sum_rate']) in (int,float) and math.isfinite(row['mean_sum_rate']),'Original finite saved mean')
        schemes[kind]=copy.deepcopy(row)
    receipt['all_original_fields_and_failed_counts_exactly_copied']=True
    receipt['original_per_call_FPA_history_or_W_QT_KKT_not_recovered']=True
    receipt['returned_scheme_numeric_digest']=exact_digest(schemes)
    return schemes,receipt

def load_ma_components(target_job,target_cfg,donor_record):
    """Exact JSON state/history components; no optimizer or MC evaluator."""
    result,receipt=_bound_original(donor_record,target_job,target_cfg,'MA')
    import numpy as np
    payload={}
    n=target_job['N']
    for mode in ('mrt','zf'):
        positions=np.asarray(result['metrics'][mode+'_positions'],dtype=float)
        realized=np.asarray(result['metrics'][mode+'_realized_positions'],dtype=float)
        history=copy.deepcopy(result['history'][mode])
        need(positions.shape==realized.shape==(n,2) and np.all(np.isfinite(positions)) and np.all(np.isfinite(realized)),'Actual original final positions')
        need(type(history['converged']) is bool,'Retain actual convergence including cap failure')
        need(np.asarray(history['positions'][-1],float).tobytes()==positions.tobytes(),'Original final/history identity')
        payload[mode]=dict(positions=positions,realized_positions=realized,history=history,
            actual_full1000_performance=copy.deepcopy(result['metrics']['schemes']['MA-'+mode.upper()]))
    receipt['all_saved_failed_stops_retained']=True
    receipt['original_historical_typed_object_identity_not_claimed']=True
    return payload,receipt
