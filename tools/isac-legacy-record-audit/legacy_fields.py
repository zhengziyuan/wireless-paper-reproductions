"""Unchanged independent kernels for the actual preserved historical initial state.

Historical negative-cosine communication gains and unweighted target steering
remain explicit. These kernels do not execute an archived optimizer or sampler.
"""
from pathlib import Path
from fractions import Fraction
import hashlib
import sys
import numpy as np
import mpmath as mp

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/isac-line-search-replay'))
import mp_physical_reference as ref
if hashlib.sha256(Path(ref.__file__).read_bytes()).hexdigest()!='d14050078d636ca33bd78fb2206406735a22589eeb0aa14b0f28c3d443d893bc':
    raise RuntimeError('The original independent arbitrary-precision frame reference changed')

def require(value, message):
    if not value:
        raise AssertionError(message)

def scalar(data, name):
    return float(data[name][0,0])

def matrix(array):
    return mp.matrix([[mp.mpc(float(v.real),float(v.imag)) for v in row] for row in np.asarray(array)])

def serial(value, digits):
    return dict(shape=[value.rows,value.cols],
        real=[[mp.nstr(mp.re(value[i,j]),digits) for j in range(value.cols)] for i in range(value.rows)],
        imag=[[mp.nstr(mp.im(value[i,j]),digits) for j in range(value.cols)] for i in range(value.rows)])

def all_hex_equal(original, sealed):
    require(original == sealed, 'A complete actual saved MAT numeric variable/coordinate differs')

def fields(data, digits):
    with mp.workdps(digits):
        k,m,n = [int(scalar(data,key)) for key in ('K','M','N')]
        count = int(scalar(data,'NA'))
        qB = ref.frame(data['rB'].ravel()); qR = ref.frame(data['rR'].ravel())
        localB,localR = matrix(data['coordsB']),matrix(data['coordsR'])
        centerB,centerR = matrix(data['d0_B']),matrix(data['d0_R'])
        dB = localB*qB.transpose()+centerB; dR = localR*qR.transpose()+centerR
        wave = 2*mp.pi/ref.exact(scalar(data,'lambda'))
        def response(direction, positions, q, gain0, exponent, communication):
            u = [ref.exact(v) if isinstance(v,mp.mpf) else ref.exact(float(v)) for v in direction]
            cosine = -mp.fsum(q[d,2]*u[d] for d in range(3))
            amplitude = mp.sqrt(ref.exact(gain0))*cosine**(ref.exact(exponent)/2) if cosine>0 else mp.mpf(0)
            if not communication:
                amplitude = mp.mpf(1)
            return [amplitude*mp.exp(1j*wave*mp.fsum(positions[i,d]*u[d] for d in range(3)))
                    for i in range(positions.rows)]
        argsB = (dB,qB,scalar(data,'G0B'),scalar(data,'pB'))
        argsR = (dR,qR,scalar(data,'G0R'),scalar(data,'pR'))
        H,G,B = mp.matrix(m,k+count),mp.matrix(n,k+count),mp.matrix(m,n)
        for user in range(k):
            for array_name,gain_name,target,args in (('u_BU','a_BU',H,argsB),('u_RU','c_RU',G,argsR)):
                directions=data[array_name][user,0]; gains=data[gain_name][user,0].ravel()
                for ray in range(directions.shape[1]):
                    a=response(directions[:,ray],*args,True)
                    gain=ref.exact(complex(gains[ray]))
                    for i,value in enumerate(a):
                        target[i,user] += gain*value
        for ray,gain in enumerate(data['bBR'].ravel()):
            a=response(data['uBR'][:,ray],*argsB,True)
            b=response(data['uRB'][:,ray],*argsR,True)
            for i in range(m):
                for j in range(n):
                    B[i,j] += ref.exact(complex(gain))*a[i]*mp.conj(b[j])
        # Original full per-cell direction intermediates were not saved.
        # Independently evaluate their recipe in MP from the exact saved grid
        # angles; compare every resulting saved field at the disclosed bound.
        AZ,EL = data['AZ'].ravel(order='F'),data['EL'].ravel(order='F')
        directions=[]
        for az,el in zip(AZ,EL):
            az,el=ref.exact(float(az)),ref.exact(float(el))
            directions.append([mp.cos(el)*mp.cos(az),mp.cos(el)*mp.sin(az),mp.sin(el)])
        for target,u in enumerate(directions):
            for matrix_out,args in ((H,argsB),(G,argsR)):
                for i,value in enumerate(response(u,*args,False)):
                    matrix_out[i,k+target]=value
        W=matrix(data['W']); theta=[ref.exact(complex(v)) for v in data['theta'].ravel()]
        C=B*mp.diag(theta)*G; F=H+C; Q=F.conjugate().transpose()*W
        powers=[[abs(Q[i,j])**2 for j in range(Q.cols)] for i in range(Q.rows)]
        sinr=[powers[i][i]/(ref.exact(float(data['sigma2'][i,0]))+
              mp.fsum(x for j,x in enumerate(powers[i]) if j!=i)) for i in range(k)]
        pattern=[mp.fsum(row) for row in powers[k:]]
        desired=[ref.exact(float(v)) for v in data['Pd'].ravel()]
        raw_mse=mp.fsum((p-d)**2 for p,d in zip(pattern,desired))/count
        parts=dict(direct=H,RIS_outgoing=G,BS_RIS_bridge=B,cascade=C,effective=F,
                   received_signal=Q,transmit_covariance=W*W.conjugate().transpose(),
                   BS_positions=dB,RIS_positions=dR,BS_frame=qB,RIS_frame=qR)
        metrics=dict(Pgrid=pattern,SINR=sinr,raw_MSE=[raw_mse])
        return parts,metrics

