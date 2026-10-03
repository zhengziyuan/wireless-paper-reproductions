"""Independent angular/radial Decimal60 full Fig7 physical checker, NOT a solver.

Unlike the live verifier's Euclidean complex-gradient projection, this uses
radial and angular directional derivatives and the projection-norm identity.
X uses uncentered Euclidean derivatives; simplex shift invariance is exact.
"""
from decimal import Decimal, localcontext
import os
for key in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS'):os.environ[key]='1'
import numpy as np

def D(x):return Decimal.from_float(float(x))
def add(a,b):return a[0]+b[0],a[1]+b[1]
def mul(a,b):return a[0]*b[0]-a[1]*b[1],a[0]*b[1]+a[1]*b[0]
def conjugate(a):return a[0],-a[1]
def abs2(a):return a[0]**2+a[1]**2
def pairs(state):return [(D(r),D(i)) for r,i in zip(state['real'],state['imag'])]


def geometry(settings,baseline):
    if baseline not in ('MIS','SMS'):raise ValueError('Unknown baseline')
    config={'ms1':[1,2],'ms2':[1,1] if baseline=='MIS' else [0,0],
        'azimuth_deg':[-60.,-20.,20.,60.],'elevation_deg':[45.]*4,
        'spacing_over_wavelength':settings['spacing_over_wavelength'],
        'incidence_direction_cosines':settings['incidence_direction_cosines'],
        'number_of_targets':4,'reference_snr':settings['reference_snr']}
    # Independent direct geometry construction; no numerical-engine import.
    az=np.deg2rad(np.array(config['azimuth_deg']));el=np.deg2rad(np.array(config['elevation_deg']))
    directions=np.column_stack((np.sin(el)*np.cos(az),np.sin(el)*np.sin(az)))
    coordinates=np.array([[0,0],[0,1]])
    c=np.exp(2j*np.pi*config['spacing_over_wavelength']*(directions@coordinates.T))
    c*=np.exp(2j*np.pi*config['spacing_over_wavelength']*(coordinates@np.array(config['incidence_direction_cosines'])))[None,:]
    indices=[[u] for u in range(2)] if baseline=='MIS' else [[]]
    return config,{'real':c.real.tolist(),'imag':c.imag.tolist()},indices


def initial_input(settings,baseline,start):
    n=1 if baseline=='MIS' else 0;u=2 if baseline=='MIS' else 1
    seed=settings['initialization']['seed']+(0 if baseline=='MIS' else 500000)
    draws=4*u+2+n;before=int(seed)*pow(16807,(start-1)*draws,2147483647)%2147483647
    state=before;values=[]
    for _ in range(draws):state=16807*state%2147483647;values.append(state/2147483647)
    X=np.asarray(values[:4*u],float).reshape(4,u);X/=np.sum(X,axis=1,keepdims=True)
    p=np.exp(2j*np.pi*np.asarray(values[4*u:4*u+2]));t=np.exp(2j*np.pi*np.asarray(values[4*u+2:]))
    return before,state,{'phi':{'real':p.real.tolist(),'imag':p.imag.tolist()},
        'theta':{'real':t.real.tolist(),'imag':t.imag.tolist()},'X':X.tolist()}


def prescribed_mu(settings,start):
    mu=settings['initial_mu_values'][(start-1)%len(settings['initial_mu_values'])];values=[]
    while mu>=settings['terminal_mu']:values.append(mu);mu*=.5
    return values


def project_simplex(row):
    sorted_row=sorted(row,reverse=True);total=Decimal(0);threshold=None
    for k,y in enumerate(sorted_row,1):
        total+=y;candidate=(total-1)/k
        if y>candidate:threshold=candidate
    if threshold is None:raise ArithmeticError('Finite simplex threshold absent')
    return [max(Decimal(0),y-threshold) for y in row]


