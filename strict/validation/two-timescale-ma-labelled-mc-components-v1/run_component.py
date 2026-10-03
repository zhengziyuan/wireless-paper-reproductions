"""Portable exact source-D3 component; no smaller production grid/MC option."""
from pathlib import Path
import argparse,hashlib,json,math,os,time
from fractions import Fraction
from itertools import permutations

for name in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS'):
    os.environ[name]='1'
import numpy as np
from mc_labelled_zf_exact_bound_v1 import ExactLabelledMCZF,LN2_LO,LN2_HI

HERE=Path(__file__).resolve().parent
PREFLIGHT_INDICES=(0,1,17,63,127,511,1023,1535,2047,2559,3022,3023)


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def write_fresh(path,data):
    if path.exists():raise FileExistsError(path)
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(data,indent=2,allow_nan=False)+'\n',encoding='utf-8')


def outward_quotient(num,den,lower):
    rational=Fraction(num,den);value=float(rational)
    assert math.isfinite(value)
    stored=Fraction.from_float(value)
    if lower and stored>rational:value=math.nextafter(value,-math.inf)
    if not lower and stored<rational:value=math.nextafter(value,math.inf)
    assert (Fraction.from_float(value)<=rational) if lower else (Fraction.from_float(value)>=rational)
    return value


def packet():
    manifest=json.loads((HERE/'freeze-manifest.json').read_bytes())
    for name,expected in manifest['files'].items():assert sha(HERE/name)==expected,name
    input_data=json.loads((HERE/'input-table.json').read_bytes())
    assert input_data['shape']==[1000,4,9,3] and input_data['dtype']=='<c16' and input_data['order']=='C'
    raw=(HERE/'channel-table.bin').read_bytes()
    assert hashlib.sha256(raw).hexdigest()==input_data['original_channel_table_sha256']
    h=np.frombuffer(raw,dtype='<c16').reshape(input_data['shape'])
    leaves=json.loads((HERE/'leaf-intervals.json').read_bytes())
    intervals={tuple(row['labelled_layout']):(int(row['exact_natural_total_Q80_lower']),int(row['exact_natural_total_Q80_upper']))
               for row in leaves['all3024_leaf_records']}
    assert len(intervals)==3024 and set(intervals)==set(permutations(range(9),4))
    grid=np.array(input_data['grid'],float)
    distance=np.linalg.norm(grid[:,None]-grid[None,:],axis=2)+np.eye(9)*1e9
    assert distance.min()>=.5
    bounds=json.loads((HERE/'bound-and-prunes.json').read_bytes())
    winner=tuple(bounds['winner_labelled_layout']);incumbent=intervals[winner][0]
    assert all(high<incumbent for layout,(_,high) in intervals.items() if layout!=winner)
    const=int(bounds['bound']['bound_natural_log_constant_Q80'])
    coefficient=[[int(x) for x in row] for row in bounds['bound']['bound_label_candidate_coefficients_Q80']]
    def upper(prefix):
        remaining=[p for p in range(9) if p not in prefix]
        return const+sum(coefficient[n][p] for n,p in enumerate(prefix))+sum(
            max(coefficient[n][p] for p in remaining) for n in range(len(prefix),4))
    checked=0
    def visit(prefix):
        nonlocal checked
        candidates=[interval for layout,interval in intervals.items() if layout[:len(prefix)]==prefix]
        assert upper(prefix)>=max(high for _,high in candidates)
        checked+=1
        if len(prefix)<4:
            for p in range(9):
                if p not in prefix:visit((*prefix,p))
    visit(());assert checked==3610
    covered=[]
    for certificate in bounds['certificates']:
        prefix=tuple(certificate['prefix']);descendants=[layout for layout in intervals if layout[:len(prefix)]==prefix]
        ub=upper(prefix)
        assert ub==int(certificate['upper_Q80']) and incumbent==int(certificate['incumbent_lower_Q80'])
        assert ub<=incumbent and max(intervals[layout][1] for layout in descendants)<incumbent
        covered.extend(descendants)
    visited=[layout for layout in intervals if layout not in set(covered)]
    assert len(covered)==len(set(covered)) and len(covered)+len(visited)==3024 and len(bounds['certificates'])==301
    assert len(visited)==2693
    return input_data,h,grid,intervals,winner,manifest