def compare_actual_saved(data,parts,metrics):
    k=int(scalar(data,'K'))
    saved_H=np.column_stack([data['h_all'][i,0].ravel() for i in range(k)])
    saved_G=np.column_stack([data['g_all'][i,0].ravel() for i in range(k)])
    pairs=[('all_original_user_h',parts['direct'][:,:k],saved_H),
           ('all_original_user_g',parts['RIS_outgoing'][:,:k],saved_G),
           ('all_original_BB',parts['BS_RIS_bridge'],data['BB']),
           ('all_original_transmit_covariance',parts['transmit_covariance'],data['Ccov']),
           ('all_original_BS_positions',parts['BS_positions'],data['dB']),
           ('all_original_RIS_positions',parts['RIS_positions'],data['dR']),
           ('all_original_BS_frame',parts['BS_frame'],data['RB']),
           ('all_original_RIS_frame',parts['RIS_frame'],data['RR']),
           ('actual_last_saved_user_field',parts['effective'][:,k-1],data['fk']),
           ('actual_last_saved_target_field',parts['effective'][:,parts['effective'].cols-1],data['fS'])]
    rows=[]; largest=mp.mpf(0); coordinates=0
    for name,fresh,saved in pairs:
        require((fresh.rows,fresh.cols)==saved.shape, 'A complete saved physical matrix shape differs: '+name)
        gap=mp.mpf(0)
        for i in range(fresh.rows):
            for j in range(fresh.cols):
                for a,b in ((mp.re(fresh[i,j]),float(saved[i,j].real)),(mp.im(fresh[i,j]),float(saved[i,j].imag))):
                    delta=abs(a-ref.exact(b)); gap=max(gap,delta); coordinates+=1
                    require(delta<=mp.mpf('1e-12')*(1+abs(ref.exact(b))), 'An actual saved field ordinate differs: '+name)
        largest=max(largest,gap); rows.append(dict(field=name,real_imag_coordinates=2*fresh.rows*fresh.cols,maximum_gap=mp.nstr(gap,30)))
    scalar_count=0
    for name,raw in (('Pgrid',data['Pgrid'].ravel()),('SINR',data['SINR'].ravel()),('raw_MSE',[scalar(data,'MSE')])):
        fresh=metrics[name]; require(len(fresh)==len(raw), 'A complete physical metric array is missing')
        gap=mp.mpf(0)
        for a,b in zip(fresh,raw):
            delta=abs(a-ref.exact(float(b))); gap=max(gap,delta); scalar_count+=1
            require(delta<=mp.mpf('1e-12')*(1+abs(ref.exact(float(b)))), 'An actual saved scalar differs: '+name)
        largest=max(largest,gap); rows.append(dict(field=name,all_scalar_values=len(fresh),maximum_gap=mp.nstr(gap,30)))
    return dict(saved_physical_real_imag_coordinates=coordinates,actual_saved_metric_values=scalar_count,
                maximum_actual_binary64_saved_gap=mp.nstr(largest,40),all_complete_fields_pass=True,fields=rows)

def dot(a,b): return sum(x*y for x,y in zip(a,b))

def geometry_pair(a,b):
    a,b=[[Fraction.from_float(float(x)) for x in v] for v in (a,b)]
    aa,bb,ab=dot(a,a),dot(b,b),dot(a,b); determinant=aa*bb-ab*ab
    require(determinant>0, 'The saved first-ray closest-line system is singular')
    t=(bb*10*a[0]-ab*10*b[0])/determinant
    s=(ab*10*a[0]-aa*10*b[0])/determinant
    residual=[t*x-s*y-d for x,y,d in zip(a,b,(10,0,0))]
    require(dot(residual,a)==dot(residual,b)==0, 'Exact saved closest-line normal equations failed')
    distance=dot(residual,residual); triple=10*(a[1]*b[2]-a[2]*b[1])
    require(distance==triple*triple/determinant and distance>0, 'The exact Gram/cross-product geometry differs')
    frac=lambda value:dict(numerator=value.numerator,denominator=value.denominator)
    with mp.workdps(100):
        separation=mp.sqrt(mp.mpf(distance.numerator)/distance.denominator)
    return dict(exact_squared_minimum_supporting_line_separation_m2=frac(distance),
        exact_Gram_determinant=frac(determinant),MP100_line_separation_m=mp.nstr(separation,100),
        exact_common_point_LoS_condition_fails=True)