def physical(config,c,indices,state,mu):
    with localcontext() as context:
        context.prec=60;zero=Decimal(0)
        p=pairs(state['phi']);t=pairs(state['theta']);X=[[D(x) for x in row] for row in state['X']]
        C=[[(D(r),D(i)) for r,i in zip(rr,ii)] for rr,ii in zip(c['real'],c['imag'])]
        M=len(p);N=len(t);K=len(C);U=len(indices);iota=D(config['reference_snr'])
        if M!=2 or K!=4 or N not in (0,1) or U!=(2 if N else 1):raise ValueError('Original full Fig7 dimensions required')
        if len(X)!=K or any(len(row)!=U for row in X):raise ValueError('Physical X dimension mismatch')
        bars=[[(Decimal(1),zero) for _ in range(M)] for _ in range(U)]
        for u in range(U):
            for n,m in enumerate(indices[u]):bars[u][m]=t[n]
        fields=[[(zero,zero) for _ in range(U)] for _ in range(K)]
        powers=[[zero for _ in range(U)] for _ in range(K)]
        terms=[[[None]*M for _ in range(U)] for _ in range(K)]
        for k in range(K):
            for u in range(U):
                q=(zero,zero)
                for m in range(M):
                    term=mul(C[k][m],mul(p[m],bars[u][m]));terms[k][u][m]=term;q=add(q,term)
                fields[k][u]=q;powers[k][u]=iota*abs2(q)
        users=[sum((X[k][u]*powers[k][u] for u in range(U)),zero) for k in range(K)]
        minimum=min(users);m_mu=D(mu);ex=[(-(v-minimum)/m_mu).exp() for v in users]
        total=sum(ex,zero);weights=[v/total for v in ex]
        radial_p=[zero]*M;angular_p=[zero]*M;radial_t=[zero]*N;angular_t=[zero]*N
        for k in range(K):
            for u in range(U):
                factor=2*iota*weights[k]*X[k][u]
                for m in range(M):
                    v=mul(conjugate(fields[k][u]),terms[k][u][m])
                    radial_p[m]-=factor*v[0];angular_p[m]+=factor*v[1]
                for n,m in enumerate(indices[u]):
                    v=mul(conjugate(fields[k][u]),terms[k][u][m])
                    radial_t[n]-=factor*v[0];angular_t[n]+=factor*v[1]
        def projection_square(phases,radial,angular):
            result=zero
            for z,r,a in zip(phases,radial,angular):
                radius_squared=abs2(z)
                # Exact stored-complex norm of g-Re(g*conj(z))*z.
                result+=(a*a+r*r*(1-radius_squared)**2)/radius_squared
            return result
        phi_square=projection_square(p,radial_p,angular_p);theta_square=projection_square(t,radial_t,angular_t)
        simplex_square=zero;rowmean_square=zero
        for k in range(K):
            raw=[-weights[k]*value for value in powers[k]];mean=sum(raw,zero)/U
            rowmean_square+=sum(((v-mean)**2 for v in raw),zero)
            projected=project_simplex([X[k][u]-raw[u] for u in range(U)])
            simplex_square+=sum(((x-y)**2 for x,y in zip(X[k],projected)),zero)
        norm=(phi_square+theta_square+simplex_square).sqrt()
        rowmean_norm=(phi_square+theta_square+rowmean_square).sqrt()
        binary=[];snr=[]
        for k in range(K):
            selected=max(range(U),key=lambda u:X[k][u]);binary.append([int(u==selected) for u in range(U)]);snr.append(powers[k][selected])
        phase_error=max([abs(abs2(z).sqrt()-1) for z in p+t] or [zero]);row_error=max(abs(sum(row,zero)-1) for row in X)
        domain=phase_error<D(1e-12) and row_error<D(1e-12) and min(x for row in X for x in row)>=0
        return {'method':'independent Decimal60 angular/radial projected-norm identity and uncentered simplex oracle',
            'projected_kkt_norm':float(norm),'projected_kkt_norm_decimal':str(norm),'printed_rowmean_norm':float(rowmean_norm),
            'phi_norm':float(phi_square.sqrt()),'theta_norm':float(theta_square.sqrt()),'X_norm':float(simplex_square.sqrt()),
            'objective':float(-minimum+m_mu*total.ln()),'min_binary_snr':float(min(snr)),
            'min_relaxed_snr':float(minimum),'binary_schedule':binary,'domain_feasible':bool(domain),
            'maximum_radius_error':float(phase_error),'maximum_simplex_sum_error':float(row_error),
            'unchanged_implemented_1e_minus6_gate_pass':bool(norm<=D(1e-6)),
            'printed_open_simplex_gradient_criterion_claimed':False}