def qr_rate(h,power,noise):
    q,r=np.linalg.qr(h,mode='reduced')
    v=q@np.linalg.solve(r.conj().transpose(0,2,1),np.broadcast_to(np.eye(3),(len(h),3,3)))
    w=v/np.linalg.norm(v,axis=1)[:,None,:]*np.sqrt(power/3)
    gain=abs(h.conj().transpose(0,2,1)@w)**2;signal=np.diagonal(gain,axis1=1,axis2=2)
    return float(np.log2(1+signal/(gain.sum(axis=2)-signal+noise)).sum(axis=1).mean())


def main():
    parser=argparse.ArgumentParser();mode=parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--verify-frozen',action='store_true');mode.add_argument('--preflight',action='store_true');mode.add_argument('--execute',action='store_true')
    parser.add_argument('--output',type=Path);args=parser.parse_args()
    if not args.verify_frozen and args.output is None:parser.error('A fresh --output is required')
    if args.output is not None and args.output.exists():raise FileExistsError(args.output)
    start=time.perf_counter();data,h,grid,intervals,winner,manifest=packet()
    base={'scope':'portable exact fixed geometry0 full source-D3 component, not entire original figure',
        'packet_manifest_sha256':sha(HERE/'freeze-manifest.json'),'original_binary_input_table_sha256':data['original_channel_table_sha256'],
        'all_packet_hashes_and3610_upper_interval_and301prune_checks_passed':True,
        'original_N4_M3_and_all1000_per_layout':True,'full_D3_to18_all100geometry_or_MATLAB_parity_claimed':False}
    if args.verify_frozen:
        report=dict(base,mode='verify-frozen',fresh_physical_full3024_rerun=False,elapsed_seconds=time.perf_counter()-start)
    else:
        model=ExactLabelledMCZF(grid,h,float.fromhex(data['power_hex']),float.fromhex(data['noise_hex']))
        layouts=list(model.completions());assert len(layouts)==3024
        selected=[layouts[i] for i in PREFLIGHT_INDICES] if args.preflight else layouts
        rows=[];maximum_physical_error=0.
        for count,layout in enumerate(selected,1):
            interval=model.leaf_interval(layout)
            assert interval==intervals[layout],f'Exact interval differs for labelled layout{layout}'
            low=outward_quotient(interval[0],1000*LN2_HI,True)
            high=outward_quotient(interval[1],1000*LN2_LO,False)
            physical=qr_rate(np.array([h[:,n,layout[n]] for n in range(4)]).transpose(1,0,2),
                             float.fromhex(data['power_hex']),float.fromhex(data['noise_hex']))
            error=max(low-physical,physical-high,0.);maximum_physical_error=max(maximum_physical_error,error)
            assert error<1e-9
            rows.append({'labelled_layout':list(layout),'exact_Q80_natural_lower':str(interval[0]),'exact_Q80_natural_upper':str(interval[1]),
                'outward_display_lower':low,'outward_display_upper':high,'independent_QR_mean':physical})
            if count%64==0:print(json.dumps({'actual_full1000_layouts_completed':count,'expected':len(selected)}),flush=True)
        report=dict(base,mode='preflight' if args.preflight else 'execute',fixed_preflight_indices=list(PREFLIGHT_INDICES) if args.preflight else None,
            actual_complete_layouts=len(selected),all12_preflight_not_full_rerun=bool(args.preflight),
            fresh_every3024_full1000_complete=not args.preflight,all_actual_exact_intervals_match_retained_full_evidence=True,
            maximum_independent_QR_reporting_error=maximum_physical_error,unchanged_QR_reporting_gate=1e-9,
            winner_labelled_layout=list(winner),winner_exact_lower_rational={'num':str(intervals[winner][0]),'den':str(1000*LN2_HI)},
            winner_exact_upper_rational={'num':str(intervals[winner][1]),'den':str(1000*LN2_LO)},
            actual_layout_records=rows,elapsed_seconds=time.perf_counter()-start)
    if args.output is not None:write_fresh(args.output,report)
    print(json.dumps({k:v for k,v in report.items() if k!='actual_layout_records'}),flush=True)


if __name__=='__main__':main()
