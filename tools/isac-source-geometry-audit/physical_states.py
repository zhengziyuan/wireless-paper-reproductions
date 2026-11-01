"""Full NoRIS state fields from the unchanged independent physical reference."""
from copy import deepcopy
import hashlib
import math
from pathlib import Path
import sys
import mpmath as mp
from evidence import require, VARIANTS

REFERENCE_SHA256="d14050078d636ca33bd78fb2206406735a22589eeb0aa14b0f28c3d443d893bc"
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/isac-line-search-replay'))
import mp_physical_reference as ref
require(hashlib.sha256(Path(ref.__file__).read_bytes()).hexdigest()==REFERENCE_SHA256,
        'The original complete independent physical reference changed')


def serial(a,d):return dict(shape=[a.rows,a.cols],real=[[mp.nstr(mp.re(a[i,j]),d) for j in range(a.cols)] for i in range(a.rows)],
    imag=[[mp.nstr(mp.im(a[i,j]),d) for j in range(a.cols)] for i in range(a.rows)])

def norm2(a):return mp.fsum(abs(x)**2 for x in a)

def values(F,W,scene,fixed_iota):
    signal=F.conjugate().transpose()*W;k=len(scene['noise'])
    power=[[abs(signal[i,j])**2 for j in range(signal.cols)] for i in range(signal.rows)]
    sinr=[power[i][i]/(ref.exact(scene['noise'][i])+mp.fsum(x for j,x in enumerate(power[i]) if j!=i)) for i in range(k)]
    pattern=[mp.fsum(row) for row in power[k:]];desired=list(map(ref.exact,scene['desired_pattern']))
    e=mp.fsum(x*x for x in desired);c=mp.fsum(x*x for x in pattern);d=mp.fsum(x*y for x,y in zip(pattern,desired))
    rate=mp.fsum(mp.log1p(x) for x in sinr)/mp.log(2);iota=ref.exact(fixed_iota);assert iota>0 and e>0
    nmse=mp.fsum((x-iota*y)**2 for x,y in zip(pattern,desired))/(iota*iota*e)
    optimum=c/d if c>0 and d>0 else None
    best=mp.fsum((x-optimum*y)**2 for x,y in zip(pattern,desired))/(optimum*optimum*e) if optimum else None
    return signal,dict(rate=rate,sinr=sinr,pattern=pattern,actual_saved_fixed_iota=iota,fixed_iota_NMSE=nmse,
        fixed_iota_utility=rate-ref.exact(scene['rho'])*nmse,positive_optimal_iota=optimum,
        analytically_rescaled_NMSE=best,analytically_rescaled_utility=rate-ref.exact(scene['rho'])*best if best is not None else None)

def scalar_tree(value,d):
    if value is None:return None
    if isinstance(value,list):return [scalar_tree(x,d) for x in value]
    if isinstance(value,dict):return {k:scalar_tree(x,d) for k,x in value.items()}
    return mp.nstr(value,d)


def replay_lanes(saved,scene,scheme):
    """Freshly form every H/G/B/C/F/Q coordinate in both precision lanes."""
    m,n,k=len(scene['bs_coordinates']),len(scene['ris_coordinates']),len(scene['noise'])
    require(len(saved['w_re'])==len(saved['w_im'])==m and all(len(row)==k+m for row in saved['w_re']+saved['w_im']),
        'Every actual saved transmit-stream coordinate is required')
    require(len(saved['theta_re'])==len(saved['theta_im'])==n and len(saved['rotation'])==6,
        'Every actual saved RIS/rotation coordinate is required')
    require(all(math.isfinite(x) for row in saved['w_re']+saved['w_im'] for x in row) and
        all(math.isfinite(x) for key in ('theta_re','theta_im','rotation') for x in saved[key]),'A saved physical state is nonfinite')
    require(saved['rotation'][3:]==[0]*3,'The actual original NoRIS fixed RIS rotation must be preserved')
    lanes={}
    for digits in (80,100):
        with mp.workdps(digits):
            W=mp.matrix([[mp.mpc(ref.exact(a),ref.exact(b)) for a,b in zip(re,im)] for re,im in zip(saved['w_re'],saved['w_im'])])
            theta=[mp.mpc(ref.exact(a),ref.exact(b)) for a,b in zip(saved['theta_re'],saved['theta_im'])]
            require(norm2(W)<=ref.exact(scene['power'])+ref.exact(scene['verification_tolerance']), 'Actual original saved power constraint failed')
            require(max(abs(abs(x)-1) for x in theta)<=mp.mpf('1e-12'),'Actual original saved RIS unit modulus failed')
            width=scene.get('rotation_bs_half_width',scene.get('rotation_half_width',math.pi/2)) if scheme.startswith('Rot-BS') else 0
            require(all(abs(ref.exact(x))<=ref.exact(width)+mp.mpf('1e-12') for x in saved['rotation'][:3]),'Original NoRIS BS angle box failed')
            lane={};internal={}
            for variant in VARIANTS:
                own=deepcopy(scene)
                if variant.startswith('supplied'):
                    own['br_gain_re']=[0.]*len(own['br_gain_re']);own['br_gain_im']=[0.]*len(own['br_gain_im'])
                else:
                    for field in ('ru_gain_re','ru_gain_im'):own[field]=[[0. for _ in row] for row in own[field]]
                H,G,B=ref.field_parts(saved['rotation'],own);C=B*mp.diag(theta)*G;F=H+C
                Q,metrics=values(F,W,own,saved['iota'])
                require(all(C[i,j]==0 for i in range(C.rows) for j in range(k)),'A NoRIS variant retained a user cascade')
                if variant.startswith('supplied'):require(all(x==0 for x in B) and all(x==0 for x in C),'R1 all-assisted removal retained a cascade')
                else:require(all(G[i,j]==0 for i in range(G.rows) for j in range(k)),'The literal RU-only source variant retained a user outgoing channel')
                matrices=dict(direct=H,RIS_outgoing=G,BS_RIS_bridge=B,cascade=C,effective=F,received_signal=Q)
                lane[variant]=dict(full_fields={key:serial(a,digits) for key,a in matrices.items()},metrics=scalar_tree(metrics,digits),
                    full_cascade_squared_norm=mp.nstr(norm2(C),digits),actual_transmit_power=mp.nstr(norm2(W),digits))
                internal[variant]=dict(signal=Q,metrics=metrics)
            a,b=internal.values()
            require(a['metrics']['sinr']==b['metrics']['sinr'] and a['metrics']['rate']==b['metrics']['rate'],
                'The source variants changed an actual user SINR/rate')
            require(all(a['signal'][i,j]==b['signal'][i,j] for i in range(k) for j in range(a['signal'].cols)),
                'One original complete user received-signal coordinate changed between variants')
            original=a['metrics'];tolerance=ref.exact(scene['verification_tolerance'])
            require(abs(original['rate']-ref.exact(saved['rate']))<=tolerance and
                abs(original['fixed_iota_NMSE']-ref.exact(saved['nmse']))<=tolerance and
                abs(original['fixed_iota_utility']-ref.exact(saved['utility']))<=tolerance,
                'The unchanged R1 full state no longer replays its saved original physical metrics')
            lanes[str(digits)]=lane
    return lanes


def matrix_rows(a):
    require(isinstance(a,dict) and set(a)=={'shape','real','imag'},'A complete physical matrix representation is required')
    require(len(a['shape'])==2 and all(isinstance(x,int) and x>0 for x in a['shape']),'A full physical matrix axis is absent')
    rows,columns=a['shape']
    require(len(a['real'])==len(a['imag'])==rows and all(len(row)==columns for row in a['real']+a['imag']),
        'An original full real/imag matrix coordinate is missing')
    return rows,columns


def compare_tree(a,b,bound):
    if a is None or b is None:
        require(a is None and b is None,'An unavailable analytic scaling value changed');return 0
    if isinstance(a,dict) or isinstance(b,dict):
        require(isinstance(a,dict) and isinstance(b,dict) and set(a)==set(b),'A complete metric field is absent')
        return sum(compare_tree(a[k],b[k],bound) for k in a)
    if isinstance(a,list) or isinstance(b,list):
        require(isinstance(a,list) and isinstance(b,list) and len(a)==len(b),'A complete metric ordinate is absent')
        return sum(compare_tree(x,y,bound) for x,y in zip(a,b))
    x,y=mp.mpf(a),mp.mpf(b)
    require(mp.isfinite(x) and mp.isfinite(y) and abs(x-y)<=bound,'A complete physical scalar/metric ordinate differs')
    return 1


def compare_lanes(fresh,sealed):
    require(set(fresh)==set(sealed)=={'80','100'},'Both complete original precision lanes are required')
    coordinates={};scalar_counts={};largest=mp.mpf(0)
    with mp.workdps(140):
        bound=mp.mpf('1e-40')
        for digits in ('80','100'):
            require(set(fresh[digits])==set(sealed[digits])==set(VARIANTS),'Both complete source model variants are required')
            coordinates[digits]=0;scalar_counts[digits]=0
            for variant in VARIANTS:
                a,b=fresh[digits][variant],sealed[digits][variant]
                fields=a['full_fields'];prior=b['full_fields']
                require(set(fields)==set(prior)=={'direct','RIS_outgoing','BS_RIS_bridge','cascade','effective','received_signal'},
                    'A full independent physical field matrix is missing')
                for name in fields:
                    x,y=fields[name],prior[name];require(matrix_rows(x)==matrix_rows(y),'A complete field shape changed')
                    for component in ('real','imag'):
                        for row,old in zip(x[component],y[component]):
                            for left,right in zip(row,old):
                                left,right=mp.mpf(left),mp.mpf(right)
                                require(mp.isfinite(left) and mp.isfinite(right),'An actual full field coordinate is nonfinite')
                                gap=abs(left-right);largest=max(largest,gap);coordinates[digits]+=1
                                require(gap<=bound,'An actual full physical matrix coordinate differs from the sealed reference')
                for name in ('metrics','full_cascade_squared_norm','actual_transmit_power'):
                    scalar_counts[digits]+=compare_tree(a[name],b[name],bound)
        for variant in VARIANTS:
            for name in fresh['80'][variant]['full_fields']:
                x,y=fresh['80'][variant]['full_fields'][name],fresh['100'][variant]['full_fields'][name]
                require(matrix_rows(x)==matrix_rows(y),'A full MP80/MP100 field dimension differs')
                for component in ('real','imag'):
                    for row,old in zip(x[component],y[component]):
                        for left,right in zip(row,old):
                            require(abs(mp.mpf(left)-mp.mpf(right))<=bound,'A complete fresh MP80/MP100 field coordinate differs')
            for name in ('metrics','full_cascade_squared_norm','actual_transmit_power'):
                compare_tree(fresh['80'][variant][name],fresh['100'][variant][name],bound)
    return dict(full_field_coordinates_per_precision=coordinates,physical_scalar_values_per_precision=scalar_counts,
        maximum_full_field_difference_from_sealed_reference=mp.nstr(largest,140),precision_bound='1e-40')
